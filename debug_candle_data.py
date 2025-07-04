import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import get_yfinance_interval

def test_candle_data_quality():
    """Test and analyze candle data quality for different timeframes"""
    print("=== Testing Candle Data Quality ===")
    
    symbol = "AAPL"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    timeframes = ['1h', '4h', '1d']
    
    for timeframe in timeframes:
        print(f"\n--- Testing {timeframe} timeframe ---")
        
        try:
            # Get yfinance interval
            yf_interval = get_yfinance_interval(timeframe)
            print(f"yfinance interval: {yf_interval}")
            
            # Test with different auto_adjust settings
            for auto_adjust in [True, False]:
                for prepost in [True, False]:
                    print(f"\nTesting auto_adjust={auto_adjust}, prepost={prepost}")
                    
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(
                        start=start_date,
                        end=end_date,
                        interval=yf_interval,
                        auto_adjust=auto_adjust,
                        prepost=prepost
                    )
                    
                    if not data.empty:
                        print(f"Data points: {len(data)}")
                        
                        # Analyze OHLC relationships
                        analyze_ohlc_quality(data, f"{timeframe}_auto{auto_adjust}_pre{prepost}")
                    else:
                        print("No data retrieved")
                        
        except Exception as e:
            print(f"Error testing {timeframe}: {e}")

def analyze_ohlc_quality(data, label):
    """Analyze OHLC data quality and detect anomalies"""
    print(f"\n  Analysis for {label}:")
    
    # Check basic OHLC relationships
    invalid_high = (data['High'] < data['Open']) | (data['High'] < data['Close']) | (data['High'] < data['Low'])
    invalid_low = (data['Low'] > data['Open']) | (data['Low'] > data['Close']) | (data['Low'] > data['High'])
    
    print(f"  Invalid High values: {invalid_high.sum()}")
    print(f"  Invalid Low values: {invalid_low.sum()}")
    
    if invalid_high.any() or invalid_low.any():
        print("  ⚠️  OHLC relationship violations detected!")
        if invalid_high.any():
            print(f"  Invalid High samples:")
            print(data[invalid_high][['Open', 'High', 'Low', 'Close']].head())
        if invalid_low.any():
            print(f"  Invalid Low samples:")
            print(data[invalid_low][['Open', 'High', 'Low', 'Close']].head())
    
    # Check for extreme wicks (high/low vs open/close)
    body_size = abs(data['Close'] - data['Open'])
    upper_wick = data['High'] - data[['Open', 'Close']].max(axis=1)
    lower_wick = data[['Open', 'Close']].min(axis=1) - data['Low']
    
    # Calculate wick-to-body ratios
    upper_wick_ratio = upper_wick / (body_size + 0.0001)  # Avoid division by zero
    lower_wick_ratio = lower_wick / (body_size + 0.0001)
    
    extreme_upper_wicks = upper_wick_ratio > 10  # Upper wick > 10x body size
    extreme_lower_wicks = lower_wick_ratio > 10  # Lower wick > 10x body size
    
    print(f"  Extreme upper wicks (>10x body): {extreme_upper_wicks.sum()}")
    print(f"  Extreme lower wicks (>10x body): {extreme_lower_wicks.sum()}")
    
    if extreme_upper_wicks.any():
        print(f"  Sample extreme upper wicks:")
        extreme_data = data[extreme_upper_wicks][['Open', 'High', 'Low', 'Close']].head(3)
        for idx, row in extreme_data.iterrows():
            body = abs(row['Close'] - row['Open'])
            wick = row['High'] - max(row['Open'], row['Close'])
            ratio = wick / (body + 0.0001)
            print(f"    {idx}: O={row['Open']:.2f} H={row['High']:.2f} L={row['Low']:.2f} C={row['Close']:.2f} (wick/body: {ratio:.1f}x)")
    
    if extreme_lower_wicks.any():
        print(f"  Sample extreme lower wicks:")
        extreme_data = data[extreme_lower_wicks][['Open', 'High', 'Low', 'Close']].head(3)
        for idx, row in extreme_data.iterrows():
            body = abs(row['Close'] - row['Open'])
            wick = min(row['Open'], row['Close']) - row['Low']
            ratio = wick / (body + 0.0001)
            print(f"    {idx}: O={row['Open']:.2f} H={row['High']:.2f} L={row['Low']:.2f} C={row['Close']:.2f} (wick/body: {ratio:.1f}x)")
    
    # Price range analysis
    price_range = data['High'] - data['Low']
    avg_range = price_range.mean()
    extreme_ranges = price_range > (avg_range * 5)  # Ranges > 5x average
    
    print(f"  Average price range: {avg_range:.2f}")
    print(f"  Extreme ranges (>5x avg): {extreme_ranges.sum()}")
    
    if extreme_ranges.any():
        print(f"  Sample extreme ranges:")
        extreme_data = data[extreme_ranges][['Open', 'High', 'Low', 'Close']].head(3)
        for idx, row in extreme_data.iterrows():
            range_val = row['High'] - row['Low']
            ratio = range_val / avg_range
            print(f"    {idx}: Range={range_val:.2f} ({ratio:.1f}x avg) O={row['Open']:.2f} H={row['High']:.2f} L={row['Low']:.2f} C={row['Close']:.2f}")

def test_backtesting_system_data():
    """Test the actual data retrieval from backtesting system"""
    print("\n=== Testing Backtesting System Data Retrieval ===")
    
    try:
        from backtesting_system import BacktestingAdapter
        from config import TradingConfig, StrategyType
        
        # Create minimal config
        config = TradingConfig()
        adapter = BacktestingAdapter(config, [StrategyType.CDM])
        
        symbol = "AAPL"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for timeframe in ['1h', '4h', '1d']:
            print(f"\n--- Backtesting System: {timeframe} ---")
            
            try:
                data = adapter.fetch_data(symbol, start_date, end_date, timeframe)
                print(f"Retrieved {len(data)} data points")
                
                # Analyze the data
                analyze_ohlc_quality(data, f"BacktestSystem_{timeframe}")
                
            except Exception as e:
                print(f"Error with {timeframe}: {e}")
                
    except Exception as e:
        print(f"Error testing backtesting system: {e}")

if __name__ == "__main__":
    test_candle_data_quality()
    test_backtesting_system_data()
    
    print("\n=== Analysis Complete ===")
    print("\nRecommendations:")
    print("1. If extreme wicks are found, consider using auto_adjust=False")
    print("2. If prepost=True causes issues, try prepost=False")
    print("3. Check if the data source has known issues with intraday data")
    print("4. Consider data validation and filtering in the backtesting system")