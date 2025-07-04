import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from backtesting_system import BacktestingAdapter
from config import TradingConfig, StrategyType

def test_candle_fix():
    """Test the fixed candle data retrieval"""
    print("=== Testing Fixed Candle Data Retrieval ===")
    
    # Create backtesting adapter
    config = TradingConfig()
    adapter = BacktestingAdapter(config, [StrategyType.CDM])
    
    symbol = "AAPL"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    timeframes = ['1h', '4h', '1d']
    
    for timeframe in timeframes:
        print(f"\n--- Testing {timeframe} timeframe ---")
        
        try:
            # Test with fixed backtesting system
            data = adapter.fetch_data(symbol, start_date, end_date, timeframe)
            print(f"Retrieved {len(data)} data points")
            
            # Analyze the cleaned data
            analyze_cleaned_data(data, timeframe)
            
        except Exception as e:
            print(f"Error with {timeframe}: {e}")

def analyze_cleaned_data(data, timeframe):
    """Analyze the cleaned candle data quality"""
    print(f"\n  Analysis for cleaned {timeframe} data:")
    
    # Check basic OHLC relationships
    invalid_high = (data['High'] < data['Open']) | (data['High'] < data['Close']) | (data['High'] < data['Low'])
    invalid_low = (data['Low'] > data['Open']) | (data['Low'] > data['Close']) | (data['Low'] > data['High'])
    
    print(f"  Invalid High values: {invalid_high.sum()}")
    print(f"  Invalid Low values: {invalid_low.sum()}")
    
    # Check for extreme wicks
    body_size = abs(data['Close'] - data['Open'])
    upper_wick = data['High'] - data[['Open', 'Close']].max(axis=1)
    lower_wick = data[['Open', 'Close']].min(axis=1) - data['Low']
    
    # Calculate wick-to-body ratios
    min_body_size = 0.01
    effective_body_size = body_size.where(body_size >= min_body_size, min_body_size)
    upper_wick_ratio = upper_wick / effective_body_size
    lower_wick_ratio = lower_wick / effective_body_size
    
    # Define thresholds based on timeframe
    if timeframe in ['1m', '5m', '15m', '30m']:
        max_wick_ratio = 20
    elif timeframe in ['1h', '2h', '4h']:
        max_wick_ratio = 15
    else:
        max_wick_ratio = 10
    
    extreme_upper_wicks = upper_wick_ratio > max_wick_ratio
    extreme_lower_wicks = lower_wick_ratio > max_wick_ratio
    
    print(f"  Extreme upper wicks (>{max_wick_ratio}x body): {extreme_upper_wicks.sum()}")
    print(f"  Extreme lower wicks (>{max_wick_ratio}x body): {extreme_lower_wicks.sum()}")
    
    # Price range analysis
    price_range = data['High'] - data['Low']
    median_range = price_range.median()
    extreme_ranges = price_range > (median_range * 8)
    
    print(f"  Median price range: {median_range:.2f}")
    print(f"  Extreme ranges (>8x median): {extreme_ranges.sum()}")
    
    # Show some sample candles
    print(f"\n  Sample candles:")
    sample_data = data.head(5)
    for idx, row in sample_data.iterrows():
        body = abs(row['Close'] - row['Open'])
        u_wick = row['High'] - max(row['Open'], row['Close'])
        l_wick = min(row['Open'], row['Close']) - row['Low']
        u_ratio = u_wick / max(body, min_body_size)
        l_ratio = l_wick / max(body, min_body_size)
        print(f"    {idx}: O={row['Open']:.2f} H={row['High']:.2f} L={row['Low']:.2f} C={row['Close']:.2f} "
              f"(U:{u_ratio:.1f}x L:{l_ratio:.1f}x)")
    
    # Quality score
    total_issues = invalid_high.sum() + invalid_low.sum() + extreme_upper_wicks.sum() + extreme_lower_wicks.sum() + extreme_ranges.sum()
    quality_score = max(0, 100 - (total_issues / len(data) * 100))
    print(f"\n  Data Quality Score: {quality_score:.1f}% (0 issues = 100%)")
    
    if quality_score >= 95:
        print(f"  ✅ Excellent data quality!")
    elif quality_score >= 85:
        print(f"  ✅ Good data quality")
    elif quality_score >= 70:
        print(f"  ⚠️  Acceptable data quality")
    else:
        print(f"  ❌ Poor data quality - may need further investigation")

def compare_before_after():
    """Compare data quality before and after the fix"""
    print("\n=== Comparing Before/After Fix ===")
    
    symbol = "AAPL"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    from config import get_yfinance_interval
    
    for timeframe in ['1h', '4h']:
        print(f"\n--- {timeframe} Comparison ---")
        
        try:
            yf_interval = get_yfinance_interval(timeframe)
            
            # Before fix (with prepost=True)
            ticker = yf.Ticker(symbol)
            data_before = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=True
            )
            
            # After fix (with prepost=False)
            data_after = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=False
            )
            
            print(f"  Before fix (prepost=True): {len(data_before)} candles")
            print(f"  After fix (prepost=False): {len(data_after)} candles")
            
            # Count extreme wicks in both datasets
            def count_extreme_wicks(data, threshold=15):
                if data.empty:
                    return 0
                body_size = abs(data['Close'] - data['Open'])
                upper_wick = data['High'] - data[['Open', 'Close']].max(axis=1)
                lower_wick = data[['Open', 'Close']].min(axis=1) - data['Low']
                
                min_body_size = 0.01
                effective_body_size = body_size.where(body_size >= min_body_size, min_body_size)
                upper_wick_ratio = upper_wick / effective_body_size
                lower_wick_ratio = lower_wick / effective_body_size
                
                extreme_wicks = (upper_wick_ratio > threshold) | (lower_wick_ratio > threshold)
                return extreme_wicks.sum()
            
            extreme_before = count_extreme_wicks(data_before)
            extreme_after = count_extreme_wicks(data_after)
            
            print(f"  Extreme wicks before: {extreme_before}")
            print(f"  Extreme wicks after: {extreme_after}")
            print(f"  Improvement: {extreme_before - extreme_after} fewer extreme wicks")
            
            if extreme_after < extreme_before:
                improvement_pct = ((extreme_before - extreme_after) / max(extreme_before, 1)) * 100
                print(f"  ✅ {improvement_pct:.1f}% reduction in extreme wicks")
            
        except Exception as e:
            print(f"  Error comparing {timeframe}: {e}")

if __name__ == "__main__":
    test_candle_fix()
    compare_before_after()
    
    print("\n=== Summary ===")
    print("✅ Fixed prepost=False to exclude pre/post market data")
    print("✅ Added data validation to filter extreme wicks")
    print("✅ Added adaptive thresholds based on timeframe")
    print("✅ Improved logging for data quality issues")
    print("\nThe backtesting system should now provide more realistic candle data!")