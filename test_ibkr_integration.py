#!/usr/bin/env python3
"""
Test Script: IBKR Integration Verification

This script tests the IBKR integration without running a full backtest.
Use this to verify that your IBKR connection and data fetching works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ibkr_historical_data import IBKRDataProvider, fetch_ibkr_data
import logging
from datetime import datetime, timedelta

def test_ibkr_connection():
    """Test basic IBKR connection"""
    print("=== Testing IBKR Connection ===")
    
    try:
        provider = IBKRDataProvider()
        provider.connect()
        print("✅ Successfully connected to IBKR")
        
        # Test if connection is active
        if provider.client and provider.client.is_connected:
            print("✅ Connection is active")
        else:
            print("❌ Connection appears inactive")
            
        provider.disconnect()
        print("✅ Successfully disconnected")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure TWS or IB Gateway is running and API is enabled")
        return False

def test_data_fetching():
    """Test historical data fetching"""
    print("\n=== Testing Data Fetching ===")
    
    try:
        # Test with a recent date range (last 30 days)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"Fetching AAPL data from {start_date} to {end_date}")
        
        data = fetch_ibkr_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            interval="1h"
        )
        
        if not data.empty:
            print(f"✅ Successfully fetched {len(data)} data points")
            print(f"✅ Data columns: {list(data.columns)}")
            print(f"✅ Date range: {data.index[0]} to {data.index[-1]}")
            print(f"✅ Sample data:")
            print(data.head(3))
            return True
        else:
            print("❌ No data returned")
            return False
            
    except Exception as e:
        print(f"❌ Data fetching failed: {e}")
        return False

def test_backtesting_integration():
    """Test integration with backtesting system"""
    print("\n=== Testing Backtesting Integration ===")
    
    try:
        from app.backtesting_system import BacktestingSystem
        from app.config import TradingConfig
        from app.strategies.strategy_types import StrategyType
        
        # Create minimal config
        config = TradingConfig()
        selected_strategies = [StrategyType.MARTINGALE_RSI]
        
        # Initialize backtesting system
        backtester = BacktestingSystem(config, selected_strategies)
        
        # Test data fetching through backtesting system
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        print(f"Testing backtesting system data fetch for {start_date} to {end_date}")
        
        data = backtester.fetch_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            interval="1h",
            use_ibkr=True
        )
        
        if not data.empty:
            print(f"✅ Backtesting system successfully fetched {len(data)} data points")
            print(f"✅ Data validation passed")
            return True
        else:
            print("❌ Backtesting system returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Backtesting integration failed: {e}")
        return False

def main():
    """Run all tests"""
    print("IBKR Integration Test Suite")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    tests = [
        ("Connection Test", test_ibkr_connection),
        ("Data Fetching Test", test_data_fetching),
        ("Backtesting Integration Test", test_backtesting_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! IBKR integration is working correctly.")
        print("You can now use use_ibkr=True in your backtesting calls.")
    else:
        print("\n⚠️  Some tests failed. Please check your IBKR setup:")
        print("1. Ensure TWS or IB Gateway is running")
        print("2. Enable API connections in TWS/Gateway settings")
        print("3. Check your market data permissions")
        print("4. Verify network connectivity")

if __name__ == "__main__":
    main()