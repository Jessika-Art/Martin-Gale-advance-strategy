# Interactive Brokers Market Data Subscription Setup

## Overview
To enable real-time trading with the MartinGales bot, you need proper market data subscriptions from Interactive Brokers. The Error 10167 indicates that your account doesn't have the required market data subscriptions.

## Current Status
Your bot is currently using **delayed market data** (15-20 minute delay), which is:
- ✅ **Sufficient for backtesting and learning**
- ❌ **NOT suitable for real-time trading**
- ❌ **Will cause poor trade execution timing**

## Market Data Subscription Options

### 1. US Securities Snapshot and Futures Value Bundle
**Cost:** ~$4.50/month
**Includes:**
- Real-time US stock quotes
- NASDAQ, NYSE, AMEX data
- Options data
- **Recommended for stock trading**

### 2. US Equity and Options Add-On Streaming Bundle
**Cost:** ~$14.50/month
**Includes:**
- Real-time streaming data
- Level I quotes
- Options chains
- **Best for active trading**

### 3. Professional Market Data
**Cost:** $25-100+/month
**Includes:**
- Level II data
- Advanced order book
- **For professional traders**

## How to Subscribe

### Step 1: Log into TWS or IB Gateway
1. Open Trader Workstation (TWS) or IB Gateway
2. Go to **Account Management**
3. Navigate to **Settings** → **Market Data Subscriptions**

### Step 2: Subscribe to Required Data
1. **For Stock Trading (Recommended):**
   - Subscribe to "US Securities Snapshot and Futures Value Bundle"
   - This covers NASDAQ, NYSE, AMEX real-time data

2. **For Active Trading:**
   - Subscribe to "US Equity and Options Add-On Streaming Bundle"
   - Provides streaming real-time data

### Step 3: Accept Market Data Agreements
1. Read and accept the **Market Data Agreements**
2. Complete any required **Professional/Non-Professional** declarations
3. **Important:** Most retail traders qualify as "Non-Professional"

### Step 4: Verify Subscription
1. Wait 15-30 minutes for activation
2. Restart TWS/IB Gateway
3. Check that real-time quotes appear (no delay indicator)

## Alternative: Free Real-Time Data

### IBKR Lite Accounts
If you have an **IBKR Lite** account:
- You get **free real-time US stock data**
- No additional subscription needed
- Limited to US stocks only

### Upgrade to IBKR Lite
1. Contact IBKR support
2. Request account type change
3. Meet minimum requirements (usually $0 minimum)

## Testing Your Setup

### 1. Check Market Data Status
```python
# In TWS, check if quotes show:
# ✅ Real-time: No delay indicator
# ❌ Delayed: "D" or delay notice
```

### 2. Verify in Bot Logs
After subscription, you should see:
```
✅ Market data subscription active
✅ Real-time quotes received
❌ No more "Error 10167" messages
```

### 3. Test Trading
- Start with paper trading account
- Verify orders execute at current market prices
- Check that price updates are immediate

## Cost Considerations

### Monthly Costs
- **Basic Real-time Data:** $4.50/month
- **Streaming Data:** $14.50/month
- **Commission Rebates:** Often offset subscription costs

### Cost-Benefit Analysis
- **Delayed Data:** Free but poor trade execution
- **Real-time Data:** Small cost but proper trade timing
- **For $1000+ trading:** Subscription cost is negligible vs. better execution

## Troubleshooting

### Still Getting Error 10167?
1. **Wait 30 minutes** after subscription
2. **Restart TWS/IB Gateway** completely
3. **Check account status** in Account Management
4. **Contact IBKR support** if issues persist

### Market Data Not Working?
1. Verify **Market Data Agreements** are signed
2. Check **Professional vs Non-Professional** status
3. Ensure **account is funded** (some subscriptions require minimum balance)
4. Try **different market data bundle**

## Recommendations

### For Learning/Testing
- ✅ Use **paper trading account**
- ✅ Start with **delayed data** (free)
- ✅ Subscribe to **basic real-time** when ready

### For Live Trading
- ✅ **Must have real-time data**
- ✅ Start with **US Securities Snapshot Bundle**
- ✅ Upgrade to **streaming** for active trading

### For Professional Use
- ✅ **Level II data** subscription
- ✅ **Multiple exchange** feeds
- ✅ **Professional** account status

## Next Steps

1. **Immediate:** Subscribe to US Securities Snapshot Bundle ($4.50/month)
2. **Test:** Verify real-time data in TWS
3. **Restart:** Restart the trading bot
4. **Monitor:** Check logs for Error 10167 resolution
5. **Trade:** Begin live trading with proper market data

## Support

If you need help:
- **IBKR Support:** 877-442-2757
- **Market Data Team:** Available 24/7
- **Documentation:** [IBKR Market Data Guide](https://www.interactivebrokers.com/en/index.php?f=14193)

---

**⚠️ Important:** Real-time market data is essential for profitable trading. The small subscription cost is typically offset by better trade execution and timing.