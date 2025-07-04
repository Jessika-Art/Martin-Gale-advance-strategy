import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import get_yfinance_interval
from backtesting_system import BacktestingAdapter
from config import TradingConfig

def test_timeframe_fix():
    """Test that the timeframe issue is now fixed"""
    print("Testing Timeframe Fix")
    print("=" * 30)
    
    # Test with recent dates (within 700 days)
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    symbol = "AAPL"
    
    print(f"Testing with recent dates: {start_date} to {end_date}")
    print(f"Symbol: {symbol}")
    print()
    
    # Test all timeframes
    timeframes = ["1h", "4h", "1d"]
    
    for timeframe in timeframes:
        print(f"Testing {timeframe} timeframe:")
        print("-" * 25)
        
        try:
            # Test with backtesting system (this should now work)
            config = TradingConfig()
            adapter = BacktestingAdapter(config, [])
            
            data = adapter.fetch_data(symbol, start_date, end_date, timeframe)
            
            print(f"✅ Success: {len(data)} data points")
            print(f"Date range: {data.index[0]} to {data.index[-1]}")
            
            # Check time intervals
            if len(data) > 1:
                time_diffs = data.index[1:] - data.index[:-1]
                unique_diffs = time_diffs.unique()
                
                # Expected intervals
                expected = {
                    "1h": pd.Timedelta(hours=1),
                    "4h": pd.Timedelta(hours=4),
                    "1d": pd.Timedelta(days=1)
                }
                
                if timeframe in expected:
                    exp_interval = expected[timeframe]
                    # Check if most intervals match expected (allowing for some variation due to weekends/holidays)
                    correct_intervals = sum(1 for diff in time_diffs if abs((diff - exp_interval).total_seconds()) < 3600)
                    total_intervals = len(time_diffs)
                    
                    if correct_intervals / total_intervals > 0.8:  # 80% should be correct
                        print(f"✅ Correct intervals: {correct_intervals}/{total_intervals} match {exp_interval}")
                    else:
                        print(f"⚠️  Interval issues: only {correct_intervals}/{total_intervals} match {exp_interval}")
                        print(f"   Sample intervals: {unique_diffs[:3]}")
            
            # Show sample data
            print("Sample data (first 2 rows):")
            print(data.head(2)[['Open', 'High', 'Low', 'Close']].round(2))
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

def test_old_date_validation():
    """Test that old dates are properly rejected for intraday timeframes"""
    print("Testing Old Date Validation")
    print("=" * 30)
    
    # Test with old dates (should fail for intraday)
    old_start = "2022-01-01"  # More than 730 days ago
    old_end = "2022-12-31"
    symbol = "AAPL"
    
    print(f"Testing with old dates: {old_start} to {old_end}")
    print("This should fail for intraday timeframes but work for daily")
    print()
    
    timeframes = ["1h", "4h", "1d"]
    
    for timeframe in timeframes:
        print(f"Testing {timeframe} with old dates:")
        
        try:
            config = TradingConfig()
            adapter = BacktestingAdapter(config, [])
            
            data = adapter.fetch_data(symbol, old_start, old_end, timeframe)
            print(f"✅ Unexpected success: {len(data)} data points (this should only work for daily)")
            
        except ValueError as e:
            if "730 days" in str(e):
                print(f"✅ Correctly rejected: {str(e)[:100]}...")
            else:
                print(f"❌ Different error: {str(e)[:100]}...")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)[:100]}...")
        
        print()

if __name__ == "__main__":
    test_timeframe_fix()
    test_old_date_validation()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("- Recent dates (last 90 days) should work for all timeframes")
    print("- Old dates (2+ years ago) should be rejected for 1h/4h but work for 1d")
    print("- The UI now automatically adjusts date limits based on timeframe")
    print("- Better error messages guide users to fix date range issues")