import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import get_yfinance_interval

def check_system_date():
    """Check what the system thinks the current date is"""
    print("System Date Check:")
    print("=" * 30)
    print(f"datetime.now(): {datetime.now()}")
    print(f"datetime.utcnow(): {datetime.utcnow()}")
    print(f"pd.Timestamp.now(): {pd.Timestamp.now()}")
    print(f"pd.Timestamp.utcnow(): {pd.Timestamp.utcnow()}")
    print()

def test_timeframe_issue(symbol="AAPL"):
    """Test the specific timeframe issue with proper dates"""
    print(f"Testing timeframe issue for {symbol}")
    print("=" * 50)
    
    # Use a known good historical date range
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    timeframes_to_test = ["1h", "4h", "1d"]
    
    for timeframe in timeframes_to_test:
        print(f"\nTesting {timeframe} timeframe:")
        print("-" * 30)
        
        try:
            # Convert using our mapping function
            yf_interval = get_yfinance_interval(timeframe)
            print(f"Mapped: {timeframe} -> {yf_interval}")
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=True
            )
            
            if data.empty:
                print(f"❌ No data for {timeframe}")
                continue
                
            print(f"✅ Retrieved {len(data)} data points")
            print(f"Date range: {data.index[0]} to {data.index[-1]}")
            
            # Show first few rows to check data quality
            print("First 3 rows:")
            print(data.head(3)[['Open', 'High', 'Low', 'Close']].round(2))
            
            # Check time intervals
            if len(data) > 1:
                time_diffs = data.index[1:] - data.index[:-1]
                unique_diffs = time_diffs.unique()
                print(f"Time intervals found: {unique_diffs}")
                
                # Expected intervals
                expected = {
                    "1h": pd.Timedelta(hours=1),
                    "4h": pd.Timedelta(hours=4),
                    "1d": pd.Timedelta(days=1)
                }
                
                if timeframe in expected:
                    exp_interval = expected[timeframe]
                    if len(unique_diffs) == 1 and abs((unique_diffs[0] - exp_interval).total_seconds()) < 3600:
                        print(f"✅ Correct interval: {exp_interval}")
                    else:
                        print(f"⚠️  Unexpected intervals. Expected: {exp_interval}")
            
            # Test with backtesting system
            print("\nTesting with backtesting system:")
            try:
                from backtesting_system import BacktestingAdapter
                from config import TradingConfig
                
                config = TradingConfig()
                adapter = BacktestingAdapter(config, [])
                
                bt_data = adapter.fetch_data(symbol, start_date, end_date, timeframe)
                print(f"✅ Backtesting fetch: {len(bt_data)} points")
                print(f"BT range: {bt_data.index[0]} to {bt_data.index[-1]}")
                
                # Compare data
                if len(bt_data) == len(data):
                    print(f"✅ Same data length as direct yfinance")
                    
                    # Check if data is identical
                    if bt_data.equals(data):
                        print(f"✅ Data is identical")
                    else:
                        print(f"⚠️  Data differs from direct yfinance")
                        # Show differences in first few rows
                        diff_cols = ['Open', 'High', 'Low', 'Close']
                        print("Direct yfinance (first 2):")
                        print(data.head(2)[diff_cols].round(2))
                        print("Backtesting system (first 2):")
                        print(bt_data.head(2)[diff_cols].round(2))
                else:
                    print(f"⚠️  Different data length: BT={len(bt_data)}, Direct={len(data)}")
                    
            except Exception as bt_e:
                print(f"❌ Backtesting system error: {str(bt_e)}")
                
        except Exception as e:
            print(f"❌ Error with {timeframe}: {str(e)}")
    
    print("\n" + "=" * 50)

def test_ui_date_handling():
    """Test how the UI passes dates to the backtesting system"""
    print("\nTesting UI date handling simulation:")
    print("=" * 40)
    
    # Simulate how the UI creates dates
    from datetime import date
    
    # This is how the UI creates dates
    ui_start_date = date(2024, 1, 1)
    ui_end_date = date(2024, 1, 31)
    
    # This is how they get converted to strings
    start_str = ui_start_date.strftime('%Y-%m-%d')
    end_str = ui_end_date.strftime('%Y-%m-%d')
    
    print(f"UI start date: {ui_start_date} -> {start_str}")
    print(f"UI end date: {ui_end_date} -> {end_str}")
    
    # Test with these exact strings
    try:
        from backtesting_system import BacktestingAdapter
        from config import TradingConfig
        
        config = TradingConfig()
        adapter = BacktestingAdapter(config, [])
        
        for timeframe in ["1h", "4h", "1d"]:
            try:
                data = adapter.fetch_data("AAPL", start_str, end_str, timeframe)
                print(f"✅ {timeframe}: {len(data)} points, {data.index[0]} to {data.index[-1]}")
            except Exception as e:
                print(f"❌ {timeframe}: {str(e)}")
                
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")

if __name__ == "__main__":
    check_system_date()
    test_timeframe_issue()
    test_ui_date_handling()