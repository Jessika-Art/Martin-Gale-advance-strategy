# Account Balance Integration Guide

## Overview

This document explains the automatic account balance integration that replaces manual balance input with real-time data from Interactive Brokers.

## Key Changes

### 1. Automatic Balance Retrieval

**Before:**
- Manual input of initial balance in UI
- Fixed value used for all calculations
- Risk of using outdated or incorrect balance

**After:**
- Real-time balance retrieved from IBKR account
- Automatic updates when connected
- Fallback to manual input when disconnected

### 2. Position Sizing Improvements

**Previous Issue:**
- Position sizes calculated in dollar amounts
- Could result in massive orders (e.g., 62,500 shares)
- No safety limits on order sizes

**Current Solution:**
- Position sizes converted to actual share quantities
- Safety limits: minimum 1 share, maximum 1,000 shares
- Proper price-based calculations

## How It Works

### Balance Retrieval

```python
# IBKR API automatically requests account summary
api.reqAccountSummary(9001, "All", "TotalCashValue,NetLiquidation,AvailableFunds,BuyingPower")

# Balance is available via:
balance = api.get_account_balance()  # Returns NetLiquidation
buying_power = api.get_buying_power()  # Returns BuyingPower
```

### Position Sizing Formula

```python
# Step 1: Calculate dollar amount to invest
dollar_amount = account_balance × capital_allocation × size_multiplier

# Step 2: Convert to shares
shares = dollar_amount ÷ current_price

# Step 3: Apply safety limits
final_shares = max(1, min(int(shares), 1000))
```

### Example Calculation

**Scenario:**
- Account Balance: $250,000
- Capital Allocation: 5% (0.05)
- Size Multiplier: 1.0 (first leg)
- Stock Price: $500

**Calculation:**
1. Dollar Amount = $250,000 × 0.05 × 1.0 = $12,500
2. Shares = $12,500 ÷ $500 = 25 shares
3. Final = max(1, min(25, 1000)) = 25 shares

**Result:** Order for 25 shares instead of 25,000 shares!

## UI Changes

### Connected State
When connected to IBKR:
- Displays real account balance and buying power
- Updates automatically
- No manual input required

### Disconnected State
When not connected:
- Shows warning message
- Allows manual balance input as fallback
- Maintains previous functionality

## Configuration Impact

### Settings That Affect Position Sizing

1. **Capital Allocation** (`capital_allocation`)
   - Percentage of account to use per strategy
   - Default: 5% (0.05)
   - Range: 1-20% recommended

2. **Order Size Multipliers** (`order_sizes`)
   - Multipliers for each martingale leg
   - Default: [1.0, 2.0, 4.0, 8.0]
   - Controls position scaling

3. **Safety Limits** (hardcoded)
   - Minimum: 1 share
   - Maximum: 1,000 shares per order
   - Prevents oversized positions

## Risk Management

### Built-in Protections

1. **Share Limits**
   - Maximum 1,000 shares per order
   - Prevents accidental large positions

2. **Price Validation**
   - Requires valid current price
   - Fallback to conservative estimates

3. **Account Balance Checks**
   - Uses real-time balance data
   - Prevents trading with outdated information

### Recommended Settings

**Conservative (Low Risk):**
- Capital Allocation: 2-3%
- Order Sizes: [1.0, 1.5, 2.0, 3.0]

**Moderate (Medium Risk):**
- Capital Allocation: 5%
- Order Sizes: [1.0, 2.0, 4.0, 6.0]

**Aggressive (High Risk):**
- Capital Allocation: 10%
- Order Sizes: [1.0, 2.0, 4.0, 8.0]

## Troubleshooting

### Common Issues

1. **"Order rejected - insufficient funds"**
   - Check if account balance is correctly retrieved
   - Verify capital allocation settings
   - Ensure buying power is sufficient

2. **"Position size too small"**
   - Increase capital allocation
   - Check if stock price is very high
   - Verify account balance is accurate

3. **"No current price available"**
   - Ensure market data subscription is active
   - Check if symbol is correctly subscribed
   - Verify market hours

### Logging Information

The system now logs detailed position sizing information:

```
Position sizing: Account=$250,000.00, Allocation=5.0%, Multiplier=1.00, 
Dollar Amount=$12,500.00, Price=$500.00, Shares=25
```

This helps debug position sizing issues and verify calculations.

## Migration Notes

### For Existing Users

1. **Automatic Migration**
   - No action required when connected to IBKR
   - System automatically uses real balance

2. **Configuration Review**
   - Review capital allocation settings
   - Adjust for your actual account size
   - Test with small positions first

3. **Monitoring**
   - Watch initial orders for correct sizing
   - Check logs for position calculations
   - Verify P&L calculations

### Testing Recommendations

1. **Paper Trading**
   - Test with IBKR paper account first
   - Verify position sizes are reasonable
   - Check all calculations

2. **Small Positions**
   - Start with low capital allocation (1-2%)
   - Monitor first few trades closely
   - Gradually increase if working correctly

## Benefits

1. **Accuracy**
   - Always uses current account balance
   - Eliminates manual input errors
   - Real-time risk management

2. **Safety**
   - Built-in position size limits
   - Prevents oversized orders
   - Automatic price-based calculations

3. **Convenience**
   - No manual balance updates needed
   - Automatic synchronization
   - Seamless integration

4. **Transparency**
   - Detailed logging of calculations
   - Clear position sizing logic
   - Easy troubleshooting