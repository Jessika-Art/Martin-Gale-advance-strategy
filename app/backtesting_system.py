import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import logging
import uuid

from config import TradingConfig, StrategyType, StrategySettings
from strategies import CDMStrategy, WDMStrategy, ZRMStrategy, IZRMStrategy, MarketData, OrderAction, Position
from cycle_analysis import CycleAnalyzer, Trade, TradeType, CycleAnalysisReport
from risk_manager import GlobalRiskManager

class BacktestingAdapter:
    """Adapter to convert our strategies to backtesting.py format"""
    
    def __init__(self, config: TradingConfig, selected_strategies: List[StrategyType]):
        self.config = config
        self.selected_strategies = selected_strategies
        self.logger = logging.getLogger(__name__)
        self.cycle_analyzer = CycleAnalyzer()
        
        # Initialize global risk manager
        shared_settings = getattr(config, 'shared_settings', None)
        if shared_settings:
            self.risk_manager = GlobalRiskManager(
                max_concurrent_cycles=shared_settings.global_max_concurrent_cycles,
                daily_loss_limit=shared_settings.global_daily_loss_limit,
                daily_profit_target=shared_settings.global_daily_profit_target
            )
        else:
            self.risk_manager = GlobalRiskManager()
        
    def fetch_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1h') -> pd.DataFrame:
        """Fetch historical data using yfinance"""
        try:
            # Convert interval format using config mapping
            from config import get_yfinance_interval
            yf_interval = get_yfinance_interval(interval)
            
            # Check for yfinance limitations before making the request
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            days_back = (datetime.now() - start_dt).days
            
            intraday_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '2h', '4h']
            if yf_interval in intraday_intervals and days_back > 730:
                raise ValueError(
                    f"Intraday data ({interval}) is only available for the last 730 days. "
                    f"Your start date ({start_date}) is {days_back} days ago. "
                    f"Please select a more recent start date or use daily (1d) timeframe for longer periods."
                )
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=False  # Exclude pre/post market data to avoid unrealistic wicks
            )
            
            if data.empty:
                # Provide more specific error message based on timeframe
                if yf_interval in intraday_intervals:
                    error_msg = (
                        f"No intraday data found for {symbol} from {start_date} to {end_date}. "
                        f"This could be because: \n"
                        f"1. The date range is too old (intraday data limited to 730 days)\n"
                        f"2. The symbol doesn't exist or is delisted\n"
                        f"3. No trading occurred during this period\n"
                        f"Try using a more recent date range or daily (1d) timeframe."
                    )
                else:
                    error_msg = f"No data found for {symbol} from {start_date} to {end_date}. Please check the symbol and date range."
                raise ValueError(error_msg)
            
            # Ensure required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Clean data
            data = data.dropna()
            
            # Validate data quality
            if len(data) < 10:
                raise ValueError(f"Insufficient data: only {len(data)} data points found. Need at least 10 data points for backtesting.")
            
            # Check for data gaps
            if data.isnull().any().any():
                self.logger.warning(f"Data contains null values for {symbol}, cleaning...")
                data = data.fillna(method='ffill').fillna(method='bfill')
            
            # Ensure data is sorted by date
            data = data.sort_index()
            
            # Validate price data integrity
            for col in ['Open', 'High', 'Low', 'Close']:
                if (data[col] <= 0).any():
                    raise ValueError(f"Invalid price data: {col} contains zero or negative values")
            
            # Additional data quality validation for unrealistic wicks
            data = self._validate_and_clean_candle_data(data, symbol, interval)
            
            self.logger.info(f"Fetched and validated {len(data)} data points for {symbol} from {start_date} to {end_date}")
            return data
            
        except Exception as e:
            # Enhanced error handling with more specific messages
            error_msg = str(e)
            if "730 days" in error_msg or "not available for startTime" in error_msg:
                enhanced_msg = (
                    f"yfinance limitation: Intraday data ({interval}) is only available for the last 730 days. "
                    f"Your requested date range is too old. Please either:\n"
                    f"1. Use a more recent start date (within the last 2 years)\n"
                    f"2. Switch to daily (1d) timeframe for longer historical periods"
                )
                self.logger.error(enhanced_msg)
                raise ValueError(enhanced_msg)
            else:
                self.logger.error(f"Error fetching data for {symbol}: {error_msg}")
                raise
    
    def _validate_and_clean_candle_data(self, data: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        """Validate and clean candle data to remove unrealistic wicks and anomalies"""
        if data.empty:
            return data
        
        original_count = len(data)
        
        # Check for basic OHLC relationship violations
        invalid_high = (data['High'] < data['Open']) | (data['High'] < data['Close']) | (data['High'] < data['Low'])
        invalid_low = (data['Low'] > data['Open']) | (data['Low'] > data['Close']) | (data['Low'] > data['High'])
        
        if invalid_high.any() or invalid_low.any():
            self.logger.warning(f"Found {invalid_high.sum() + invalid_low.sum()} candles with OHLC violations for {symbol}")
            # Remove invalid candles
            data = data[~(invalid_high | invalid_low)]
        
        # Detect and filter extreme wicks (likely data errors)
        body_size = abs(data['Close'] - data['Open'])
        upper_wick = data['High'] - data[['Open', 'Close']].max(axis=1)
        lower_wick = data[['Open', 'Close']].min(axis=1) - data['Low']
        
        # Calculate wick-to-body ratios (avoid division by zero)
        min_body_size = 0.01  # Minimum body size to avoid extreme ratios on doji candles
        effective_body_size = body_size.where(body_size >= min_body_size, min_body_size)
        
        upper_wick_ratio = upper_wick / effective_body_size
        lower_wick_ratio = lower_wick / effective_body_size
        
        # Define thresholds based on timeframe
        if interval in ['1m', '5m', '15m', '30m']:
            max_wick_ratio = 20  # More lenient for shorter timeframes
        elif interval in ['1h', '2h', '4h']:
            max_wick_ratio = 15  # Moderate threshold for hourly data
        else:
            max_wick_ratio = 10  # Stricter for daily and longer timeframes
        
        extreme_wicks = (upper_wick_ratio > max_wick_ratio) | (lower_wick_ratio > max_wick_ratio)
        
        if extreme_wicks.any():
            self.logger.warning(
                f"Found {extreme_wicks.sum()} candles with extreme wicks (>{max_wick_ratio}x body) for {symbol} {interval}. "
                f"These may be data errors and will be filtered out."
            )
            
            # Log some examples for debugging
            extreme_samples = data[extreme_wicks].head(3)
            for idx, row in extreme_samples.iterrows():
                body = abs(row['Close'] - row['Open'])
                u_wick = row['High'] - max(row['Open'], row['Close'])
                l_wick = min(row['Open'], row['Close']) - row['Low']
                u_ratio = u_wick / max(body, min_body_size)
                l_ratio = l_wick / max(body, min_body_size)
                self.logger.debug(
                    f"Extreme wick at {idx}: O={row['Open']:.2f} H={row['High']:.2f} L={row['Low']:.2f} C={row['Close']:.2f} "
                    f"(upper: {u_ratio:.1f}x, lower: {l_ratio:.1f}x)"
                )
            
            # Remove extreme wick candles
            data = data[~extreme_wicks]
        
        # Check for extreme price ranges (potential data errors)
        price_range = data['High'] - data['Low']
        median_range = price_range.median()
        extreme_range_threshold = median_range * 8  # 8x median range
        
        extreme_ranges = price_range > extreme_range_threshold
        
        if extreme_ranges.any():
            self.logger.warning(
                f"Found {extreme_ranges.sum()} candles with extreme price ranges (>{extreme_range_threshold:.2f}) for {symbol} {interval}"
            )
            # Remove extreme range candles
            data = data[~extreme_ranges]
        
        cleaned_count = len(data)
        if cleaned_count < original_count:
            self.logger.info(
                f"Cleaned candle data for {symbol} {interval}: removed {original_count - cleaned_count} problematic candles "
                f"({cleaned_count} remaining)"
            )
        
        # Ensure we still have sufficient data after cleaning
        if len(data) < 10:
            self.logger.warning(
                f"After data cleaning, only {len(data)} candles remain for {symbol} {interval}. "
                f"This may not be sufficient for reliable backtesting."
            )
        
        return data
    
    def create_combined_strategy(self, symbol: str) -> type:
        """Create a combined strategy class for backtesting"""
        
        # Capture references to pass to the strategy
        risk_manager = self.risk_manager
        cycle_analyzer = self.cycle_analyzer
        config = self.config
        selected_strategies = self.selected_strategies
        logger = self.logger
        
        class CombinedMartingaleStrategy(Strategy):
            def init(self):
                # Initialize strategy instances
                self.strategies = {}
                self.initial_cash = 100000  # Default initial cash
                
                # Set references from outer scope
                self.risk_manager = risk_manager
                self.cycle_analyzer = cycle_analyzer
                self.config = config
                self.selected_strategies = selected_strategies
                self.logger = logger
                
                for strategy_type in self.selected_strategies:
                    settings = self.config.get_strategy_settings(strategy_type)
                    settings.symbol = symbol
                    
                    if strategy_type == StrategyType.CDM:
                        self.strategies[strategy_type] = CDMStrategy(settings)
                    elif strategy_type == StrategyType.WDM:
                        self.strategies[strategy_type] = WDMStrategy(settings)
                    elif strategy_type == StrategyType.ZRM:
                        self.strategies[strategy_type] = ZRMStrategy(settings)
                    elif strategy_type == StrategyType.IZRM:
                        self.strategies[strategy_type] = IZRMStrategy(settings)
                
                # Register strategies with each other for coordination
                for strategy_type, strategy in self.strategies.items():
                    for other_type, other_strategy in self.strategies.items():
                        if strategy_type != other_type:
                            strategy.register_other_strategy(other_type, other_strategy)
                
                # Track positions for each strategy
                self.strategy_positions = {st: [] for st in self.selected_strategies}
                self.strategy_cash = {st: self.initial_cash / len(self.selected_strategies) for st in self.selected_strategies}
                
                # Cycle tracking
                self.active_cycles = {st: None for st in self.selected_strategies}
                
            def next(self):
                current_price = self.data.Close[-1]
                current_time = self.data.index[-1]
                
                # Check market hours if pre_after_hours is disabled
                shared_settings = getattr(self.config, 'shared_settings', None)
                if shared_settings and not shared_settings.pre_after_hours:
                    # Check if current time is within market hours (9:30 AM - 4:00 PM ET)
                    try:
                        import pytz
                        if hasattr(current_time, 'tz_localize'):
                            # Convert to ET if timezone-naive
                            if current_time.tz is None:
                                current_time_et = current_time.tz_localize('UTC').tz_convert('US/Eastern')
                            else:
                                current_time_et = current_time.tz_convert('US/Eastern')
                        else:
                            # Assume UTC and convert to ET
                            et_tz = pytz.timezone('US/Eastern')
                            current_time_et = pytz.utc.localize(current_time).astimezone(et_tz)
                        
                        # Check if it's a weekday and within market hours
                        if (current_time_et.weekday() >= 5 or  # Weekend
                            current_time_et.hour < 9 or  # Before 9 AM
                            (current_time_et.hour == 9 and current_time_et.minute < 30) or  # Before 9:30 AM
                            current_time_et.hour >= 16):  # After 4 PM
                            # Market is closed, skip this bar
                            return
                    except ImportError:
                        # Fallback without timezone handling
                        hour = current_time.hour
                        if (current_time.weekday() >= 5 or  # Weekend
                            hour < 9 or hour >= 16):  # Outside basic hours
                            return
                
                # Create market data object
                market_data = MarketData(
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    bid=current_price * 0.999,  # Approximate bid
                    ask=current_price * 1.001,  # Approximate ask
                    volume=int(self.data.Volume[-1]) if hasattr(self.data, 'Volume') else 1000
                )
                
                # Update risk manager with current date
                self.risk_manager.update_daily_date(current_time.date())
                
                # Process each strategy
                for strategy_type, strategy in self.strategies.items():
                    self._process_strategy(strategy_type, strategy, market_data)
                
                # Update risk manager with total unrealized PnL
                total_unrealized = sum(strategy.get_unrealized_pnl() for strategy in self.strategies.values())
                self.risk_manager.update_unrealized_pnl(total_unrealized)
            
            def _process_strategy(self, strategy_type: StrategyType, strategy, market_data: MarketData):
                """Process individual strategy logic"""
                current_price = market_data.price
                
                # Update current price for existing positions
                for pos in strategy.positions:
                    pos.current_price = current_price
                
                # Entry logic with coordination and risk management
                if strategy.should_enter_with_coordination(market_data) and not strategy.is_active:
                    # Check continue_trading setting - if False and strategy has completed at least one cycle, don't start new cycles
                    shared_settings = getattr(self.config, 'shared_settings', None)
                    if shared_settings and not shared_settings.continue_trading and strategy.total_cycles > 0:
                        self.logger.info(f"Continue trading disabled - skipping new cycle for {strategy_type.value} on {symbol}")
                        return
                    
                    # Check risk management before starting new cycle
                    can_start, reason = self.risk_manager.can_start_new_cycle(strategy_type.value)
                    if not can_start:
                        self.logger.warning(f"Cannot start new cycle for {strategy_type.value}: {reason}")
                        return
                    
                    # Start new cycle
                    cycle_id = f"{strategy_type.value}_{symbol}_{market_data.timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    cycle = self.cycle_analyzer.start_cycle(cycle_id, strategy_type.value, symbol, market_data.timestamp)
                    self.active_cycles[strategy_type] = cycle_id
                    
                    # Register with risk manager
                    self.risk_manager.register_cycle_start(cycle_id, strategy_type.value)
                    
                    strategy.start_cycle(market_data)
                    
                    # Calculate position size
                    available_cash = self.strategy_cash[strategy_type]
                    position_size = strategy.calculate_position_size(
                        leg_number=0,
                        account_balance=available_cash,
                        current_price=current_price
                    )
                    
                    if position_size > 0 and available_cash >= position_size * current_price:
                        # Determine trade type based on initial_trade_type setting
                        strategy_settings = self.config.get_strategy_settings(strategy_type)
                        
                        is_sell_entry = (hasattr(strategy_settings, 'initial_trade_type') and 
                                       strategy_settings.initial_trade_type == "SELL")
                        
                        trade_type = TradeType.SELL if is_sell_entry else TradeType.BUY
                        trade_action = "SELL" if is_sell_entry else "BUY"
                        
                        # Execute order
                        cost = position_size * current_price
                        self.strategy_cash[strategy_type] -= cost
                        self.logger.info(f"ENTRY TRADE: {strategy_type.value} ({trade_action}) - Cost: ${cost:.2f}, Remaining cash: ${self.strategy_cash[strategy_type]:.2f}")
                        
                        # Create trade record
                        trade = Trade(
                            trade_id=f"{cycle_id}_trade_{len(strategy.positions) + 1}",
                            timestamp=market_data.timestamp,
                            symbol=symbol,
                            trade_type=trade_type,
                            quantity=position_size,
                            price=current_price,
                            order_level=strategy.current_leg + 1,
                            strategy_type=strategy_type.value,
                            commission=cost * 0.002  # 0.2% commission
                        )
                        
                        # Add trade to cycle
                        self.cycle_analyzer.add_trade_to_cycle(cycle_id, trade)
                        
                        # Register trade with risk manager
                        self.risk_manager.register_trade(cost, trade.commission)
                        
                        # Add position to strategy
                        position = Position(
                            symbol=market_data.symbol,
                            quantity=position_size if not is_sell_entry else -position_size,  # Negative for short positions
                            avg_price=current_price,
                            current_price=current_price,
                            strategy_id=strategy_type.value,
                            leg_number=strategy.current_leg,
                            entry_time=market_data.timestamp
                        )
                        strategy.positions.append(position)
                        strategy.current_leg += 1
                        
                        # Place order in backtesting framework
                        # Get order type from shared settings
                        shared_settings = getattr(self.config, 'shared_settings', None)
                        order_type = getattr(shared_settings, 'order_type', 'MARKET') if shared_settings else 'MARKET'
                        
                        if order_type == 'LIMIT':
                            # For limit orders, use current price as limit price
                            if is_sell_entry:
                                self.sell(size=position_size, limit=current_price)
                            else:
                                self.buy(size=position_size, limit=current_price)
                        else:
                            # Market orders (default behavior)
                            if is_sell_entry:
                                self.sell(size=position_size)
                            else:
                                self.buy(size=position_size)
                    elif position_size > 0:
                        required_cash = position_size * current_price
                        self.logger.warning(f"ENTRY SKIPPED: {strategy_type.value} - Need: ${required_cash:.2f}, Available: ${available_cash:.2f}, Shortfall: ${required_cash - available_cash:.2f}")
                        return  # Skip the rest of the entry logic
                
                # Add leg logic
                elif strategy.should_add_leg(market_data) and strategy.is_active:
                    # Check if trading is halted (but don't check concurrent cycle limit for existing cycles)
                    if self.risk_manager.trading_halted:
                        self.logger.warning(f"Cannot add leg for {strategy_type.value}: {self.risk_manager.halt_reason}")
                        return
                    
                    available_cash = self.strategy_cash[strategy_type]
                    position_size = strategy.calculate_position_size(
                        leg_number=strategy.current_leg,
                        account_balance=available_cash,
                        current_price=current_price
                    )
                    
                    if position_size > 0 and available_cash >= position_size * current_price:
                        # Determine trade type based on initial_trade_type setting (same as initial trade)
                        strategy_settings = self.config.get_strategy_settings(strategy_type)
                        
                        is_sell_entry = (hasattr(strategy_settings, 'initial_trade_type') and 
                                       strategy_settings.initial_trade_type == "SELL")
                        
                        trade_type = TradeType.SELL if is_sell_entry else TradeType.BUY
                        trade_action = "SELL" if is_sell_entry else "BUY"
                        
                        cost = position_size * current_price
                        self.strategy_cash[strategy_type] -= cost
                        self.logger.info(f"LEG TRADE: {strategy_type.value} ({trade_action}) - Cost: ${cost:.2f}, Remaining cash: ${self.strategy_cash[strategy_type]:.2f}")
                        
                        # Create trade record for additional leg
                        cycle_id = self.active_cycles[strategy_type]
                        
                        # Register trade with risk manager
                        self.risk_manager.register_trade(cost, cost * 0.002)
                        
                        if cycle_id:
                            trade = Trade(
                                trade_id=f"{cycle_id}_trade_{len(strategy.positions) + 1}",
                                timestamp=market_data.timestamp,
                                symbol=symbol,
                                trade_type=trade_type,
                                quantity=position_size,
                                price=current_price,
                                order_level=strategy.current_leg + 1,
                                strategy_type=strategy_type.value,
                                commission=cost * 0.002  # 0.2% commission
                            )
                            
                            # Add trade to cycle
                            self.cycle_analyzer.add_trade_to_cycle(cycle_id, trade)
                        
                        # Add position to strategy
                        position = Position(
                            symbol=market_data.symbol,
                            quantity=position_size if not is_sell_entry else -position_size,  # Negative for short positions
                            avg_price=current_price,
                            current_price=current_price,
                            strategy_id=strategy_type.value,
                            leg_number=strategy.current_leg,
                            entry_time=market_data.timestamp
                        )
                        strategy.positions.append(position)
                        strategy.current_leg += 1
                        
                        # Place order in backtesting framework
                        # Get order type from shared settings
                        shared_settings = getattr(self.config, 'shared_settings', None)
                        order_type = getattr(shared_settings, 'order_type', 'MARKET') if shared_settings else 'MARKET'
                        
                        if order_type == 'LIMIT':
                            # For limit orders, use current price as limit price
                            if is_sell_entry:
                                self.sell(size=position_size, limit=current_price)
                            else:
                                self.buy(size=position_size, limit=current_price)
                        else:
                            # Market orders (default behavior)
                            if is_sell_entry:
                                self.sell(size=position_size)
                            else:
                                self.buy(size=position_size)
                    elif position_size > 0:
                        required_cash = position_size * current_price
                        self.logger.warning(f"LEG SKIPPED: {strategy_type.value} - Need: ${required_cash:.2f}, Available: ${available_cash:.2f}, Shortfall: ${required_cash - available_cash:.2f}")
                        return  # Skip the rest of the leg logic
                
                # Exit logic
                elif strategy.should_exit(market_data) and strategy.is_active:
                    total_quantity = sum(pos.quantity for pos in strategy.positions)
                    abs_total_quantity = abs(total_quantity)
                    
                    if abs_total_quantity > 0:
                        # Get strategy settings to check hold_previous
                        strategy_settings = self.config.get_strategy_settings(strategy_type)
                        hold_previous = getattr(strategy_settings, 'hold_previous', True)
                        
                        # Determine if we have long or short positions
                        is_short_position = total_quantity < 0
                        
                        cycle_id = self.active_cycles[strategy_type]
                        total_profit = 0
                        
                        if hold_previous:
                            # Close all positions simultaneously with a single order
                            # Calculate profit/loss
                            total_cost = sum(pos.quantity * pos.avg_price for pos in strategy.positions)
                            if is_short_position:
                                # For short positions: profit = entry_value - current_value
                                total_value = abs_total_quantity * current_price
                                profit = abs(total_cost) - total_value
                            else:
                                # For long positions: profit = current_value - entry_cost
                                total_value = total_quantity * current_price
                                profit = total_value - total_cost
                            
                            total_profit = profit
                            
                            # Determine exit trade type (opposite of entry)
                            exit_trade_type = TradeType.BUY if is_short_position else TradeType.SELL
                            exit_action = "BUY" if is_short_position else "SELL"
                            
                            # Create exit trade record
                            if cycle_id:
                                exit_trade = Trade(
                                    trade_id=f"{cycle_id}_exit_trade",
                                    timestamp=market_data.timestamp,
                                    symbol=symbol,
                                    trade_type=exit_trade_type,
                                    quantity=abs_total_quantity,
                                    price=current_price,
                                    order_level=0,  # Exit trade
                                    strategy_type=strategy_type.value,
                                    commission=abs_total_quantity * current_price * 0.002  # 0.2% commission
                                )
                                
                                # Add trade to cycle
                                self.cycle_analyzer.add_trade_to_cycle(cycle_id, exit_trade)
                            
                            # Update strategy cash
                            if is_short_position:
                                # For short positions, we get back the original short sale proceeds plus/minus profit
                                self.strategy_cash[strategy_type] += abs(total_cost) + profit
                            else:
                                # For long positions, we get the current market value
                                self.strategy_cash[strategy_type] += total_value
                            
                            # Close all positions
                            # Get order type from shared settings
                            shared_settings = getattr(self.config, 'shared_settings', None)
                            order_type = getattr(shared_settings, 'order_type', 'MARKET') if shared_settings else 'MARKET'
                            
                            if order_type == 'LIMIT':
                                # For limit orders, use current price as limit price
                                if is_short_position:
                                    self.buy(size=abs_total_quantity, limit=current_price)
                                else:
                                    self.sell(size=abs_total_quantity, limit=current_price)
                            else:
                                # Market orders (default behavior)
                                if is_short_position:
                                    self.buy(size=abs_total_quantity)
                                else:
                                    self.sell(size=abs_total_quantity)
                            
                            self.logger.info(f"EXIT TRADE: {strategy_type.value} (hold_previous=True, {exit_action}) - Profit: ${profit:.2f}, New cash: ${self.strategy_cash[strategy_type]:.2f}")
                        
                        else:
                            # Close each position individually
                            for i, pos in enumerate(strategy.positions):
                                pos_quantity = pos.quantity
                                pos_avg_price = pos.avg_price
                                pos_abs_quantity = abs(pos_quantity)
                                pos_is_short = pos_quantity < 0
                                
                                # Calculate profit/loss for this position
                                if pos_is_short:
                                    # For short positions: profit = entry_value - current_value
                                    pos_profit = (pos_avg_price - current_price) * pos_abs_quantity
                                else:
                                    # For long positions: profit = current_value - entry_cost
                                    pos_profit = (current_price - pos_avg_price) * pos_abs_quantity
                                
                                total_profit += pos_profit
                                
                                # Determine exit trade type (opposite of position)
                                exit_trade_type = TradeType.BUY if pos_is_short else TradeType.SELL
                                exit_action = "BUY" if pos_is_short else "SELL"
                                
                                # Create exit trade record for each position
                                if cycle_id:
                                    exit_trade = Trade(
                                        trade_id=f"{cycle_id}_exit_trade_{i+1}",
                                        timestamp=market_data.timestamp,
                                        symbol=symbol,
                                        trade_type=exit_trade_type,
                                        quantity=pos_abs_quantity,
                                        price=current_price,
                                        order_level=pos.leg_number,
                                        strategy_type=strategy_type.value,
                                        commission=pos_abs_quantity * current_price * 0.002  # 0.2% commission
                                    )
                                    
                                    # Add trade to cycle
                                    self.cycle_analyzer.add_trade_to_cycle(cycle_id, exit_trade)
                                
                                # Update strategy cash for this position
                                if pos_is_short:
                                    # For short positions, we get back the original short sale proceeds plus/minus profit
                                    self.strategy_cash[strategy_type] += (pos_avg_price * pos_abs_quantity) + pos_profit
                                else:
                                    # For long positions, we get the current market value
                                    self.strategy_cash[strategy_type] += pos_abs_quantity * current_price
                                
                                # Place individual exit order
                                # Get order type from shared settings
                                shared_settings = getattr(self.config, 'shared_settings', None)
                                order_type = getattr(shared_settings, 'order_type', 'MARKET') if shared_settings else 'MARKET'
                                
                                if order_type == 'LIMIT':
                                    # For limit orders, use current price as limit price
                                    if pos_is_short:
                                        self.buy(size=pos_abs_quantity, limit=current_price)
                                    else:
                                        self.sell(size=pos_abs_quantity, limit=current_price)
                                else:
                                    # Market orders (default behavior)
                                    if pos_is_short:
                                        self.buy(size=pos_abs_quantity)
                                    else:
                                        self.sell(size=pos_abs_quantity)
                                
                                self.logger.info(f"EXIT TRADE: {strategy_type.value} (hold_previous=False, Position {i+1}, {exit_action}) - Profit: ${pos_profit:.2f}")
                            
                            self.logger.info(f"EXIT COMPLETE: {strategy_type.value} - Total Profit: ${total_profit:.2f}, New cash: ${self.strategy_cash[strategy_type]:.2f}")
                        
                        # Complete the cycle
                        if cycle_id:
                            completed_cycle = self.cycle_analyzer.complete_cycle(cycle_id, market_data.timestamp, total_profit)
                            self.active_cycles[strategy_type] = None
                            
                            # Register cycle completion with risk manager
                            if completed_cycle:
                                self.risk_manager.register_cycle_end(cycle_id, completed_cycle.realized_pnl)
                        
                        # Update strategy statistics
                        strategy.total_cycles += 1
                        strategy.total_profit += total_profit
                        if total_profit > 0:
                            strategy.winning_cycles += 1
                        
                        # Reset strategy state
                        strategy.positions.clear()
                        strategy.current_leg = 0
                        strategy.is_active = False
                        strategy.entry_price = None
                        
                        # Check for auto-restart cycles if enabled
                        shared_settings = getattr(self.config, 'shared_settings', None)
                        if shared_settings and shared_settings.repeat_on_close and shared_settings.auto_restart_cycles:
                            # Allow immediate restart by not blocking further entries
                            self.logger.info(f"Auto-restart enabled for {strategy_type.value}, cycle completed and ready for new entry")
                        elif shared_settings and not shared_settings.repeat_on_close:
                            # If repeat_on_close is disabled, prevent further entries for this strategy
                            self.logger.info(f"Repeat on close disabled for {strategy_type.value}, strategy will not restart after cycle completion")
        
        # Set class attributes
        CombinedMartingaleStrategy.config = self.config
        CombinedMartingaleStrategy.selected_strategies = self.selected_strategies
        
        return CombinedMartingaleStrategy
    
    def run_backtest(self, symbol: str, start_date: str, end_date: str, 
                    interval: str = '1h', initial_cash: float = 100000) -> Tuple[object, Dict, CycleAnalysisReport]:
        """Run backtest and return results with cycle analysis"""
        try:
            # Reset cycle analyzer for new backtest
            self.cycle_analyzer.reset_analysis()
            
            # Update risk manager with backtest start date to avoid using today's date
            from datetime import datetime
            backtest_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            self.risk_manager.current_date = backtest_start_date
            self.risk_manager._ensure_daily_metrics(backtest_start_date)
            
            # Fetch data
            data = self.fetch_data(symbol, start_date, end_date, interval)
            
            # Create strategy class
            StrategyClass = self.create_combined_strategy(symbol)
            
            # Run backtest
            bt = Backtest(
                data,
                StrategyClass,
                cash=initial_cash,
                commission=0.002,  # 0.2% commission
                exclusive_orders=True
            )
            
            results = bt.run()
            
            # Extract key metrics
            metrics = {
                'Start': results['Start'],
                'End': results['End'],
                'Duration': results['Duration'],
                'Exposure Time [%]': results['Exposure Time [%]'],
                'Equity Final [$]': results['Equity Final [$]'],
                'Equity Peak [$]': results['Equity Peak [$]'],
                'Return [%]': results['Return [%]'],
                'Buy & Hold Return [%]': results['Buy & Hold Return [%]'],
                'Return (Ann.) [%]': results['Return (Ann.) [%]'],
                'Volatility (Ann.) [%]': results['Volatility (Ann.) [%]'],
                'Sharpe Ratio': results['Sharpe Ratio'],
                'Sortino Ratio': results['Sortino Ratio'],
                'Calmar Ratio': results['Calmar Ratio'],
                'Max. Drawdown [%]': results['Max. Drawdown [%]'],
                'Avg. Drawdown [%]': results['Avg. Drawdown [%]'],
                'Max. Drawdown Duration': results['Max. Drawdown Duration'],
                'Avg. Drawdown Duration': results['Avg. Drawdown Duration'],
                '# Trades': results['# Trades'],
                'Win Rate [%]': results['Win Rate [%]'],
                'Best Trade [%]': results['Best Trade [%]'],
                'Worst Trade [%]': results['Worst Trade [%]'],
                'Avg. Trade [%]': results['Avg. Trade [%]'],
                'Max. Trade Duration': results['Max. Trade Duration'],
                'Avg. Trade Duration': results['Avg. Trade Duration'],
                'Profit Factor': results['Profit Factor'],
                'Expectancy [%]': results['Expectancy [%]'],
                'SQN': results['SQN']
            }
            
            # Get cycle analysis report
            cycle_report = self.cycle_analyzer.get_analysis_report()
            cycle_report.analysis_period_start = datetime.strptime(start_date, '%Y-%m-%d')
            cycle_report.analysis_period_end = datetime.strptime(end_date, '%Y-%m-%d')
            
            return bt, metrics, cycle_report
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}")
            raise
    
    def generate_cycle_focused_report(self, cycle_report: CycleAnalysisReport, symbol: str, risk_summary: Dict = None) -> Dict:
        """Generate comprehensive cycle-focused backtest report"""
        try:
            # Cycle Overview
            cycle_overview = {
                'total_cycles': cycle_report.total_cycles,
                'completed_cycles': cycle_report.completed_cycles,
                'active_cycles': cycle_report.total_cycles - cycle_report.completed_cycles,
                'winning_cycles': cycle_report.winning_cycles,
                'losing_cycles': cycle_report.losing_cycles,
                'win_rate': (cycle_report.winning_cycles / cycle_report.completed_cycles * 100) if cycle_report.completed_cycles > 0 else 0,
                'analysis_period': f"{cycle_report.analysis_period_start} to {cycle_report.analysis_period_end}",
                'symbol': symbol
            }
            
            # Cycle Metrics Summary
            cycle_metrics = {
                'total_realized_pnl': cycle_report.total_realized_pnl,
                'total_unrealized_pnl': cycle_report.total_unrealized_pnl,
                'average_cycle_pnl': cycle_report.average_cycle_pnl,
                'best_cycle_pnl': cycle_report.best_cycle_pnl,
                'worst_cycle_pnl': cycle_report.worst_cycle_pnl,
                'total_net_pnl': cycle_report.total_realized_pnl + cycle_report.total_unrealized_pnl
            }
            
            # Evaluation Ratios
            evaluation_ratios = {
                'risk_reward_ratio': cycle_report.cycles[0].risk_reward_ratio if cycle_report.cycles else 0,
                'profit_factor': cycle_report.overall_profit_factor,
                'sharpe_ratio': cycle_report.overall_sharpe_ratio,
                'sortino_ratio': cycle_report.overall_sortino_ratio,
                'calmar_ratio': cycle_report.overall_calmar_ratio,
                'maximum_drawdown_ratio': cycle_report.maximum_drawdown_ratio,
                'order_completion_efficiency': cycle_report.order_completion_efficiency,
                'return_on_equity': cycle_report.return_on_equity,
                'average_utilization_ratio': cycle_report.average_utilization_ratio,
                'time_weighted_return': cycle_report.time_weighted_return,
                'internal_rate_of_return': cycle_report.internal_rate_of_return,
                'maximum_daily_drawdown': cycle_report.maximum_daily_drawdown,
                'recovery_factor': cycle_report.recovery_factor,
                'compound_equivalent_rate': cycle_report.compound_equivalent_rate
            }
            
            # Detailed Cycle Analysis
            cycle_summary_stats = cycle_report.get_cycle_summary_stats()
            strategy_breakdown = cycle_report.get_strategy_breakdown()
            
            # Trade Log (DataFrame)
            trades_df = cycle_report.export_trades_to_dataframe()
            cycles_df = cycle_report.export_to_dataframe()
            
            # Aggregated Cycle Trade Data
            aggregated_data = {
                'total_trades': len(trades_df) if not trades_df.empty else 0,
                'total_buy_trades': len(trades_df[trades_df['trade_type'] == 'BUY']) if not trades_df.empty else 0,
                'total_sell_trades': len(trades_df[trades_df['trade_type'] == 'SELL']) if not trades_df.empty else 0,
                'average_trade_size': trades_df['quantity'].mean() if not trades_df.empty else 0,
                'total_volume': trades_df['quantity'].sum() if not trades_df.empty else 0,
                'total_commission': trades_df['commission'].sum() if not trades_df.empty else 0,
                'average_order_level': trades_df['order_level'].mean() if not trades_df.empty else 0,
                'max_order_level_reached': trades_df['order_level'].max() if not trades_df.empty else 0
            }
            
            # Risk Management Summary
            risk_management_summary = {}
            if risk_summary:
                daily_metrics = risk_summary.get('daily_metrics', {})
                limits = risk_summary.get('limits', {})
                status = risk_summary.get('status', {})
                
                risk_management_summary = {
                    'daily_realized_pnl': daily_metrics.get('daily_realized_pnl', 0),
                    'daily_unrealized_pnl': daily_metrics.get('daily_unrealized_pnl', 0),
                    'total_daily_pnl': daily_metrics.get('total_daily_pnl', 0),
                    'active_cycles': daily_metrics.get('active_cycles', 0),
                    'total_trades_today': daily_metrics.get('total_trades_today', 0),
                    'total_commission_today': daily_metrics.get('total_commission_today', 0),
                    'daily_loss_limit': limits.get('daily_loss_limit', 0),
                    'daily_profit_target': limits.get('daily_profit_target', 0),
                    'max_concurrent_cycles': limits.get('max_concurrent_cycles', 0),
                    'risk_level': status.get('risk_level', 'UNKNOWN'),
                    'can_start_new_cycle': status.get('can_start_new_cycle', False),
                    'warnings': status.get('warnings', [])
                }
            
            return {
                'cycle_overview': cycle_overview,
                'cycle_metrics': cycle_metrics,
                'evaluation_ratios': evaluation_ratios,
                'cycle_summary_stats': cycle_summary_stats,
                'strategy_breakdown': strategy_breakdown,
                'aggregated_data': aggregated_data,
                'risk_management_summary': risk_management_summary,
                'trades_dataframe': trades_df,
                'cycles_dataframe': cycles_df
            }
            
        except Exception as e:
            self.logger.error(f"Error generating cycle-focused report: {str(e)}")
            return {}
    
    def export_cycle_analysis_to_excel(self, cycle_report: CycleAnalysisReport, risk_summary: Dict = None, filename: str = None) -> str:
        """Export cycle analysis to Excel file with multiple sheets"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"cycle_analysis_{timestamp}.xlsx"
            
            # Generate comprehensive report data
            report_data = self.generate_cycle_focused_report(cycle_report, "BACKTEST", risk_summary)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Export cycles data
                cycles_df = cycle_report.export_to_dataframe()
                if not cycles_df.empty:
                    cycles_df.to_excel(writer, sheet_name='Cycles', index=False)
                
                # Export trades data
                trades_df = cycle_report.export_trades_to_dataframe()
                if not trades_df.empty:
                    trades_df.to_excel(writer, sheet_name='Trades', index=False)
                
                # Export summary statistics
                summary_stats = cycle_report.get_cycle_summary_stats()
                if summary_stats:
                    summary_df = pd.DataFrame([summary_stats])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Export strategy breakdown
                strategy_breakdown = cycle_report.get_strategy_breakdown()
                if strategy_breakdown:
                    strategy_df = pd.DataFrame(strategy_breakdown).T
                    strategy_df.to_excel(writer, sheet_name='Strategy_Breakdown', index=True)
                
                # Export risk management summary
                if report_data.get('risk_management_summary'):
                    risk_df = pd.DataFrame([report_data['risk_management_summary']])
                    risk_df.to_excel(writer, sheet_name='Risk_Management', index=False)
            
            self.logger.info(f"Cycle analysis exported to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting cycle analysis to Excel: {str(e)}")
            raise
    
    def plot_results(self, bt: object, resample: bool = True) -> object:
        """Generate backtest plot with fallback options"""
        try:
            # First try with resampling
            if resample:
                return bt.plot(resample=True)
            else:
                return bt.plot(resample=False)
        except Exception as e:
            self.logger.error(f"Error plotting results with resample={resample}: {str(e)}")
            if resample:
                # Try without resampling as fallback
                try:
                    self.logger.info("Retrying plot without resampling...")
                    return bt.plot(resample=False)
                except Exception as e2:
                    self.logger.error(f"Error plotting results without resampling: {str(e2)}")
                    raise Exception(f"Plot generation failed: {str(e)}. Fallback also failed: {str(e2)}")
            else:
                raise