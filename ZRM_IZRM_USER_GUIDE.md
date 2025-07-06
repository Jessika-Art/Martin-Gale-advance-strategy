# ZRM and IZRM Strategy Guide for UI Users

## What You'll See in the Trading Interface

This guide explains how the ZRM and IZRM strategies work from a user perspective - what you'll observe in the trading interface and configuration screens.

## Understanding the Strategy Settings

### Zone Center Price
**What you see**: A price input field in the strategy configuration
**What it means**: This is your "home base" price - the level where the strategy considers the market to be fairly valued. You can either:
- Set it manually (e.g., $100.00)
- Leave it empty to use the current market price when the strategy starts

### Order Distances
**What you see**: A list of percentage values (e.g., 1%, 2%, 3%, 5%)
**What it means**: These control how far the price must move before the strategy places each trade:
- **1st trade**: Triggers when price moves 1% from center
- **2nd trade**: Triggers when price moves 2% from center  
- **3rd trade**: Triggers when price moves 3% from center
- And so on...

**Why this matters**: Each trade requires a bigger price movement, preventing the strategy from overtrading on small market fluctuations.

### Order Sizes
**What you see**: Multiplier values (e.g., 1.0, 1.5, 2.0, 3.0)
**What it means**: How much larger each subsequent trade becomes:
- **1st trade**: 1.0x your base position size
- **2nd trade**: 1.5x your base position size
- **3rd trade**: 2.0x your base position size

## How You'll See the Strategies Work

### ZRM (Zone Recovery Martingale) - What You'll Observe

#### Strategy Activation
- **Trigger**: Strategy starts when market price equals your zone center
- **UI Display**: You'll see "Strategy Active" status change to green

#### Trade Execution Pattern
- **Price Movement**: As price moves away from center, you'll see trades being placed
- **Order Types**: The strategy alternates between BUY and SELL orders
- **Trade Timing**: 
  - Price goes up 1% → Places a SELL order
  - Price goes down 2% → Places a BUY order
  - Price goes up 3% → Places another SELL order

#### What This Looks Like in Your Portfolio
- **Mixed Positions**: You'll have both long (BUY) and short (SELL) positions
- **Net Position**: The interface shows your overall exposure (total BUYs minus total SELLs)
- **Recovery Focus**: Strategy exits when your net position becomes profitable

### IZRM (Inverse Zone Recovery Martingale) - What You'll Observe

#### Strategy Activation
- **Trigger**: Strategy starts when price moves AWAY from your zone center
- **Direction Detection**: 
  - If price goes above center → "UP breakout" mode
  - If price goes below center → "DOWN breakout" mode

#### Trade Execution Pattern
- **Directional Focus**: Only trades in the breakout direction
- **UP Breakout Example**:
  - Price hits upper levels → Places trades (alternating BUY/SELL)
  - Ignores lower price movements
- **DOWN Breakout Example**:
  - Price hits lower levels → Places trades (alternating BUY/SELL)
  - Ignores upper price movements

## What You'll See in the Trading Interface

### Real-Time Monitoring

#### Position Display
- **Individual Positions**: Each trade shown separately with entry price and current P&L
- **Net Position**: Overall long/short exposure across all trades
- **Total P&L**: Combined profit/loss from all positions

#### Strategy Status Indicators
- **Active/Inactive**: Green/red status showing if strategy is running
- **Current Leg**: Shows which trade number the strategy is on (1st, 2nd, 3rd, etc.)
- **Boundary Status**: Indicates which price level was last triggered

#### Exit Conditions You'll See
- **Profitable Exit**: Strategy closes when net position shows profit
- **Take Profit**: Individual positions may close at preset profit levels
- **Stop Loss**: Protection against excessive losses
- **Trailing Stops**: Automatic profit protection that follows favorable price moves

### Configuration Interface

#### Basic Settings
- **Symbol**: Which stock/asset to trade
- **Zone Center**: Your fair value price reference
- **Max Orders**: Maximum number of trades the strategy can make
- **Capital Allocation**: Percentage of your account to use

#### Advanced Settings
- **Order Distances**: How far price must move for each trade
- **Order Sizes**: How much larger each trade becomes
- **Take Profit Levels**: Profit targets for each position
- **Stop Loss Levels**: Loss limits for protection

## Key Benefits You'll Experience

### Smart Risk Management
- **Hedged Positions**: Mix of BUY and SELL orders reduces directional risk
- **Expanding Distances**: Larger price movements required for later trades
- **Net Position Focus**: Strategy considers overall profitability, not individual trades

### Adaptive Behavior
- **Market Noise Filtering**: Small price movements don't trigger unnecessary trades
- **Trend Adaptation**: IZRM follows breakouts, ZRM expects reversions
- **Recovery Oriented**: Designed to recover from initial losses

### User Control
- **Flexible Configuration**: Adjust all parameters to match your risk tolerance
- **Real-Time Monitoring**: See exactly what the strategy is doing
- **Manual Override**: Can stop or modify the strategy at any time

## Practical Examples

### ZRM Example (What You'd See)
1. **Setup**: Zone center at $100, distances: 1%, 2%, 3%
2. **Trade 1**: Price hits $101 → SELL 100 shares
3. **Trade 2**: Price drops to $98 → BUY 150 shares  
4. **Trade 3**: Price rises to $103 → SELL 200 shares
5. **Net Position**: -150 shares (more SELL than BUY)
6. **Exit**: When net position shows profit

### IZRM Example (What You'd See)
1. **Setup**: Zone center at $100, UP breakout detected at $102
2. **Trade 1**: Price hits $105 → SELL 100 shares
3. **Trade 2**: Price hits $108 → BUY 150 shares
4. **Trade 3**: Price hits $112 → SELL 200 shares
5. **Exit**: Either when profitable OR price returns to $100

## Important Notes for UI Users

### Risk Awareness
- **Capital Requirements**: These strategies can use significant capital
- **Market Conditions**: Performance varies with different market environments
- **Monitoring**: Keep an eye on your positions and overall account balance

### Best Practices
- **Start Small**: Use conservative position sizes when learning
- **Paper Trading**: Test strategies with virtual money first
- **Regular Review**: Check and adjust settings based on performance
- **Stop Losses**: Always use appropriate risk management settings

### When to Use Each Strategy
- **ZRM**: Best in sideways/ranging markets where prices tend to revert
- **IZRM**: Best in trending markets where breakouts tend to continue

This interface-focused approach helps you understand what's happening behind the scenes without needing to know the technical implementation details.