import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import get_yfinance_interval
from backtesting_system import BacktestingAdapter
from config import TradingConfig

def test_ui_default_dates():
    """Test with the exact same date range that the UI uses by default"""
    print("Testing UI Default Date Range")
    print("=" * 40)
    
    # This is exactly what the UI does
    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=365)
    end_date = current_date
    
    print(f"Current date: {current_date}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    print(f"Date range: {start_date} to {end_date}")
    
    # Convert to strings like the UI does
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"String format: {start_str} to {end_str}")
    print()
    
    # Test each timeframe
    timeframes = ["1h", "4h", "1d"]
    symbol = "AAPL"
    
    for timeframe in timeframes:
        print(f"Testing {timeframe} timeframe:")
        print("-" * 25)
        
        try:
            # Test direct yfinance call
            yf_interval = get_yfinance_interval(timeframe)
            ticker = yf.Ticker(symbol)
            
            print(f"Calling yfinance with: start={start_str}, end={end_str}, interval={yf_interval}")
            
            data = ticker.history(
                start=start_str,
                end=end_str,
                interval=yf_interval,
                auto_adjust=True,
                prepost=True
            )
            
            if data.empty:
                print(f"❌ No data returned")
            else:
                print(f"✅ Retrieved {len(data)} data points")
                print(f"Date range: {data.index[0]} to {data.index[-1]}")
                
                # Check if dates are reasonable
                data_start = data.index[0].tz_localize(None) if data.index[0].tz else data.index[0]
                data_end = data.index[-1].tz_localize(None) if data.index[-1].tz else data.index[-1]
                
                expected_start = pd.to_datetime(start_str)
                expected_end = pd.to_datetime(end_str)
                
                print(f"Expected range: {expected_start} to {expected_end}")
                print(f"Actual range: {data_start} to {data_end}")
                
                # Check if data is in the future
                now = pd.Timestamp.now().tz_localize(None)
                if data_end > now:
                    print(f"⚠️  WARNING: Data extends into the future!")
                    print(f"   Current time: {now}")
                    print(f"   Data end: {data_end}")
                    print(f"   Future by: {data_end - now}")
                else:
                    print(f"✅ Data is not in the future")
                
                # Show sample data
                print("First 3 rows:")
                print(data.head(3)[['Open', 'High', 'Low', 'Close']].round(2))
                
                print("Last 3 rows:")
                print(data.tail(3)[['Open', 'High', 'Low', 'Close']].round(2))
            
            # Test backtesting system
            print("\nTesting backtesting system:")
            config = TradingConfig()
            adapter = BacktestingAdapter(config, [])
            
            bt_data = adapter.fetch_data(symbol, start_str, end_str, timeframe)
            print(f"✅ Backtesting: {len(bt_data)} points")
            print(f"BT range: {bt_data.index[0]} to {bt_data.index[-1]}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

def test_safe_historical_range():
    """Test with a known safe historical range"""
    print("\nTesting Safe Historical Range (Jan-Dec 2023)")
    print("=" * 50)
    
    start_str = "2023-01-01"
    end_str = "2023-12-31"
    symbol = "AAPL"
    
    print(f"Using safe historical range: {start_str} to {end_str}")
    print()
    
    timeframes = ["1h", "4h", "1d"]
    
    for timeframe in timeframes:
        print(f"Testing {timeframe}:")
        try:
            config = TradingConfig()
            adapter = BacktestingAdapter(config, [])
            
            data = adapter.fetch_data(symbol, start_str, end_str, timeframe)
            print(f"✅ {len(data)} points, {data.index[0]} to {data.index[-1]}")
            
            # Check time intervals
            if len(data) > 1:
                time_diffs = data.index[1:] - data.index[:-1]
                unique_diffs = time_diffs.unique()
                print(f"   Intervals: {unique_diffs[:3]}...")  # Show first 3
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print()

if __name__ == "__main__":
    test_ui_default_dates()
    test_safe_historical_range()