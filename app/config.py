"""Configuration module for Multi-Martingales Trading Bot"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from enum import Enum

class AccountType(Enum):
    DEMO = "demo"
    LIVE = "live"

class StrategyType(Enum):
    CDM = "cdm"  # Counter Direction Martingale
    WDM = "wdm"  # With Direction Martingale
    ZRM = "zrm"  # Zone Recovery Martingale
    IZRM = "izrm"  # Inverse Zone Recovery Martingale

class ExecutionMode(Enum):
    SINGLE = "single"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"

@dataclass
class IBConfig:
    """Interactive Brokers connection configuration"""
    host: str = "127.0.0.1"
    demo_port: int = 4002  # IB Gateway paper trading (newer versions)
    live_port: int = 4001  # IB Gateway live trading
    client_id: int = 1
    timeout: int = 30
    
    def get_port(self, account_type: AccountType) -> int:
        return self.demo_port if account_type == AccountType.DEMO else self.live_port

@dataclass
class SharedSettings:
    """Comprehensive shared settings across all strategies"""
    
    # === GLOBAL STRATEGY COORDINATION ===
    # Strategy alignment and execution mode
    global_strategy_alignment: str = "PARALLEL"  # PARALLEL or SEQUENTIAL
    global_parallel_start_mode: bool = False
    global_strategy_to_start_with: str = "CDM"  # CDM, WDM, ZRM, IZRM
    global_order_number_to_start: int = 1
    global_sequential_mode_strategy: str = "CDM"  # CDM, WDM, ZRM, IZRM
    
    # Multi-strategy coordination
    enable_strategy_coordination: bool = True
    max_concurrent_strategies: int = 4
    strategy_priority_order: List[str] = field(default_factory=lambda: ["CDM", "WDM", "ZRM", "IZRM"])
    
    # === GLOBAL POSITION SIZING ===
    # Position sizing configuration
    global_position_size_unit: str = "SHARES"  # SHARES, USD, PERCENTAGE
    global_fixed_position_size: float = 100.0
    global_percentage_of_portfolio: float = 5.0  # 5% of total portfolio
    
    # Dynamic position sizing
    enable_dynamic_sizing: bool = False
    min_position_size: float = 50.0
    max_position_size: float = 1000.0
    size_increment_factor: float = 1.2  # Multiplier for increasing position sizes
    
    # Portfolio-based sizing
    enable_portfolio_targeting: bool = False
    target_portfolio_percentage: float = 10.0  # Target % of portfolio per symbol
    allow_fractional_shares: bool = True
    
    # === GLOBAL RISK MANAGEMENT ===
    # Concurrent trading limits
    global_max_concurrent_cycles: int = 300000000
    max_concurrent_symbols: int = 500000
    max_orders_per_symbol: int = 50000000
    
    # Daily limits
    global_daily_loss_limit: float = 100000000000000.0  # USD
    global_daily_profit_target: float = 20000000000000000000.0  # USD
    enable_daily_limits: bool = False
    
    # Drawdown protection
    max_portfolio_drawdown_pct: float = 100.0  # 100% max drawdown
    enable_drawdown_protection: bool = False
    
    # === GLOBAL TRADING SETTINGS ===
    # Trading hours and market conditions
    continue_trading: bool = True
    pre_after_hours: bool = False
    enable_market_hours_only: bool = True
    
    # Order management
    order_type: str = "MARKET"  # MARKET or LIMIT
    default_order_timeout: int = 300  # 5 minutes
    enable_order_retry: bool = True
    max_order_retries: int = 3
    
    # === GLOBAL CYCLE MANAGEMENT ===
    # Cycle behavior
    repeat_on_close: bool = True
    auto_restart_cycles: bool = True
    cycle_cooldown_minutes: int = 5
    
    # Cycle limits
    max_cycles_per_day: int = 100000000
    max_cycle_duration_hours: int = 24
    
    # === GLOBAL MONEY MANAGEMENT ===
    # Portfolio growth settings
    money_management: bool = False
    growth_threshold: float = 10000.0
    increase_value: float = 0.1  # 10%
    progressive_reinvestment_step: float = 0.05  # 5%
    
    # Capital allocation
    total_capital_allocation: float = 1.0  # 100% of available capital
    reserve_capital_percentage: float = 0.1  # 10% reserve
    
    # === GLOBAL PERFORMANCE SETTINGS ===
    # Reporting and analysis
    backtest_performance_report: bool = True
    enable_real_time_analytics: bool = True
    performance_update_interval: int = 60  # seconds
    
    # Account settings
    initial_balance: float = 50000.0  # Starting account balance for P&L calculation
    
    # === GLOBAL TRAILING STOPS ===
    # Global trailing stop settings
    enable_global_trailing_stops: bool = False
    global_trailing_trigger_pct: float = 5.0  # Profit % to trigger trailing
    global_trailing_distance_pct: float = 1.0  # Trailing stop distance %
    
    # === GLOBAL EXIT CONDITIONS ===
    # Emergency exit conditions
    enable_emergency_exit: bool = True
    emergency_loss_threshold: float = 5000.0  # USD
    emergency_drawdown_threshold: float = 15.0  # %
    
    # Time-based exits
    enable_time_based_exit: bool = False
    max_trade_duration_hours: int = 48
    
    # === GLOBAL NOTIFICATIONS ===
    # Alert settings
    enable_notifications: bool = False
    notification_profit_threshold: float = 1000.0
    notification_loss_threshold: float = 500.0
    
    def validate_settings(self) -> List[str]:
        """Validate shared settings and return list of validation errors"""
        errors = []
         
        # Validate position sizing
        if self.global_position_size_unit not in ["SHARES", "USD", "PERCENTAGE"]:
            errors.append("global_position_size_unit must be SHARES, USD, or PERCENTAGE")
        
        if self.global_fixed_position_size < 0:
            errors.append("global_fixed_position_size must be non-negative (0.0 or positive)")
        
        if self.global_percentage_of_portfolio <= 0 or self.global_percentage_of_portfolio > 100:
            errors.append("global_percentage_of_portfolio must be between 0 and 100")
         
        # Validate risk management
        if self.global_max_concurrent_cycles <= 0:
            errors.append("global_max_concurrent_cycles must be positive")
        
        if self.max_concurrent_symbols <= 0:
            errors.append("max_concurrent_symbols must be positive")
        
        if self.max_orders_per_symbol <= 0 or self.max_orders_per_symbol > 50000:
            errors.append("max_orders_per_symbol must be between 1 and 50000")
        
        # Validate daily limits
        if self.global_daily_loss_limit <= 0:
            errors.append("global_daily_loss_limit must be positive")
        
        if self.global_daily_profit_target <= 0:
            errors.append("global_daily_profit_target must be positive")
        
        # Validate drawdown protection
        if self.max_portfolio_drawdown_pct <= 0 or self.max_portfolio_drawdown_pct > 100:
            errors.append("max_portfolio_drawdown_pct must be between 0 and 100")
        
        # Validate strategy coordination
        if self.global_strategy_alignment not in ["PARALLEL", "SEQUENTIAL"]:
            errors.append("global_strategy_alignment must be PARALLEL or SEQUENTIAL")
        
        valid_strategies = ["CDM", "WDM", "ZRM", "IZRM"]
        if self.global_strategy_to_start_with not in valid_strategies:
            errors.append(f"global_strategy_to_start_with must be one of {valid_strategies}")
        
        if self.global_sequential_mode_strategy not in valid_strategies:
            errors.append(f"global_sequential_mode_strategy must be one of {valid_strategies}")
        
        # Validate order management
        if self.order_type not in ["MARKET", "LIMIT"]:
            errors.append("order_type must be MARKET or LIMIT")
        
        if self.default_order_timeout <= 0:
            errors.append("default_order_timeout must be positive")
        
        # Validate dynamic sizing
        if self.enable_dynamic_sizing:
            if self.min_position_size <= 0:
                errors.append("min_position_size must be positive when dynamic sizing is enabled")
            if self.max_position_size <= self.min_position_size:
                errors.append("max_position_size must be greater than min_position_size")
            if self.size_increment_factor <= 1.0:
                errors.append("size_increment_factor must be greater than 1.0")
        
        # Validate trailing stops
        if self.enable_global_trailing_stops:
            if self.global_trailing_trigger_pct <= 0:
                errors.append("global_trailing_trigger_pct must be positive")
            if self.global_trailing_distance_pct <= 0:
                errors.append("global_trailing_distance_pct must be positive")
        
        return errors
     
    def get_effective_position_size(self, account_balance: float, symbol_price: float) -> float:
        """Calculate effective position size based on current settings"""
        if self.global_position_size_unit == "SHARES":
            if self.global_fixed_position_size == 0.0:
                # Fixed Position Size is 0.0 - use percentage-based sizing
                usd_amount = account_balance * (self.global_percentage_of_portfolio / 100)
                return usd_amount / symbol_price if symbol_price > 0 else 0
            return self.global_fixed_position_size
        elif self.global_position_size_unit == "USD":
            if self.global_fixed_position_size == 0.0:
                # Fixed Position Size is 0.0 - use percentage-based sizing
                usd_amount = account_balance * (self.global_percentage_of_portfolio / 100)
                return usd_amount / symbol_price if symbol_price > 0 else 0
            return self.global_fixed_position_size / symbol_price if symbol_price > 0 else 0
        elif self.global_position_size_unit == "PERCENTAGE":
            usd_amount = account_balance * (self.global_percentage_of_portfolio / 100)
            return usd_amount / symbol_price if symbol_price > 0 else 0
        else:
            if self.global_fixed_position_size == 0.0:
                # Fixed Position Size is 0.0 - use percentage-based sizing
                usd_amount = account_balance * (self.global_percentage_of_portfolio / 100)
                return usd_amount / symbol_price if symbol_price > 0 else 0
            return self.global_fixed_position_size
    
    def is_within_risk_limits(self, current_loss: float, current_drawdown_pct: float) -> bool:
        """Check if current trading is within risk limits"""
        if self.enable_daily_limits and current_loss >= self.global_daily_loss_limit:
            return False
        
        if self.enable_drawdown_protection and current_drawdown_pct >= self.max_portfolio_drawdown_pct:
            return False
        
        return True
    
    def should_trigger_emergency_exit(self, current_loss: float, current_drawdown_pct: float) -> bool:
        """Check if emergency exit conditions are met"""
        if not self.enable_emergency_exit:
            return False
        
        if current_loss >= self.emergency_loss_threshold:
            return True
        
        if current_drawdown_pct >= self.emergency_drawdown_threshold:
            return True
        
        return False
    
    def get_strategy_priority_index(self, strategy: str) -> int:
        """Get priority index for a strategy (lower index = higher priority)"""
        try:
            return self.strategy_priority_order.index(strategy)
        except ValueError:
            return len(self.strategy_priority_order)  # Lowest priority for unknown strategies

@dataclass
class StrategySettings:
    """Base strategy settings"""
    enabled: bool = False
    capital_allocation: float = 0.25  # 25% of account
    initial_trade_type: str = "BUY"  # BUY or SELL
    symbol: str = "AAPL"
    price_trigger: Optional[float] = None
    max_orders: int = 5
    hold_previous: bool = True
    
    # Strategy alignment settings
    other_strategies_entry_index: bool = False
    strategy_alignment: str = "PARALLEL"  # PARALLEL or SEQUENTIAL
    parallel_start_mode: bool = False
    strategy_to_start_with: str = "CDM"  # CDM, WDM, ZRM, IZRM
    order_number_to_start: int = 1
    sequential_mode_strategy: str = "CDM"  # CDM, WDM, ZRM, IZRM
    
    # Order configuration (up to 50 legs)
    order_distances: List[float] = field(default_factory=lambda: [1.0, 1.5, 2.0, 2.5, 3.0] + [3.0] * 45)
    order_sizes: List[float] = field(default_factory=lambda: [1.0, 1.5, 2.0, 2.5, 3.0] + [3.0] * 45)
    
    # Position sizing options
    position_size_unit: str = "SHARES"  # SHARES or USD
    fixed_position_size: float = 100.0  # Fixed size when not using percentage
    
@dataclass
class CDMSettings(StrategySettings):
    """Counter Direction Martingale settings"""
    order_tps: List[float] = field(default_factory=lambda: [2.0, 2.0, 2.0, 2.0, 2.0] + [2.0] * 45)  # Take profit % for 50 legs
    trailing_stops: bool = False
    trailing_trigger_pct: List[float] = field(default_factory=lambda: [5.0, 5.0, 5.0, 5.0, 5.0] + [5.0] * 45)  # Profit % to trigger trailing
    trailing_distance_pct: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 1.0] + [1.0] * 45)  # Trailing stop distance %
    # Legacy fields for backward compatibility
    first_distance_trailing: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 1.0] + [1.0] * 45)
    trailing_progress: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5, 0.5] + [0.5] * 45)

@dataclass
class WDMSettings(StrategySettings):
    """With Direction Martingale settings"""
    order_sls: List[float] = field(default_factory=lambda: [2.0, 2.0, 2.0, 2.0, 2.0] + [2.0] * 45)  # Stop loss % for 50 legs

@dataclass
class ZRMSettings(StrategySettings):
    """Zone Recovery Martingale settings"""
    zone_center_price: Optional[float] = None
    order_tps: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 1.0] + [1.0] * 45)  # Take profit % for 50 legs
    trailing_stops: bool = False
    trailing_trigger_pct: List[float] = field(default_factory=lambda: [3.0, 3.0, 3.0, 3.0, 3.0] + [3.0] * 45)  # Profit % to trigger trailing
    trailing_distance_pct: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5, 0.5] + [0.5] * 45)  # Trailing stop distance %
    # Legacy fields for backward compatibility
    first_distance_trailing: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5, 0.5] + [0.5] * 45)
    trailing_progress: List[float] = field(default_factory=lambda: [0.3, 0.3, 0.3, 0.3, 0.3] + [0.3] * 45)

@dataclass
class IZRMSettings(StrategySettings):
    """Inverse Zone Recovery Martingale settings"""
    zone_center_price: Optional[float] = None
    order_sls: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 1.0] + [1.0] * 45)  # Stop loss % for 50 legs

@dataclass
class TradingConfig:
    """Main trading configuration"""
    account_type: AccountType = AccountType.DEMO
    execution_mode: ExecutionMode = ExecutionMode.SINGLE
    active_strategies: List[StrategyType] = field(default_factory=lambda: [StrategyType.CDM])
    
    # Multi-ticker support
    tickers: List[str] = field(default_factory=lambda: ["AAPL"])
    
    # Data configuration
    timeframe: str = "1 min"  # 1 min, 5 mins, 15 mins, 30 mins, 1 hour, 2 hours, 4 hours, 1 day, 1 week, 1 month
    duration: str = "30 D"  # 30 D, 1 Y, etc.
    data_type: str = "TRADES"
    
    # Position sizing
    position_size_type: str = "PERCENTAGE"  # PERCENTAGE, LOTS, SHARES
    position_size_value: float = 5.0  # 5% of account or number of lots/shares
    
    # Configuration objects
    ib_config: IBConfig = field(default_factory=IBConfig)
    shared_settings: SharedSettings = field(default_factory=SharedSettings)
    cdm_settings: CDMSettings = field(default_factory=CDMSettings)
    wdm_settings: WDMSettings = field(default_factory=WDMSettings)
    zrm_settings: ZRMSettings = field(default_factory=ZRMSettings)
    izrm_settings: IZRMSettings = field(default_factory=IZRMSettings)
    
    def get_strategy_settings(self, strategy_type: StrategyType) -> StrategySettings:
        """Get settings for a specific strategy"""
        mapping = {
            StrategyType.CDM: self.cdm_settings,
            StrategyType.WDM: self.wdm_settings,
            StrategyType.ZRM: self.zrm_settings,
            StrategyType.IZRM: self.izrm_settings
        }
        
        # Try direct mapping first
        if strategy_type in mapping:
            return mapping[strategy_type]
        
        # Fallback: try to match by enum value
        for enum_key, settings in mapping.items():
            if enum_key.value == strategy_type.value:
                return settings
        
        # If still not found, raise a more descriptive error
        raise KeyError(f"Strategy type {strategy_type} (value: {strategy_type.value}) not found in mapping. Available: {list(mapping.keys())}")
    
    def enable_strategy(self, strategy_type: StrategyType, enabled: bool = True):
        """Enable or disable a strategy"""
        settings = self.get_strategy_settings(strategy_type)
        settings.enabled = enabled
        
        if enabled and strategy_type not in self.active_strategies:
            self.active_strategies.append(strategy_type)
        elif not enabled and strategy_type in self.active_strategies:
            self.active_strategies.remove(strategy_type)
    
    def set_ticker_for_strategy(self, strategy_type: StrategyType, ticker: str):
        """Set ticker for a specific strategy"""
        settings = self.get_strategy_settings(strategy_type)
        settings.symbol = ticker
    
    def set_all_tickers(self, ticker: str):
        """Set the same ticker for all strategies"""
        for strategy_type in StrategyType:
            self.set_ticker_for_strategy(strategy_type, ticker)
    
    def validate_configuration(self) -> List[str]:
        """Validate the entire trading configuration"""
        errors = []
        
        # Validate shared settings
        shared_errors = self.shared_settings.validate_settings()
        errors.extend([f"Shared Settings: {error}" for error in shared_errors])
        
        # Validate strategy-specific settings
        for strategy_type in self.active_strategies:
            strategy_settings = self.get_strategy_settings(strategy_type)
            if not strategy_settings.enabled:
                errors.append(f"{strategy_type.value.upper()}: Strategy is in active list but not enabled")
            
            if strategy_settings.capital_allocation <= 0 or strategy_settings.capital_allocation > 1:
                errors.append(f"{strategy_type.value.upper()}: capital_allocation must be between 0 and 1")
            
            if strategy_settings.max_orders <= 0 or strategy_settings.max_orders > 50:
                errors.append(f"{strategy_type.value.upper()}: max_orders must be between 1 and 50")
        
        # Validate total capital allocation
        total_allocation = sum(self.get_strategy_settings(st).capital_allocation for st in self.active_strategies)
        if total_allocation > 1.0:
            errors.append(f"Total capital allocation ({total_allocation:.2f}) exceeds 100%")
        
        # Validate execution mode compatibility
        if self.execution_mode == ExecutionMode.SEQUENTIAL and len(self.active_strategies) < 2:
            errors.append("Sequential mode requires at least 2 active strategies")
        
        return errors
    
    def get_effective_position_size_for_strategy(self, strategy_type: StrategyType, account_balance: float, symbol_price: float) -> float:
        """Get effective position size for a specific strategy"""
        strategy_settings = self.get_strategy_settings(strategy_type)
        
        # Use strategy-specific position sizing if available, otherwise use shared settings
        if hasattr(strategy_settings, 'position_size_unit') and strategy_settings.position_size_unit:
            if strategy_settings.position_size_unit == "SHARES":
                if strategy_settings.fixed_position_size == 0.0:
                    # Fixed Position Size is 0.0 - use percentage-based sizing with capital allocation
                    allocated_capital = account_balance * strategy_settings.capital_allocation
                    return allocated_capital / symbol_price if symbol_price > 0 else 0
                return strategy_settings.fixed_position_size
            elif strategy_settings.position_size_unit == "USD":
                if strategy_settings.fixed_position_size == 0.0:
                    # Fixed Position Size is 0.0 - use percentage-based sizing with capital allocation
                    allocated_capital = account_balance * strategy_settings.capital_allocation
                    return allocated_capital / symbol_price if symbol_price > 0 else 0
                return strategy_settings.fixed_position_size / symbol_price if symbol_price > 0 else 0
            elif strategy_settings.position_size_unit == "PERCENTAGE":
                # Use strategy's capital allocation
                allocated_capital = account_balance * strategy_settings.capital_allocation
                return allocated_capital / symbol_price if symbol_price > 0 else 0
        
        # Fall back to shared settings
        base_size = self.shared_settings.get_effective_position_size(account_balance, symbol_price)
        return base_size * strategy_settings.capital_allocation
    
    def is_strategy_coordination_enabled(self) -> bool:
        """Check if strategy coordination is enabled"""
        return (self.shared_settings.enable_strategy_coordination and 
                len(self.active_strategies) > 1)
    
    def get_next_strategy_in_sequence(self, current_strategy: StrategyType) -> Optional[StrategyType]:
        """Get the next strategy in sequential execution mode"""
        if not self.is_strategy_coordination_enabled() or self.execution_mode != ExecutionMode.SEQUENTIAL:
            return None
        
        try:
            current_index = self.active_strategies.index(current_strategy)
            next_index = (current_index + 1) % len(self.active_strategies)
            return self.active_strategies[next_index]
        except ValueError:
            return None
    
    def should_start_parallel_strategies(self) -> bool:
        """Check if parallel strategies should start simultaneously"""
        return (self.execution_mode == ExecutionMode.PARALLEL and 
                self.shared_settings.global_parallel_start_mode)
    
    def get_strategy_start_priority(self, strategy_type: StrategyType) -> int:
        """Get start priority for a strategy (lower number = higher priority)"""
        strategy_name = strategy_type.value.upper()
        return self.shared_settings.get_strategy_priority_index(strategy_name)
    
    def apply_shared_settings_to_strategies(self):
        """Apply shared settings to individual strategy settings where applicable"""
        for strategy_type in StrategyType:
            strategy_settings = self.get_strategy_settings(strategy_type)
            
            # Apply global position sizing if strategy doesn't have specific settings
            if not hasattr(strategy_settings, 'position_size_unit') or not strategy_settings.position_size_unit:
                strategy_settings.position_size_unit = self.shared_settings.global_position_size_unit
                strategy_settings.fixed_position_size = self.shared_settings.global_fixed_position_size
            
            # Apply global strategy alignment
            strategy_settings.strategy_alignment = self.shared_settings.global_strategy_alignment
            strategy_settings.parallel_start_mode = self.shared_settings.global_parallel_start_mode
            strategy_settings.strategy_to_start_with = self.shared_settings.global_strategy_to_start_with
            strategy_settings.order_number_to_start = self.shared_settings.global_order_number_to_start
            strategy_settings.sequential_mode_strategy = self.shared_settings.global_sequential_mode_strategy
            
            # Apply coordination enabled flag based on global coordination settings
            # Coordination should be disabled for single strategy execution
            strategy_settings.other_strategies_entry_index = self.is_strategy_coordination_enabled()
    
    def get_risk_limits_status(self, current_loss: float, current_drawdown_pct: float) -> Dict[str, bool]:
        """Get comprehensive risk limits status"""
        return {
            'within_limits': self.shared_settings.is_within_risk_limits(current_loss, current_drawdown_pct),
            'emergency_exit': self.shared_settings.should_trigger_emergency_exit(current_loss, current_drawdown_pct),
            'daily_limits_enabled': self.shared_settings.enable_daily_limits,
            'drawdown_protection_enabled': self.shared_settings.enable_drawdown_protection,
            'emergency_exit_enabled': self.shared_settings.enable_emergency_exit
        }

# Default configuration instance
default_config = TradingConfig()

# Example configurations for different scenarios
def get_demo_single_cdm_config() -> TradingConfig:
    """Demo account, single CDM strategy on AAPL"""
    config = TradingConfig(
        account_type=AccountType.DEMO,
        execution_mode=ExecutionMode.SINGLE,
        active_strategies=[StrategyType.CDM],
        tickers=["AAPL"]
    )
    config.enable_strategy(StrategyType.CDM, True)
    config.cdm_settings.capital_allocation = 1.0  # 100% for single strategy
    return config

def get_demo_parallel_multi_config() -> TradingConfig:
    """Demo account, parallel CDM+WDM on AAPL"""
    config = TradingConfig(
        account_type=AccountType.DEMO,
        execution_mode=ExecutionMode.PARALLEL,
        active_strategies=[StrategyType.CDM, StrategyType.WDM],
        tickers=["AAPL"]
    )
    config.enable_strategy(StrategyType.CDM, True)
    config.enable_strategy(StrategyType.WDM, True)
    config.cdm_settings.capital_allocation = 0.5  # 50% each
    config.wdm_settings.capital_allocation = 0.5
    return config

def get_live_multi_ticker_config() -> TradingConfig:
    """Live account, CDM on multiple tickers"""
    config = TradingConfig(
        account_type=AccountType.LIVE,
        execution_mode=ExecutionMode.SINGLE,
        active_strategies=[StrategyType.CDM],
        tickers=["AAPL", "TSLA", "MSFT"]
    )
    config.enable_strategy(StrategyType.CDM, True)
    config.position_size_value = 2.0  # 2% per ticker
    return config

def get_ib_bar_size(timeframe: str) -> str:
    """Convert display timeframe to IB bar size format"""
    timeframe_mapping = {
        "1 min": "1 min",
        "5 mins": "5 mins",
        "15 mins": "15 mins",
        "30 mins": "30 mins",
        "1 hour": "1 hour",
        "2 hours": "2 hours",
        "4 hours": "4 hours",
        "1 day": "1 day",
        "1 week": "1 week",
        "1 month": "1 month"
    }
    return timeframe_mapping.get(timeframe, "1 min")

def get_yfinance_interval(timeframe: str) -> str:
    """Convert display timeframe to yfinance interval format"""
    interval_mapping = {
        # Support both display names and direct interval codes
        "1 min": "1m",
        "5 mins": "5m",
        "15 mins": "15m",
        "30 mins": "30m",
        "1 hour": "1h",
        "2 hours": "2h",
        "4 hours": "4h",
        "1 day": "1d",
        "1 week": "1wk",
        "1 month": "1mo",
        # Direct interval codes from backtesting UI
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "1d": "1d",
        "1wk": "1wk",
        "1mo": "1mo"
    }
    return interval_mapping.get(timeframe, "1h")