# Shared Settings Implementation

This document describes the comprehensive **Shared Settings** implementation for the Multi-Martingales Trading Bot. The SharedSettings functionality provides centralized configuration management for global trading parameters, risk management, strategy coordination, and advanced features.

## Overview

The SharedSettings implementation addresses the requirements specified in the original documentation by providing:

- **Global Strategy Coordination**: Centralized control over how multiple strategies interact
- **Advanced Position Sizing**: Multiple position sizing methods with dynamic adjustments
- **Comprehensive Risk Management**: Daily limits, drawdown protection, and emergency exits
- **Global Trailing Stops**: Unified trailing stop management across all strategies
- **Configuration Validation**: Real-time validation of all settings
- **Flexible Money Management**: Advanced capital allocation and growth strategies

## Key Features

### 1. Global Strategy Coordination

```python
# Enable strategy coordination
panel.enable_strategy_coordination(
    enabled=True,
    alignment="PARALLEL",  # or "SEQUENTIAL"
    start_strategy="CDM"
)

# Check coordination status
if config.is_strategy_coordination_enabled():
    next_strategy = config.get_next_strategy_in_sequence(StrategyType.CDM)
```

**Available Settings:**
- `enable_strategy_coordination`: Enable/disable coordination
- `global_strategy_alignment`: "PARALLEL" or "SEQUENTIAL"
- `global_strategy_to_start_with`: Starting strategy name
- `global_parallel_start_mode`: Start all strategies simultaneously
- `strategy_start_priority`: Priority order for strategy execution

### 2. Advanced Position Sizing

```python
# Configure position sizing
panel.update_position_sizing_advanced(
    size_unit="PERCENTAGE",  # "PERCENTAGE", "USD", "SHARES"
    percentage=5.0,
    enable_dynamic=True,
    dynamic_factor=1.5
)

# Calculate effective position size
position_size = config.get_effective_position_size_for_strategy(
    StrategyType.CDM, account_balance=50000, symbol_price=150
)
```

**Position Sizing Options:**
- **Fixed Amount**: Specific dollar amount or share count
- **Percentage**: Percentage of account balance
- **Dynamic Sizing**: Adjusts based on performance metrics
- **Portfolio-Based**: Considers overall portfolio heat

### 3. Comprehensive Risk Management

```python
# Update risk management settings
panel.update_risk_management(
    daily_loss_limit=1000.0,
    daily_profit_target=2000.0,
    max_drawdown_pct=10.0,
    max_concurrent_cycles=5
)

# Check risk status
risk_status = panel.get_risk_status(
    current_loss=500.0,
    current_drawdown_pct=3.0
)
```

**Risk Management Features:**
- **Daily Limits**: Maximum daily loss and profit targets
- **Drawdown Protection**: Portfolio-level drawdown monitoring
- **Concurrent Cycle Limits**: Maximum simultaneous strategy cycles
- **Emergency Exit**: Automatic position closure on extreme conditions

### 4. Global Trailing Stops

```python
# Enable trailing stops
panel.enable_trailing_stops(
    enabled=True,
    trailing_pct=2.0,
    activation_pct=1.0
)
```

**Trailing Stop Features:**
- **Global Application**: Applied across all strategies
- **Configurable Thresholds**: Customizable trailing and activation percentages
- **Update Frequency**: Configurable update intervals

### 5. Configuration Validation

```python
# Validate configuration
errors = panel.validate_configuration()
if errors:
    for error in errors:
        print(f"Validation Error: {error}")
else:
    print("Configuration is valid")
```

## Configuration Structure

The SharedSettings class contains the following parameter groups:

### Basic Trading Settings
- `continue_trading`: Enable continuous trading
- `pre_after_hours`: Allow pre/after hours trading
- `money_management`: Enable money management
- `initial_balance`: Starting account balance
- `order_type`: Default order type

### Global Strategy Coordination
- `enable_strategy_coordination`: Master coordination switch
- `global_strategy_alignment`: PARALLEL or SEQUENTIAL execution
- `global_strategy_to_start_with`: Initial strategy
- `global_parallel_start_mode`: Simultaneous start for parallel mode
- `strategy_start_priority`: Strategy execution priority list

### Global Position Sizing
- `global_position_size_unit`: PERCENTAGE, USD, or SHARES
- `global_fixed_position_size`: Fixed size value
- `global_percentage_of_balance`: Percentage for percentage-based sizing
- `enable_dynamic_sizing`: Enable dynamic position adjustments
- `dynamic_sizing_factor`: Multiplier for dynamic sizing
- `enable_portfolio_based_sizing`: Portfolio heat consideration
- `portfolio_heat_limit`: Maximum portfolio heat percentage

### Global Risk Management
- `global_max_concurrent_cycles`: Maximum simultaneous cycles
- `enable_daily_limits`: Enable daily P&L limits
- `global_daily_loss_limit`: Maximum daily loss
- `global_daily_profit_target`: Daily profit target
- `enable_drawdown_protection`: Enable drawdown monitoring
- `max_portfolio_drawdown_pct`: Maximum portfolio drawdown
- `drawdown_calculation_period_days`: Drawdown calculation period

### Trading Hours and Order Management
- `enable_trading_hours_restriction`: Restrict trading hours
- `trading_start_time`: Trading session start time
- `trading_end_time`: Trading session end time
- `enable_order_timeout`: Enable order timeouts
- `order_timeout_minutes`: Order timeout duration
- `max_pending_orders_per_strategy`: Maximum pending orders

### Cycle Management
- `cycle_completion_behavior`: RESTART, STOP, or CONTINUE
- `max_cycles_per_day`: Maximum cycles per trading day
- `cycle_cooldown_minutes`: Cooldown between cycles
- `enable_cycle_profit_target`: Enable cycle-level profit targets
- `cycle_profit_target_pct`: Cycle profit target percentage

### Money Management
- `growth_threshold`: Balance threshold for position size increases
- `increase_value`: Position size increase amount
- `progressive_reinvestment_step`: Reinvestment step size
- `enable_compound_growth`: Enable compound growth
- `compound_frequency_days`: Compounding frequency
- `capital_allocation_method`: EQUAL, WEIGHTED, or DYNAMIC

### Global Trailing Stops
- `enable_global_trailing_stops`: Master trailing stop switch
- `global_trailing_stop_pct`: Trailing stop percentage
- `global_trailing_activation_pct`: Activation threshold
- `trailing_stop_update_frequency_seconds`: Update frequency

### Exit Conditions
- `enable_emergency_exit`: Enable emergency exit conditions
- `emergency_loss_threshold_pct`: Emergency exit threshold
- `enable_time_based_exit`: Enable time-based exits
- `max_position_hold_hours`: Maximum position hold time
- `force_exit_before_close_minutes`: Pre-close exit timing

### Notifications
- `enable_notifications`: Master notification switch
- `notification_methods`: List of notification methods
- `notify_on_trade_execution`: Trade execution notifications
- `notify_on_cycle_completion`: Cycle completion notifications
- `notify_on_daily_limits`: Daily limit notifications
- `notify_on_emergency_exit`: Emergency exit notifications

## Usage Examples

### Basic Setup

```python
from app.control_panel import ControlPanel

# Create control panel
panel = ControlPanel("my_config.json")

# Load or create configuration
config = panel.load_config()
if not config:
    config = panel.create_default_config("demo")
    panel.config = config

# Validate configuration
errors = panel.validate_configuration()
if not errors:
    print("Configuration is valid")
```

### Risk Management Setup

```python
# Configure comprehensive risk management
panel.update_risk_management(
    daily_loss_limit=500.0,
    daily_profit_target=1000.0,
    max_drawdown_pct=8.0,
    max_concurrent_cycles=3
)

# Enable emergency exit
panel.update_shared_settings(
    enable_emergency_exit=True,
    emergency_loss_threshold_pct=12.0
)
```

### Strategy Coordination

```python
# Enable sequential strategy execution
panel.enable_strategy_coordination(
    enabled=True,
    alignment="SEQUENTIAL",
    start_strategy="CDM"
)

# Enable multiple strategies
panel.enable_strategy("CDM", True)
panel.enable_strategy("WDM", True)
panel.enable_strategy("ZRM", True)
```

### Advanced Position Sizing

```python
# Dynamic percentage-based sizing
panel.update_position_sizing_advanced(
    size_unit="PERCENTAGE",
    percentage=3.0,
    enable_dynamic=True,
    dynamic_factor=1.5
)

# Fixed dollar amount sizing
panel.update_position_sizing_advanced(
    size_unit="USD",
    fixed_size=1000.0,
    enable_dynamic=False
)
```

### Trailing Stops

```python
# Enable global trailing stops
panel.enable_trailing_stops(
    enabled=True,
    trailing_pct=1.5,
    activation_pct=0.8
)

# Configure update frequency
panel.update_shared_settings(
    trailing_stop_update_frequency_seconds=15
)
```

## Integration with Existing Code

The SharedSettings implementation integrates seamlessly with the existing codebase:

### TradingConfig Integration

```python
# Access shared settings through TradingConfig
config = TradingConfig(...)

# Validate entire configuration
errors = config.validate_configuration()

# Apply shared settings to strategies
config.apply_shared_settings_to_strategies()

# Check strategy coordination
if config.is_strategy_coordination_enabled():
    next_strategy = config.get_next_strategy_in_sequence(current_strategy)

# Calculate position sizes
position_size = config.get_effective_position_size_for_strategy(
    strategy_type, account_balance, symbol_price
)

# Check risk limits
risk_status = config.get_risk_limits_status(current_loss, current_drawdown)
```

### ControlPanel Integration

```python
# Use ControlPanel for high-level management
panel = ControlPanel()

# Update settings with validation
panel.update_shared_settings(enable_daily_limits=True)

# Get comprehensive status
summary = panel.get_shared_settings_summary()
risk_status = panel.get_risk_status()

# Print detailed status
panel.print_status()
```

## Demo Script

Run the included demo script to see the SharedSettings functionality in action:

```bash
python shared_settings_demo.py
```

The demo script demonstrates:
- Basic configuration setup
- Risk management configuration
- Strategy coordination
- Position sizing options
- Trailing stops setup
- Comprehensive configuration

## Validation and Error Handling

The implementation includes comprehensive validation:

```python
# Automatic validation on updates
success = panel.update_shared_settings(global_daily_loss_limit=1000.0)
if not success:
    print("Update failed validation")

# Manual validation
errors = panel.validate_configuration()
for error in errors:
    print(f"Error: {error}")
```

**Validation Checks:**
- Parameter ranges and types
- Logical consistency
- Strategy compatibility
- Risk limit coherence
- Position sizing validity

## Benefits

1. **Centralized Control**: All global settings managed from one location
2. **Consistency**: Ensures consistent behavior across all strategies
3. **Flexibility**: Supports multiple trading styles and risk profiles
4. **Safety**: Comprehensive risk management and validation
5. **Scalability**: Easy to add new global parameters
6. **Integration**: Seamless integration with existing code

## Future Enhancements

The SharedSettings implementation provides a foundation for future enhancements:

- **Machine Learning Integration**: Dynamic parameter adjustment based on performance
- **Market Condition Adaptation**: Automatic settings adjustment based on market volatility
- **Advanced Notifications**: Integration with external notification systems
- **Performance Analytics**: Real-time performance tracking and optimization
- **Risk Scenario Testing**: Stress testing with different risk scenarios

## Conclusion

The SharedSettings implementation successfully addresses the requirements for centralized configuration management while providing a flexible and extensible foundation for future development. It enhances the trading bot's capabilities with comprehensive risk management, strategy coordination, and advanced position sizing options.