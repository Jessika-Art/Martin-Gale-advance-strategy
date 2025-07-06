"""Main trading engine for Multi-Martingales Trading Bot"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json

from config import TradingConfig, StrategyType, ExecutionMode, AccountType
from strategies import BaseStrategy, create_strategy, MarketData, OrderRequest, OrderAction, Position
from ibkr_api import IBKRApi, IBOrder, IBPosition

class EngineState(Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"

@dataclass
class TradingCycle:
    """Trading cycle tracking"""
    cycle_id: str
    strategy_type: StrategyType
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    positions: List[Position] = None
    total_pnl: float = 0.0
    trade_count: int = 0
    
    def __post_init__(self):
        if self.positions is None:
            self.positions = []

class TradingEngine:
    """Main trading engine coordinating all strategies"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger("TradingEngine")
        
        # Engine state
        self.state = EngineState.STOPPED
        self.start_time: Optional[datetime] = None
        self.stop_requested = False
        
        # API connection
        self.api: Optional[IBKRApi] = None
        
        # Strategy management
        self.strategies: Dict[str, BaseStrategy] = {}  # key: f"{strategy_type}_{symbol}"
        self.active_symbols: Set[str] = set()
        
        # Position and order tracking
        self.all_positions: Dict[str, List[Position]] = {}  # key: symbol
        self.pending_orders: Dict[int, OrderRequest] = {}  # key: order_id
        self.completed_cycles: List[TradingCycle] = []
        
        # Performance tracking
        self.total_trades = 0
        self.total_pnl = 0.0
        self.peak_equity = 0.0
        
        # Threading
        self.engine_thread: Optional[threading.Thread] = None
        self.running_lock = threading.Lock()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.INFO
        if hasattr(self.config, 'debug') and self.config.debug:
            log_level = logging.DEBUG
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'trading_bot_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize(self) -> bool:
        """Initialize the trading engine"""
        try:
            self.logger.info("Initializing trading engine...")
            self.state = EngineState.STARTING
            
            # Initialize API connection
            if not self._initialize_api():
                self.state = EngineState.ERROR
                return False
            
            # Initialize strategies
            if not self._initialize_strategies():
                self.state = EngineState.ERROR
                return False
            
            # Subscribe to market data
            if not self._subscribe_market_data():
                self.state = EngineState.ERROR
                return False
            
            # Request initial account and position data
            self._request_initial_data()
            
            self.logger.info("Trading engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize trading engine: {e}")
            self.state = EngineState.ERROR
            return False
    
    def _initialize_api(self) -> bool:
        """Initialize IBKR API connection"""
        try:
            self.api = IBKRApi(self.config.ib_config, self.config.account_type)
            
            # Register as global instance
            from ibkr_api import set_api_instance
            set_api_instance(self.api)
            
            # Add callbacks
            self.api.add_market_data_callback(self._on_market_data)
            self.api.add_order_status_callback(self._on_order_status)
            self.api.add_position_callback(self._on_position_update)
            
            # Connect to IB
            if not self.api.connect_to_ib():
                self.logger.error("Failed to connect to Interactive Brokers")
                return False
            
            self.logger.info(f"Connected to IB ({self.config.account_type.value} account)")
            return True
            
        except Exception as e:
            self.logger.error(f"API initialization failed: {e}")
            return False
    
    def _initialize_strategies(self) -> bool:
        """Initialize trading strategies"""
        try:
            for symbol in self.config.tickers:
                for strategy_type in self.config.active_strategies:
                    # Get strategy-specific settings
                    strategy_settings = self.config.get_strategy_settings(strategy_type)
                    
                    if strategy_settings:
                        # Set symbol for this strategy instance
                        strategy_settings.symbol = symbol
                        # Create strategy instance
                        strategy = create_strategy(strategy_type, strategy_settings)
                        strategy_key = f"{strategy_type.value}_{symbol}"
                        self.strategies[strategy_key] = strategy
                        
                        self.logger.info(f"Initialized {strategy_type.value} strategy for {symbol}")
            
            self.logger.info(f"Initialized {len(self.strategies)} strategies")
            return True
            
        except Exception as e:
            self.logger.error(f"Strategy initialization failed: {e}")
            return False
    
    def _subscribe_market_data(self) -> bool:
        """Subscribe to market data for all symbols"""
        try:
            for symbol in self.config.tickers:
                if self.api.subscribe_market_data(symbol):
                    self.active_symbols.add(symbol)
                else:
                    self.logger.error(f"Failed to subscribe to market data for {symbol}")
                    return False
            
            self.logger.info(f"Subscribed to market data for {len(self.active_symbols)} symbols")
            return True
            
        except Exception as e:
            self.logger.error(f"Market data subscription failed: {e}")
            return False
    
    def _request_initial_data(self):
        """Request initial account and position data"""
        if self.api:
            self.api.request_account_summary()
            self.api.request_positions()
            time.sleep(2)  # Give time for data to arrive
    
    def start(self) -> bool:
        """Start the trading engine"""
        with self.running_lock:
            if self.state == EngineState.RUNNING:
                self.logger.warning("Trading engine is already running")
                return True
            
            if not self.initialize():
                return False
            
            self.state = EngineState.RUNNING
            self.start_time = datetime.now()
            self.stop_requested = False
            
            # Start main engine thread
            self.engine_thread = threading.Thread(target=self._run_engine, daemon=True)
            self.engine_thread.start()
            
            self.logger.info("Trading engine started")
            return True
    
    def stop(self):
        """Stop the trading engine"""
        with self.running_lock:
            if self.state != EngineState.RUNNING:
                self.logger.warning("Trading engine is not running")
                return
            
            self.logger.info("Stopping trading engine...")
            self.state = EngineState.STOPPING
            self.stop_requested = True
            
            # Wait for engine thread to finish
            if self.engine_thread and self.engine_thread.is_alive():
                self.engine_thread.join(timeout=10)
            
            # Cleanup
            self._cleanup()
            
            self.state = EngineState.STOPPED
            self.logger.info("Trading engine stopped")
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            # Unsubscribe from market data
            if self.api:
                for symbol in self.active_symbols:
                    self.api.unsubscribe_market_data(symbol)
                
                # Disconnect from IB
                self.api.disconnect_from_ib()
            
            # Save performance data
            self._save_performance_data()
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def _run_engine(self):
        """Main engine loop"""
        self.logger.info("Engine main loop started")
        
        try:
            while not self.stop_requested and self.state == EngineState.RUNNING:
                # Check if market is open (if configured)
                if hasattr(self.config.shared_settings, 'pre_after_hours') and not self.config.shared_settings.pre_after_hours:
                    if not self.api.is_market_open():
                        time.sleep(60)  # Check every minute
                        continue
                
                # Process strategies
                self._process_strategies()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Sleep before next iteration
                time.sleep(1)  # 1 second intervals
                
        except Exception as e:
            self.logger.error(f"Engine loop error: {e}")
            self.state = EngineState.ERROR
        
        self.logger.info("Engine main loop ended")
    
    def _process_strategies(self):
        """Process all active strategies"""
        for strategy_key, strategy in self.strategies.items():
            try:
                symbol = strategy.settings.symbol
                market_data = self.api.get_market_data(symbol)
                
                if not market_data:
                    continue
                
                # Update strategy with latest market data
                strategy.update_positions_price(market_data)
                
                # Check for entry signals
                if not strategy.is_active and strategy.should_enter(market_data):
                    self._handle_strategy_entry(strategy, market_data)
                
                # Check for additional legs
                elif strategy.is_active and strategy.should_add_leg(market_data):
                    self._handle_strategy_add_leg(strategy, market_data)
                
                # Check for exit signals
                elif strategy.is_active and strategy.should_exit(market_data):
                    self._handle_strategy_exit(strategy, market_data)
                
            except Exception as e:
                self.logger.error(f"Error processing strategy {strategy_key}: {e}")
    
    def _handle_strategy_entry(self, strategy: BaseStrategy, market_data: MarketData):
        """Handle strategy entry signal"""
        try:
            strategy.start_cycle(market_data)
            
            # Calculate position size
            account_balance = self.api.get_account_balance()
            position_size = strategy.calculate_position_size(0, account_balance, market_data.price)
            
            # Determine order action based on strategy type
            if strategy.strategy_type in [StrategyType.CDM, StrategyType.ZRM]:
                action = OrderAction.BUY  # Counter-trend strategies typically buy on dips
            else:
                action = OrderAction.BUY  # Trend-following strategies buy on momentum
            
            # Create order request
            order_request = OrderRequest(
                symbol=market_data.symbol,
                action=action,
                quantity=position_size,
                order_type="MARKET",
                strategy_id=f"{strategy.strategy_type.value}_{market_data.symbol}",
                leg_number=0
            )
            
            # Place order
            order_id = self.api.place_order(order_request)
            if order_id:
                self.pending_orders[order_id] = order_request
                strategy.current_leg = 1
                self.logger.info(f"Entry order placed for {strategy.strategy_type.value} on {market_data.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error handling strategy entry: {e}")
    
    def _handle_strategy_add_leg(self, strategy: BaseStrategy, market_data: MarketData):
        """Handle adding another leg to strategy with alternating order logic"""
        try:
            # Calculate position size for this leg
            account_balance = self.api.get_account_balance()
            position_size = strategy.calculate_position_size(strategy.current_leg, account_balance, market_data.price)
            
            # Determine order action based on strategy type and boundary logic
            if strategy.strategy_type in [StrategyType.ZRM, StrategyType.IZRM]:
                # Use strategy-specific alternating logic for zone strategies
                if hasattr(strategy, 'get_leg_order_action'):
                    action = strategy.get_leg_order_action(market_data)
                else:
                    action = OrderAction.BUY  # Fallback
            elif strategy.strategy_type == StrategyType.CDM:
                action = OrderAction.BUY  # Counter-trend: always buy on dips
            else:
                action = OrderAction.BUY  # Default for other strategies
            
            # Create order request
            order_request = OrderRequest(
                symbol=market_data.symbol,
                action=action,
                quantity=position_size,
                order_type="MARKET",
                strategy_id=f"{strategy.strategy_type.value}_{market_data.symbol}",
                leg_number=strategy.current_leg
            )
            
            # Place order
            order_id = self.api.place_order(order_request)
            if order_id:
                self.pending_orders[order_id] = order_request
                strategy.current_leg += 1
                self.logger.info(f"Added leg {strategy.current_leg} ({action.value}) for {strategy.strategy_type.value} on {market_data.symbol}, Boundary: {getattr(strategy, 'last_boundary_touched', 'N/A')}")
            
        except Exception as e:
            self.logger.error(f"Error adding strategy leg: {e}")
    
    def _handle_strategy_exit(self, strategy: BaseStrategy, market_data: MarketData):
        """Handle strategy exit signal"""
        try:
            # Close all positions for this strategy
            total_position = strategy.get_total_position()
            
            if total_position != 0:
                # Determine exit action (opposite of position)
                action = OrderAction.SELL if total_position > 0 else OrderAction.BUY
                
                # Create exit order
                order_request = OrderRequest(
                    symbol=market_data.symbol,
                    action=action,
                    quantity=abs(total_position),
                    order_type="MARKET",
                    strategy_id=f"{strategy.strategy_type.value}_{market_data.symbol}",
                    leg_number=-1  # Exit order
                )
                
                # Place exit order
                order_id = self.api.place_order(order_request)
                if order_id:
                    self.pending_orders[order_id] = order_request
                    self.logger.info(f"Exit order placed for {strategy.strategy_type.value} on {market_data.symbol}")
            
            # End strategy cycle
            strategy.end_cycle(market_data)
            
            # Record completed cycle
            self._record_completed_cycle(strategy, market_data)
            
        except Exception as e:
            self.logger.error(f"Error handling strategy exit: {e}")
    
    def _record_completed_cycle(self, strategy: BaseStrategy, market_data: MarketData):
        """Record a completed trading cycle"""
        try:
            cycle = TradingCycle(
                cycle_id=f"{strategy.strategy_type.value}_{market_data.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                strategy_type=strategy.strategy_type,
                symbol=market_data.symbol,
                start_time=strategy.cycle_start_time or datetime.now(),
                end_time=datetime.now(),
                positions=strategy.positions.copy(),
                total_pnl=strategy.get_unrealized_pnl(),
                trade_count=len(strategy.positions)
            )
            
            self.completed_cycles.append(cycle)
            self.total_trades += cycle.trade_count
            
        except Exception as e:
            self.logger.error(f"Error recording completed cycle: {e}")
    
    def _update_performance_metrics(self):
        """Update overall performance metrics"""
        try:
            # Calculate total unrealized PnL across all strategies
            total_unrealized_pnl = 0.0
            for strategy in self.strategies.values():
                total_unrealized_pnl += strategy.get_unrealized_pnl()
            
            # Update peak equity
            current_equity = self.total_pnl + total_unrealized_pnl
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def _save_performance_data(self):
        """Save performance data to file"""
        try:
            performance_data = {
                'engine_stats': {
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'end_time': datetime.now().isoformat(),
                    'total_trades': self.total_trades,
                    'total_pnl': self.total_pnl,

                    'peak_equity': self.peak_equity
                },
                'strategy_stats': {},
                'completed_cycles': []
            }
            
            # Add strategy statistics
            for strategy_key, strategy in self.strategies.items():
                performance_data['strategy_stats'][strategy_key] = strategy.get_performance_stats()
            
            # Add completed cycles
            for cycle in self.completed_cycles:
                cycle_data = {
                    'cycle_id': cycle.cycle_id,
                    'strategy_type': cycle.strategy_type.value,
                    'symbol': cycle.symbol,
                    'start_time': cycle.start_time.isoformat(),
                    'end_time': cycle.end_time.isoformat() if cycle.end_time else None,
                    'total_pnl': cycle.total_pnl,
                    'trade_count': cycle.trade_count
                }
                performance_data['completed_cycles'].append(cycle_data)
            
            # Save to file
            filename = f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(performance_data, f, indent=2)
            
            self.logger.info(f"Performance data saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving performance data: {e}")
    
    # Callback methods
    def _on_market_data(self, market_data: MarketData):
        """Handle market data updates"""
        # Market data is automatically processed in the main loop
        pass
    
    def _on_order_status(self, order: IBOrder):
        """Handle order status updates"""
        try:
            if order.order_id in self.pending_orders:
                order_request = self.pending_orders[order.order_id]
                
                if order.status == "Filled":
                    # Find corresponding strategy
                    strategy_key = order_request.strategy_id
                    if strategy_key in self.strategies:
                        strategy = self.strategies[strategy_key]
                        
                        # Add position to strategy
                        if order_request.leg_number >= 0:  # Not an exit order
                            strategy.add_position(order_request, order.avg_fill_price)
                        
                        self.logger.info(f"Order {order.order_id} filled at {order.avg_fill_price}")
                    
                    # Remove from pending orders
                    del self.pending_orders[order.order_id]
                
                elif order.status in ["Cancelled", "Rejected"]:
                    self.logger.warning(f"Order {order.order_id} {order.status.lower()}")
                    del self.pending_orders[order.order_id]
            
        except Exception as e:
            self.logger.error(f"Error handling order status: {e}")
    
    def _on_position_update(self, position: IBPosition):
        """Handle position updates from IB"""
        try:
            # Update position tracking
            if position.symbol not in self.all_positions:
                self.all_positions[position.symbol] = []
            
            # This could be used for reconciliation with strategy positions
            self.logger.debug(f"Position update: {position.symbol} {position.position} @ {position.avg_cost}")
            
        except Exception as e:
            self.logger.error(f"Error handling position update: {e}")
    
    # Public methods for monitoring
    def get_engine_status(self) -> Dict:
        """Get current engine status"""
        return {
            'state': self.state.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'active_strategies': len(self.strategies),
            'active_symbols': list(self.active_symbols),
            'pending_orders': len(self.pending_orders),
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl,

            'account_balance': self.api.get_account_balance() if self.api else 0.0
        }
    
    def get_strategy_status(self) -> Dict:
        """Get status of all strategies"""
        status = {}
        for strategy_key, strategy in self.strategies.items():
            status[strategy_key] = {
                'is_active': strategy.is_active,
                'current_leg': strategy.current_leg,
                'positions': len(strategy.positions),
                'unrealized_pnl': strategy.get_unrealized_pnl(),
                'total_cycles': strategy.total_cycles,
                'winning_cycles': strategy.winning_cycles,
                'win_rate': (strategy.winning_cycles / strategy.total_cycles * 100) if strategy.total_cycles > 0 else 0
            }
        return status
    
    def force_exit_all(self):
        """Force exit all active strategies"""
        self.logger.warning("Force exiting all strategies")
        
        for strategy in self.strategies.values():
            if strategy.is_active:
                # Get latest market data
                market_data = self.api.get_market_data(strategy.settings.symbol)
                if market_data:
                    self._handle_strategy_exit(strategy, market_data)