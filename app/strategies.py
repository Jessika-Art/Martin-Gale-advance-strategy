"""Strategy implementations for Multi-Martingales Trading Bot"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
import time
from datetime import datetime

from config import StrategySettings, StrategyType

class OrderAction(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None

@dataclass
class OrderRequest:
    """Order request structure"""
    symbol: str
    action: OrderAction
    quantity: float
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    strategy_id: str = ""
    leg_number: int = 0

@dataclass
class Position:
    """Position tracking"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float = 0.0
    strategy_id: str = ""
    leg_number: int = 0
    entry_time: datetime = None
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_price) * self.quantity
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_price == 0:
            return 0.0
        return ((self.current_price - self.avg_price) / self.avg_price) * 100

class BaseStrategy(ABC):
    """Base class for all martingale strategies"""
    
    def __init__(self, settings: StrategySettings, strategy_type: StrategyType):
        self.settings = settings
        self.strategy_type = strategy_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{settings.symbol}")
        
        # Strategy state
        self.positions: List[Position] = []
        self.pending_orders: List[OrderRequest] = []
        self.completed_orders: List[OrderRequest] = []
        self.current_leg = 0
        self.entry_price: Optional[float] = None
        self.is_active = False
        self.cycle_start_time: Optional[datetime] = None
        self.position_direction = 'long'  # Default to long positions for most strategies
        
        # Zone and boundary tracking for ZRM/IZRM strategies
        self.last_boundary_touched: Optional[str] = None  # 'upper' or 'lower'
        self.zone_upper_boundary: Optional[float] = None
        self.zone_lower_boundary: Optional[float] = None
        self.net_position: float = 0.0  # Net position across all legs
        self.last_order_action: Optional[OrderAction] = None  # Track last order type for alternating
        
        # Strategy coordination state
        self.other_strategies: Dict[StrategyType, 'BaseStrategy'] = {}
        self.coordination_enabled = settings.other_strategies_entry_index
        self.alignment_mode = settings.strategy_alignment
        self.parallel_start_mode = settings.parallel_start_mode
        self.strategy_to_start_with = settings.strategy_to_start_with
        self.order_number_to_start = settings.order_number_to_start
        self.sequential_mode_strategy = settings.sequential_mode_strategy
        self.waiting_for_other_strategy = False
        self.first_edge_touched = False
        
        # Trailing stop tracking
        self.trailing_stops_active: Dict[int, bool] = {}  # leg_number -> is_active
        self.trailing_stop_prices: Dict[int, float] = {}  # leg_number -> stop_price
        self.highest_profit_prices: Dict[int, float] = {}  # leg_number -> highest_price
        
        # Performance tracking
        self.total_cycles = 0
        self.winning_cycles = 0
        self.total_profit = 0.0
        self.peak_equity = 0.0
        
    @abstractmethod
    def should_enter(self, market_data: MarketData) -> bool:
        """Determine if strategy should enter initial position"""
        pass
    
    @abstractmethod
    def should_add_leg(self, market_data: MarketData) -> bool:
        """Determine if strategy should add another leg"""
        pass
    
    @abstractmethod
    def should_exit(self, market_data: MarketData) -> bool:
        """Determine if strategy should exit all positions"""
        pass
    
    def update_trailing_stops(self, market_data: MarketData, current_profit_pct: float, leg_number: int) -> bool:
        """Update trailing stop logic and return True if stop should be triggered"""
        # Get trailing parameters for this leg
        trigger_pct = self.settings.trailing_trigger_pct[min(leg_number, len(self.settings.trailing_trigger_pct) - 1)]
        distance_pct = self.settings.trailing_distance_pct[min(leg_number, len(self.settings.trailing_distance_pct) - 1)]
        
        # Check if we should activate trailing stop
        if not self.trailing_stops_active[leg_number] and current_profit_pct >= trigger_pct:
            self.trailing_stops_active[leg_number] = True
            self.highest_profit_prices[leg_number] = market_data.price
            # Set initial trailing stop price
            if self.position_direction == 'long':
                self.trailing_stop_prices[leg_number] = market_data.price * (1 - distance_pct / 100)
            else:
                self.trailing_stop_prices[leg_number] = market_data.price * (1 + distance_pct / 100)
            return False
        
        # Update trailing stop if active
        if self.trailing_stops_active[leg_number]:
            # Update highest profit price
            if self.position_direction == 'long':
                if market_data.price > self.highest_profit_prices[leg_number]:
                    self.highest_profit_prices[leg_number] = market_data.price
                    # Update trailing stop price
                    new_stop_price = market_data.price * (1 - distance_pct / 100)
                    self.trailing_stop_prices[leg_number] = max(self.trailing_stop_prices[leg_number], new_stop_price)
                
                # Check if stop should be triggered
                return market_data.price <= self.trailing_stop_prices[leg_number]
            else:
                if market_data.price < self.highest_profit_prices[leg_number]:
                    self.highest_profit_prices[leg_number] = market_data.price
                    # Update trailing stop price
                    new_stop_price = market_data.price * (1 + distance_pct / 100)
                    self.trailing_stop_prices[leg_number] = min(self.trailing_stop_prices[leg_number], new_stop_price)
                
                # Check if stop should be triggered
                return market_data.price >= self.trailing_stop_prices[leg_number]
        
        return False
    
    def reset_trailing_stops(self):
        """Reset all trailing stop states"""
        self.trailing_stops_active = [False] * len(self.settings.order_sizes)
        self.trailing_stop_prices = [0.0] * len(self.settings.order_sizes)
        self.highest_profit_prices = [0.0] * len(self.settings.order_sizes)
    
    def calculate_position_size(self, leg_number: int, account_balance: float, current_price: float = None) -> float:
        """Calculate position size for a given leg (returns number of shares)"""
        # Debug logging for input parameters
        self.logger.info(f"calculate_position_size called with leg_number={leg_number}, account_balance={account_balance}, current_price={current_price}")
        
        if leg_number >= len(self.settings.order_sizes):
            # Use last size if we exceed defined sizes
            size_multiplier = self.settings.order_sizes[-1]
        else:
            size_multiplier = self.settings.order_sizes[leg_number]
        
        self.logger.info(f"Using size_multiplier={size_multiplier} for leg {leg_number}")
        
        # Check if using fixed position sizing
        if hasattr(self.settings, 'position_size_unit') and self.settings.position_size_unit == 'FIXED':
            if hasattr(self.settings, 'fixed_position_size') and self.settings.fixed_position_size > 0.0:
                # Use fixed position size with multiplier
                shares = self.settings.fixed_position_size * size_multiplier
                shares = max(0.001, min(shares, 100000))  # Allow fractional shares, higher max limit
                self.logger.info(f"Fixed position sizing: Base={self.settings.fixed_position_size}, Multiplier={size_multiplier:.2f}, Shares={shares}")
                return float(shares)
            elif hasattr(self.settings, 'fixed_position_size') and self.settings.fixed_position_size == 0.0:
                # Fixed Position Size is 0.0 - bypass fixed sizing and use only multiplier against capital allocation
                self.logger.info(f"Fixed Position Size is 0.0 - using percentage-based sizing with multiplier only")
                # Fall through to percentage-based calculation below
        
        # Default percentage-based position sizing
        base_allocation = self.settings.capital_allocation
        
        # Calculate dollar amount to invest
        dollar_amount = account_balance * base_allocation * size_multiplier
        
        # Convert to shares if current price is available
        if current_price and current_price > 0:
            shares = dollar_amount / current_price
            
            # Apply reasonable safety limits
            shares = max(0.001, min(shares, 100000))  # Min 0.001 shares, max 100000 shares
            
            self.logger.info(f"Percentage position sizing: Account=${account_balance:,.2f}, Base Allocation={base_allocation:.1%}, Multiplier={size_multiplier:.2f}, Dollar Amount=${dollar_amount:,.2f}, Price=${current_price:.2f}, Shares={shares:.6f}")
            
            # backtesting.py requires either a fraction (0 < size < 1) or a whole number (>= 1)
            if shares < 1.0:
                # If less than 1, treat as percentage of equity
                final_result = float(shares)
            else:
                # If >= 1, must be a whole number of shares
                shares = round(shares)
                final_result = float(shares)
            
            return final_result
        else:
            # Fallback: return a conservative number of shares
            fallback_shares = min(100.0, dollar_amount / 100.0)
            self.logger.warning(f"No current price available. Using fallback: {fallback_shares} shares (assuming $100/share)")
            self.logger.info(f"DEBUG: Returning fallback shares={fallback_shares}")
            return fallback_shares
    
    def get_distance_threshold(self, leg_number: int) -> float:
        """Get distance threshold for a given leg"""
        if leg_number >= len(self.settings.order_distances):
            return self.settings.order_distances[-1]
        return self.settings.order_distances[leg_number]
    
    def start_cycle(self, market_data: MarketData):
        """Start a new trading cycle"""
        self.is_active = True
        self.cycle_start_time = datetime.now()
        self.entry_price = market_data.price
        self.current_leg = 0
        self.positions.clear()
        self.pending_orders.clear()
        self.reset_trailing_stops()  # Reset trailing stops for new cycle
        self.reset_zone_tracking()  # Reset zone tracking for new cycle
        self.logger.info(f"Starting new cycle at price {market_data.price}")
    
    def end_cycle(self, market_data: MarketData):
        """End current trading cycle"""
        if not self.is_active:
            return
        
        # Calculate cycle performance
        cycle_pnl = sum(pos.unrealized_pnl for pos in self.positions)
        self.total_profit += cycle_pnl
        self.total_cycles += 1
        
        if cycle_pnl > 0:
            self.winning_cycles += 1
        
        # Update peak equity
        current_equity = self.total_profit
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        self.logger.info(f"Cycle ended. PnL: {cycle_pnl:.2f}, Total PnL: {self.total_profit:.2f}")
        
        # Reset state
        self.is_active = False
        self.current_leg = 0
        self.entry_price = None
        
        if not self.settings.hold_previous:
            self.positions.clear()
    
    def update_positions_price(self, market_data: MarketData):
        """Update current price for all positions"""
        for position in self.positions:
            if position.symbol == market_data.symbol:
                position.current_price = market_data.price
    
    def add_position(self, order_request: OrderRequest, fill_price: float):
        """Add a new position from filled order"""
        position = Position(
            symbol=order_request.symbol,
            quantity=order_request.quantity if order_request.action == OrderAction.BUY else -order_request.quantity,
            avg_price=fill_price,
            strategy_id=order_request.strategy_id,
            leg_number=order_request.leg_number,
            entry_time=datetime.now()
        )
        self.positions.append(position)
        
        # Update net position tracking
        self.update_net_position(order_request.quantity, order_request.action)
        
        # Track last order action for alternating logic
        self.last_order_action = order_request.action
        
        self.logger.info(f"Added position: {position.quantity} shares at {fill_price}, Net position: {self.net_position}")
    
    def get_total_position(self) -> float:
        """Get total position size across all legs"""
        return sum(pos.quantity for pos in self.positions)
    
    def get_average_price(self) -> float:
        """Get average entry price across all positions"""
        if not self.positions:
            return 0.0
        
        total_value = sum(pos.quantity * pos.avg_price for pos in self.positions)
        total_quantity = sum(abs(pos.quantity) for pos in self.positions)
        
        return total_value / total_quantity if total_quantity > 0 else 0.0
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized PnL"""
        return sum(pos.unrealized_pnl for pos in self.positions)
    
    def register_other_strategy(self, strategy_type: StrategyType, strategy: 'BaseStrategy'):
        """Register another strategy for coordination"""
        self.other_strategies[strategy_type] = strategy
        self.logger.info(f"Registered {strategy_type.value} strategy for coordination")
    
    def can_enter_based_on_alignment(self, market_data: MarketData) -> bool:
        """Check if strategy can enter based on alignment settings"""
        if not self.coordination_enabled:
            return True  # No coordination, can always enter
        
        if self.alignment_mode == "PARALLEL":
            return self._can_enter_parallel_mode(market_data)
        elif self.alignment_mode == "SEQUENTIAL":
            return self._can_enter_sequential_mode(market_data)
        
        return True
    
    def _can_enter_parallel_mode(self, market_data: MarketData) -> bool:
        """Check entry conditions for parallel mode"""
        if not self.parallel_start_mode:
            return True  # Independent operation
        
        # Check if we should start with another strategy
        target_strategy_type = StrategyType(self.strategy_to_start_with)
        if target_strategy_type in self.other_strategies:
            target_strategy = self.other_strategies[target_strategy_type]
            
            # Check if target strategy has reached the specified order number
            if target_strategy.current_leg >= self.order_number_to_start - 1:
                return True
            
            # If target strategy is not active yet, wait
            return target_strategy.is_active
        
        return True
    
    def _can_enter_sequential_mode(self, market_data: MarketData) -> bool:
        """Check entry conditions for sequential mode"""
        target_strategy_type = StrategyType(self.sequential_mode_strategy)
        
        if target_strategy_type in self.other_strategies:
            target_strategy = self.other_strategies[target_strategy_type]
            
            # First edge touch rule implementation
            if not self.first_edge_touched:
                # Check if target strategy has activated
                if target_strategy.is_active and target_strategy.current_leg > 0:
                    self.first_edge_touched = True
                    # If target strategy is moving in our favor, wait
                    if self._is_target_strategy_profitable(target_strategy, market_data):
                        self.waiting_for_other_strategy = True
                        return False
                    else:
                        # Target strategy going against, we can start
                        return True
                return False
            
            # If we're waiting and target strategy becomes unprofitable, we can start
            if self.waiting_for_other_strategy:
                if not self._is_target_strategy_profitable(target_strategy, market_data):
                    self.waiting_for_other_strategy = False
                    return True
                return False
        
        return True
    
    def _is_target_strategy_profitable(self, target_strategy: 'BaseStrategy', market_data: MarketData) -> bool:
        """Check if target strategy is currently profitable"""
        if not target_strategy.positions:
            return False
        
        total_pnl = sum(pos.unrealized_pnl for pos in target_strategy.positions)
        return total_pnl > 0
    
    def should_enter_with_coordination(self, market_data: MarketData) -> bool:
        """Enhanced entry logic with strategy coordination"""
        # First check base strategy entry conditions
        base_entry = self.should_enter(market_data)
        
        if not base_entry:
            return False
        
        # Then check alignment conditions
        return self.can_enter_based_on_alignment(market_data)
    
    def calculate_zone_boundaries(self, zone_center: float, leg_number: int) -> tuple:
        """Calculate zone boundaries based on distance thresholds"""
        distance_threshold = self.get_distance_threshold(leg_number)
        upper_boundary = zone_center * (1 + distance_threshold / 100)
        lower_boundary = zone_center * (1 - distance_threshold / 100)
        return upper_boundary, lower_boundary
    
    def update_net_position(self, quantity: float, action: OrderAction):
        """Update net position tracking"""
        if action == OrderAction.BUY:
            self.net_position += quantity
        else:
            self.net_position -= quantity
    
    def get_net_position(self) -> float:
        """Get current net position"""
        return self.net_position
    
    def detect_boundary_touched(self, market_data: MarketData, zone_center: float, leg_number: int) -> Optional[str]:
        """Detect which boundary was touched and return 'upper' or 'lower'"""
        upper_boundary, lower_boundary = self.calculate_zone_boundaries(zone_center, leg_number)
        
        if market_data.price >= upper_boundary:
            return 'upper'
        elif market_data.price <= lower_boundary:
            return 'lower'
        return None
    
    def get_alternating_action(self, boundary_touched: str) -> OrderAction:
        """Get alternating order action based on boundary touched and last action"""
        # For ZRM: alternate between BUY/SELL based on boundary
        # Upper boundary touch -> SELL (hedge against further rise)
        # Lower boundary touch -> BUY (hedge against further fall)
        if boundary_touched == 'upper':
            return OrderAction.SELL if self.last_order_action != OrderAction.SELL else OrderAction.BUY
        else:  # lower boundary
            return OrderAction.BUY if self.last_order_action != OrderAction.BUY else OrderAction.SELL
    
    def reset_zone_tracking(self):
        """Reset zone and boundary tracking for new cycle"""
        self.last_boundary_touched = None
        self.zone_upper_boundary = None
        self.zone_lower_boundary = None
        self.net_position = 0.0
        self.last_order_action = None
    
    def get_performance_stats(self) -> Dict:
        """Get strategy performance statistics"""
        win_rate = (self.winning_cycles / self.total_cycles * 100) if self.total_cycles > 0 else 0
        avg_profit = self.total_profit / self.total_cycles if self.total_cycles > 0 else 0
        
        return {
            'strategy_type': self.strategy_type.value,
            'symbol': self.settings.symbol,
            'total_cycles': self.total_cycles,
            'winning_cycles': self.winning_cycles,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'avg_profit_per_cycle': avg_profit,

            'current_positions': len(self.positions),
            'unrealized_pnl': self.get_unrealized_pnl()
        }

class CDMStrategy(BaseStrategy):
    """Counter Direction Martingale Strategy"""
    
    def __init__(self, settings):
        super().__init__(settings, StrategyType.CDM)
        self.last_price = None
    
    def should_enter(self, market_data: MarketData) -> bool:
        """Enter when price drops to trigger level or immediately if no trigger set"""
        if self.is_active:
            return False
        
        if self.settings.price_trigger is None:
            return True  # Enter immediately
        
        return market_data.price <= self.settings.price_trigger
    
    def should_add_leg(self, market_data: MarketData) -> bool:
        """Add leg when price drops by specified distance"""
        if not self.is_active or self.current_leg >= self.settings.max_orders:
            return False
        
        if self.entry_price is None:
            return False
        
        # Calculate required drop percentage for next leg
        distance_threshold = self.get_distance_threshold(self.current_leg)
        required_price = self.entry_price * (1 - distance_threshold / 100)
        
        return market_data.price <= required_price
    
    def should_exit(self, market_data: MarketData) -> bool:
        """Exit when price recovers to take profit level or trailing stop is triggered"""
        if not self.is_active or not self.positions:
            return False
        
        # Check trailing stops for each position
        for i, position in enumerate(self.positions):
            # Calculate current profit percentage for this position
            current_profit_pct = ((market_data.price - position.avg_price) / position.avg_price) * 100
            
            # Check if trailing stop should be triggered
            if self.update_trailing_stops(market_data, current_profit_pct, i):
                return True
        
        # Check if any position hits its take profit
        for i, position in enumerate(self.positions):
            if hasattr(self.settings, 'order_tps') and i < len(self.settings.order_tps):
                tp_pct = self.settings.order_tps[i]
                tp_price = position.avg_price * (1 + tp_pct / 100)
                
                if market_data.price >= tp_price:
                    return True
        
        # Default: exit when price recovers above average entry price (reduced threshold)
        avg_price = self.get_average_price()
        return market_data.price >= avg_price * 1.005  # 0.5% above average (more achievable)

class WDMStrategy(BaseStrategy):
    """With Direction Martingale Strategy"""
    
    def __init__(self, settings):
        super().__init__(settings, StrategyType.WDM)
        self.peak_price = None
    
    def should_enter(self, market_data: MarketData) -> bool:
        """Enter when price rises to trigger level or immediately if no trigger set"""
        if self.is_active:
            return False
        
        if self.settings.price_trigger is None:
            return True
        
        return market_data.price >= self.settings.price_trigger
    
    def should_add_leg(self, market_data: MarketData) -> bool:
        """Add leg when price rises by specified distance"""
        if not self.is_active or self.current_leg >= self.settings.max_orders:
            return False
        
        if self.entry_price is None:
            return False
        
        # Calculate required rise percentage for next leg
        distance_threshold = self.get_distance_threshold(self.current_leg)
        required_price = self.entry_price * (1 + distance_threshold / 100)
        
        return market_data.price >= required_price
    
    def should_exit(self, market_data: MarketData) -> bool:
        """Exit when price retraces from peak"""
        if not self.is_active or not self.positions:
            return False
        
        # Track peak price
        if self.peak_price is None or market_data.price > self.peak_price:
            self.peak_price = market_data.price
        
        # Check stop loss levels
        for i, position in enumerate(self.positions):
            if hasattr(self.settings, 'order_sls') and i < len(self.settings.order_sls):
                sl_pct = self.settings.order_sls[i]
                sl_price = self.peak_price * (1 - sl_pct / 100)
                
                if market_data.price <= sl_price:
                    return True
        
        return False

class ZRMStrategy(BaseStrategy):
    """Zone Recovery Martingale Strategy"""
    
    def __init__(self, settings):
        super().__init__(settings, StrategyType.ZRM)
        self.zone_center = settings.zone_center_price
    
    def should_enter(self, market_data: MarketData) -> bool:
        """Enter when price matches zone center"""
        if self.is_active:
            return False
        
        if self.zone_center is None:
            self.zone_center = market_data.price
            return True
        
        return market_data.price == self.zone_center
    
    def should_add_leg(self, market_data: MarketData) -> bool:
        """Add leg based on zone boundary touches with alternating logic"""
        if not self.is_active or self.current_leg >= self.settings.max_orders:
            return False
        
        if self.zone_center is None:
            return False
        
        # Detect which boundary was touched
        boundary_touched = self.detect_boundary_touched(market_data, self.zone_center, self.current_leg)
        
        if boundary_touched:
            # Update boundary tracking
            self.last_boundary_touched = boundary_touched
            
            # Update zone boundaries for this leg
            self.zone_upper_boundary, self.zone_lower_boundary = self.calculate_zone_boundaries(
                self.zone_center, self.current_leg
            )
            
            return True
        
        return False
    
    def get_leg_order_action(self, market_data: MarketData) -> OrderAction:
        """Get order action for current leg based on boundary touched and alternating logic"""
        if self.last_boundary_touched:
            return self.get_alternating_action(self.last_boundary_touched)
        
        # Default to BUY for first leg or when no boundary detected
        return OrderAction.BUY
    
    def should_exit(self, market_data: MarketData) -> bool:
        """Exit when hitting take profit, trailing stop, or net position is profitable"""
        if not self.is_active or not self.positions:
            return False
        
        # Calculate net position PnL
        net_pnl = self.calculate_net_position_pnl(market_data.price)
        
        # Exit if net position is profitable (basic recovery achieved)
        if net_pnl > 0:
            return True
        
        # Check trailing stops for each position
        for i, position in enumerate(self.positions):
            # Calculate current profit percentage for this position
            current_profit_pct = ((market_data.price - position.avg_price) / position.avg_price) * 100
            
            # Check if trailing stop should be triggered
            if self.update_trailing_stops(market_data, current_profit_pct, i):
                return True
        
        # Check take profit levels
        for i, position in enumerate(self.positions):
            if hasattr(self.settings, 'order_tps') and i < len(self.settings.order_tps):
                tp_pct = self.settings.order_tps[i]
                tp_price = position.avg_price * (1 + tp_pct / 100)
                
                if market_data.price >= tp_price:
                    return True
        
        return False
    
    def calculate_net_position_pnl(self, current_price: float) -> float:
        """Calculate PnL based on net position"""
        if not self.positions:
            return 0.0
        
        total_pnl = 0.0
        for position in self.positions:
            position_pnl = (current_price - position.avg_price) * position.quantity
            total_pnl += position_pnl
        
        return total_pnl

class IZRMStrategy(BaseStrategy):
    """Inverse Zone Recovery Martingale Strategy"""
    
    def __init__(self, settings):
        super().__init__(settings, StrategyType.IZRM)
        self.zone_center = settings.zone_center_price
        self.breakout_direction = None
    
    def should_enter(self, market_data: MarketData) -> bool:
        """Enter when price moves away from zone center"""
        if self.is_active:
            return False
        
        if self.zone_center is None:
            self.zone_center = market_data.price
            return False
        
        # Enter when price moves away from center
        if market_data.price > self.zone_center:
            self.breakout_direction = "UP"
            return True
        elif market_data.price < self.zone_center:
            self.breakout_direction = "DOWN"
            return True
        
        return False
    
    def should_add_leg(self, market_data: MarketData) -> bool:
        """Add leg based on zone boundary touches in breakout direction"""
        if not self.is_active or self.current_leg >= self.settings.max_orders:
            return False
        
        if self.zone_center is None:
            return False
        
        # Detect boundary touch in breakout direction
        boundary_touched = self.detect_boundary_touched(market_data, self.zone_center, self.current_leg)
        
        if boundary_touched:
            # For IZRM, only add legs in the breakout direction
            if (self.breakout_direction == "UP" and boundary_touched == "upper") or \
               (self.breakout_direction == "DOWN" and boundary_touched == "lower"):
                
                # Update boundary tracking
                self.last_boundary_touched = boundary_touched
                
                # Update zone boundaries for this leg
                self.zone_upper_boundary, self.zone_lower_boundary = self.calculate_zone_boundaries(
                    self.zone_center, self.current_leg
                )
                
                return True
        
        return False
    
    def get_leg_order_action(self, market_data: MarketData) -> OrderAction:
        """Get order action for current leg based on breakout direction and alternating logic"""
        if self.last_boundary_touched:
            # For IZRM, use alternating logic but consider breakout direction
            return self.get_alternating_action(self.last_boundary_touched)
        
        # Default action based on breakout direction
        if self.breakout_direction == "UP":
            return OrderAction.SELL  # Sell into strength
        else:
            return OrderAction.BUY   # Buy into weakness
    
    def should_exit(self, market_data: MarketData) -> bool:
        """Exit when price reverses back to zone center, net position is profitable, or hits stop loss"""
        if not self.is_active or not self.positions:
            return False
        
        # Calculate net position PnL
        net_pnl = self.calculate_net_position_pnl(market_data.price)
        
        # Exit if net position is profitable (recovery achieved)
        if net_pnl > 0:
            return True
        
        # Exit when back at zone center (reversal)
        if abs(market_data.price - self.zone_center) / self.zone_center < 0.001:  # Within 0.1% of center
            return True
        
        # Also check stop loss levels
        for i, position in enumerate(self.positions):
            if hasattr(self.settings, 'order_sls') and i < len(self.settings.order_sls):
                sl_pct = self.settings.order_sls[i]
                
                if position.quantity > 0:  # Long position
                    sl_price = position.avg_price * (1 - sl_pct / 100)
                    if market_data.price <= sl_price:
                        return True
                else:  # Short position
                    sl_price = position.avg_price * (1 + sl_pct / 100)
                    if market_data.price >= sl_price:
                        return True
        
        return False
    
    def calculate_net_position_pnl(self, current_price: float) -> float:
        """Calculate PnL based on net position"""
        if not self.positions:
            return 0.0
        
        total_pnl = 0.0
        for position in self.positions:
            position_pnl = (current_price - position.avg_price) * position.quantity
            total_pnl += position_pnl
        
        return total_pnl

def create_strategy(strategy_type: StrategyType, settings: StrategySettings) -> BaseStrategy:
    """Factory function to create strategy instances"""
    strategy_map = {
        StrategyType.CDM: CDMStrategy,
        StrategyType.WDM: WDMStrategy,
        StrategyType.ZRM: ZRMStrategy,
        StrategyType.IZRM: IZRMStrategy
    }
    
    strategy_class = strategy_map.get(strategy_type)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    return strategy_class(settings)