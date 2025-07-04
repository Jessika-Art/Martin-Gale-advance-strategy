# Trailing Stop Functionality

This document describes the new trailing stop functionality added to the Multi-Martingales Trading Bot.

## Overview

Trailing stops are a risk management tool that automatically adjusts stop-loss levels as the price moves in your favor. This helps lock in profits while allowing for continued upside potential.

## New Parameters

Two new parameters have been added to both CDM and ZRM strategy settings:

### `trailing_trigger_pct`
- **Type**: List of floats (one per leg)
- **Description**: The profit percentage required to activate the trailing stop for each leg
- **Default**: `[5.0, 5.0, 5.0, 5.0, 5.0]`
- **Example**: If set to `[3.0, 4.0, 5.0]`, the trailing stop will activate when:
  - Leg 1 reaches 3% profit
  - Leg 2 reaches 4% profit
  - Leg 3 reaches 5% profit

### `trailing_distance_pct`
- **Type**: List of floats (one per leg)
- **Description**: The percentage distance to maintain between current price and trailing stop
- **Default**: `[2.0, 2.0, 2.0, 2.0, 2.0]`
- **Example**: If set to `[1.0, 1.5, 2.0]`, the trailing stop will be:
  - Leg 1: 1% below the highest price reached
  - Leg 2: 1.5% below the highest price reached
  - Leg 3: 2% below the highest price reached

## How It Works

### Activation
1. A position must reach the specified `trailing_trigger_pct` profit level
2. Once triggered, the trailing stop becomes active for that position
3. The initial trailing stop price is set at `current_price * (1 - trailing_distance_pct / 100)`

### Updates
1. As the price moves higher, the trailing stop price is adjusted upward
2. The trailing stop price never moves down (it only "trails" upward)
3. The stop maintains the specified `trailing_distance_pct` from the highest price reached

### Triggering
1. If the current price falls to or below the trailing stop price, an exit signal is generated
2. This happens regardless of other exit conditions (take profit, zone recovery, etc.)

## Configuration Examples

### Conservative Trailing Stop
```python
cdm_settings = CDMSettings(
    # ... other settings ...
    trailing_trigger_pct=[2.0, 3.0, 4.0],  # Activate early
    trailing_distance_pct=[0.5, 1.0, 1.5]  # Tight trailing distance
)
```

### Aggressive Trailing Stop
```python
cdm_settings = CDMSettings(
    # ... other settings ...
    trailing_trigger_pct=[5.0, 7.0, 10.0],  # Activate later
    trailing_distance_pct=[2.0, 3.0, 4.0]   # Wider trailing distance
)
```

## UI Changes

The configuration UI has been updated with new input fields:

- **Profit Trigger %**: Sets the `trailing_trigger_pct` for each leg
- **Trailing Distance %**: Sets the `trailing_distance_pct` for each leg

These fields replace the previous `first_distance_trailing` and `trailing_progress` fields while maintaining backward compatibility.

## Backward Compatibility

Existing configurations will continue to work:
- Old `first_distance_trailing` and `trailing_progress` parameters are preserved
- New trailing stop parameters have sensible defaults
- Configuration files are automatically migrated when loaded

## Strategy Integration

### CDM Strategy
- Trailing stops work alongside existing take profit levels
- Can trigger exit even if price hasn't recovered to average entry price
- Each leg is tracked independently

### ZRM Strategy
- Trailing stops can trigger even when price is outside the recovery zone
- Provides additional exit mechanism beyond zone-based take profits
- Each leg is tracked independently

## Example Scenario

1. **Entry**: Buy 100 shares at $100.00
2. **Settings**: 
   - `trailing_trigger_pct[0] = 3.0` (3%)
   - `trailing_distance_pct[0] = 1.0` (1%)
3. **Price Movement**:
   - Price rises to $103.00 (3% profit) → Trailing stop activates at $101.97
   - Price rises to $105.00 → Trailing stop moves to $103.95
   - Price rises to $107.00 → Trailing stop moves to $105.93
   - Price falls to $105.93 → **Exit triggered by trailing stop**

## Benefits

1. **Profit Protection**: Automatically locks in gains as price moves favorably
2. **Reduced Emotional Trading**: Systematic exit rules reduce manual intervention
3. **Flexibility**: Different settings per leg allow for sophisticated risk management
4. **Integration**: Works seamlessly with existing strategy logic

## Testing

Run the demo script to see trailing stops in action:

```bash
python trailing_stop_demo.py
```

This script demonstrates:
- Configuration of trailing stop parameters
- Activation and updating of trailing stops
- Exit triggering when stop level is hit

## Implementation Details

### Key Methods

- `update_trailing_stops()`: Core logic for managing trailing stops
- `reset_trailing_stops()`: Resets all trailing stop states
- Integration in `should_exit()` methods of CDM and ZRM strategies

### State Tracking

- `trailing_stops_active`: Tracks which legs have active trailing stops
- `trailing_stop_prices`: Current trailing stop price for each leg
- `highest_profit_prices`: Highest price reached for each leg

### Position Direction

- Currently optimized for long positions (`position_direction = 'long'`)
- Can be extended for short positions in future versions

## Future Enhancements

1. **Short Position Support**: Extend trailing stops for short positions
2. **Time-Based Trailing**: Activate trailing stops after a time delay
3. **Volatility-Adjusted Distances**: Dynamic trailing distances based on market volatility
4. **Partial Position Trailing**: Trail only a portion of each position

---
