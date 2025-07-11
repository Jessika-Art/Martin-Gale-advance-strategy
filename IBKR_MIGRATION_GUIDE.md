# Migration Guide: From Yahoo Finance to Interactive Brokers

This guide explains how to switch from using Yahoo Finance (`yfinance`) to Interactive Brokers (IBKR) for historical market data in your backtesting system.

## Overview

The project now supports both Yahoo Finance and Interactive Brokers as data sources for backtesting. IBKR provides more accurate and comprehensive market data, especially for intraday trading strategies.

## Prerequisites

### 1. Interactive Brokers Setup
- **IBKR Account**: You need an active Interactive Brokers account
- **Market Data Permissions**: Ensure you have the necessary market data subscriptions
- **TWS or IB Gateway**: Install and run either:
  - Trader Workstation (TWS)
  - IB Gateway (lighter alternative)

### 2. Connection Configuration
- Default connection: `localhost:7497` (TWS) or `localhost:4001` (IB Gateway)
- Ensure API connections are enabled in TWS/Gateway settings
- Configure paper trading vs live trading as needed

## Key Changes Made

### 1. New IBKR Historical Data Module
Created `app/ibkr_historical_data.py` with:
- `HistoricalBar` dataclass for structured data
- `IBKRHistoricalDataClient` for connection management
- `IBKRDataProvider` for high-level data access
- `fetch_ibkr_data()` function for easy integration

### 2. Updated Backtesting System
Modified `app/backtesting_system.py`:
- Added `use_ibkr` parameter to `fetch_data()` method
- Added `use_ibkr` parameter to `run_backtest()` method
- Created separate methods: `_fetch_data_yfinance()` and `_fetch_data_ibkr()`
- Maintained all existing data validation and cleaning logic

## Usage Examples

### Basic Data Fetching

```python
from app.backtesting_system import BacktestingSystem
from app.config import BacktestConfig

# Initialize backtesting system
config = BacktestConfig()
backtester = BacktestingSystem(config)

# Fetch data using Yahoo Finance (default)
yf_data = backtester.fetch_data(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-02-01",
    interval="1h",
    use_ibkr=False  # Default behavior
)

# Fetch data using IBKR
ibkr_data = backtester.fetch_data(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-02-01",
    interval="1h",
    use_ibkr=True  # Use IBKR instead
)
```

### Running Backtests with IBKR

```python
# Run backtest with IBKR data
results = backtester.run_backtest(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-02-01",
    interval="1h",
    strategies=['martingale_rsi', 'martingale_macd'],
    use_ibkr=True  # Use IBKR for data
)
```

### Direct IBKR Data Access

```python
from app.ibkr_historical_data import fetch_ibkr_data

# Direct function call
data = fetch_ibkr_data(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-02-01",
    interval="1h"
)
```

## Migration Steps

### Step 1: Setup IBKR Connection
1. Install and configure TWS or IB Gateway
2. Enable API connections in settings
3. Start the application and ensure it's connected

### Step 2: Test IBKR Data Access
```python
# Run the example script to test IBKR connectivity
python examples/ibkr_backtesting_example.py
```

### Step 3: Update Your Code
Replace existing backtest calls:

**Before (Yahoo Finance only):**
```python
results = backtester.run_backtest(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-02-01",
    interval="1h"
)
```

**After (with IBKR option):**
```python
results = backtester.run_backtest(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-02-01",
    interval="1h",
    use_ibkr=True  # Add this parameter
)
```

### Step 4: Update Configuration (Optional)
You can modify `app/config.py` to set IBKR as default:

```python
# Add to your config class
class BacktestConfig:
    def __init__(self):
        # ... existing config ...
        self.default_data_source = 'ibkr'  # or 'yfinance'
```

## Advantages of IBKR over Yahoo Finance

### Data Quality
- **More Accurate**: Direct from exchange data
- **Better Intraday Coverage**: No 730-day limitation for intraday data
- **Real-time Updates**: Live data during market hours
- **Extended Hours**: Pre-market and after-hours data available

### Data Availability
- **Multiple Asset Classes**: Stocks, forex, futures, options
- **Global Markets**: Access to international exchanges
- **Higher Frequency**: Tick-level data available
- **Historical Depth**: Longer historical data retention

### Reliability
- **Professional Grade**: Institutional-quality data
- **Lower Latency**: Direct market connection
- **Consistent Format**: Standardized across all instruments

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure TWS/IB Gateway is running
   - Check API settings are enabled
   - Verify port numbers (7497 for TWS, 4001 for Gateway)

2. **No Data Returned**
   - Check market data permissions for the symbol
   - Verify date range is valid (not weekends/holidays)
   - Ensure symbol format is correct (e.g., "AAPL" not "AAPL.US")

3. **Timeout Errors**
   - Increase timeout settings in the configuration
   - Check network connectivity
   - Reduce date range for initial testing

### Error Messages

- `"Not connected to IBKR"`: Start TWS/Gateway and enable API
- `"No market data permissions"`: Subscribe to required data feeds
- `"Invalid contract"`: Check symbol format and exchange

## Performance Considerations

### Data Fetching Speed
- IBKR may be slower for initial requests due to connection overhead
- Yahoo Finance is faster for quick tests and development
- Consider caching IBKR data for repeated backtests

### Rate Limits
- IBKR has API rate limits (50 requests per second)
- Yahoo Finance has daily request limits
- Plan your data fetching strategy accordingly

## Best Practices

1. **Start Small**: Test with short date ranges first
2. **Validate Data**: Compare IBKR vs Yahoo Finance results initially
3. **Error Handling**: Always wrap IBKR calls in try-catch blocks
4. **Connection Management**: Properly close connections when done
5. **Market Hours**: Be aware of market hours for live data

## Example Scripts

See `examples/ibkr_backtesting_example.py` for a complete working example that demonstrates:
- Fetching data from both sources
- Running backtests with IBKR data
- Error handling and troubleshooting

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review IBKR API documentation
3. Ensure your IBKR account has proper permissions
4. Test with the provided example scripts first

## Future Enhancements

Planned improvements:
- Automatic fallback from IBKR to Yahoo Finance
- Data caching and persistence
- Real-time data integration for live trading
- Support for additional asset classes
- Configuration-based default data source selection