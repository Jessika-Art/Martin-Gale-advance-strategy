#!/usr/bin/env python3

import sys
import os
import logging
sys.path.append('C:\\Users\\amari\\Desktop\\MartinGales')
sys.path.append('C:\\Users\\amari\\Desktop\\MartinGales\\app')

# Change to the app directory to make relative imports work
os.chdir('C:\\Users\\amari\\Desktop\\MartinGales\\app')

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)

from backtesting_system import BacktestingAdapter
from config import TradingConfig
import json
from ui.config_manager import dict_to_config

def extract_year_end_dates():
    try:
        # Load configuration
        config_file = 'C:\\Users\\amari\\Desktop\\MartinGales\\config_my_64.json'
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        config = dict_to_config(config_dict)
        
        # Create backtesting adapter
        from config import StrategyType
        selected_strategies = [StrategyType.CDM]
        bt_adapter = BacktestingAdapter(config, selected_strategies)
        
        # Track year-end dates
        year_end_dates = []
        
        # Monkey patch to track specific dates
        original_create_combined_strategy = bt_adapter.create_combined_strategy
        
        def create_combined_strategy_with_date_tracking(symbol):
            StrategyClass = original_create_combined_strategy(symbol)
            
            class YearEndTrackingStrategy(StrategyClass):
                def next(self):
                    current_time = self.data.index[-1]
                    current_date = current_time.date()
                    
                    # Track dates around year-end
                    if (current_date.month == 12 and current_date.day >= 28) or \
                       (current_date.month == 1 and current_date.day <= 5):
                        year_end_dates.append(current_date.strftime('%Y-%m-%d'))
                    
                    # Call original next method
                    return super().next()
            
            return YearEndTrackingStrategy
        
        bt_adapter.create_combined_strategy = create_combined_strategy_with_date_tracking
        
        # Run backtest
        print("Running backtest to extract year-end dates...")
        bt, metrics, cycle_report = bt_adapter.run_backtest('AAPL', '2024-04-06', '2025-07-05', '1h', 100000)
        
        # Print year-end dates
        print("\n=== YEAR-END TRANSITION DATES ===")
        unique_dates = sorted(set(year_end_dates))
        for date in unique_dates:
            print(f"Trading date: {date}")
        
        print(f"\nTotal unique year-end dates: {len(unique_dates)}")
        print(f"Total trades: {metrics['# Trades']}")
        print(f"Total cycles: {cycle_report.total_cycles}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_year_end_dates()