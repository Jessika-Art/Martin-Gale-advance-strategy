#!/usr/bin/env python3

import sys
import os
import logging
sys.path.append('C:\\Users\\amari\\Desktop\\MartinGales')
sys.path.append('C:\\Users\\amari\\Desktop\\MartinGales\\app')

# Change to the app directory to make relative imports work
os.chdir('C:\\Users\\amari\\Desktop\\MartinGales\\app')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

from backtesting_system import BacktestingAdapter
from config import TradingConfig
import json
from ui.config_manager import dict_to_config

def test_both_configs():
    configs = [
        'C:\\Users\\amari\\Desktop\\MartinGales\\config_my_64.json',
        'C:\\Users\\amari\\Desktop\\MartinGales\\config_test.json'
    ]
    
    for config_file in configs:
        print(f"\n{'='*60}")
        print(f"TESTING CONFIG: {os.path.basename(config_file)}")
        print(f"{'='*60}")
        
        try:
            # Load configuration from JSON file
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            config = dict_to_config(config_dict)
            
            # Create backtesting adapter
            from config import StrategyType
            selected_strategies = [StrategyType.CDM]  # Only CDM is enabled
            bt_adapter = BacktestingAdapter(config, selected_strategies)
            
            # Monkey patch to track dates
            original_create_combined_strategy = bt_adapter.create_combined_strategy
            
            def create_combined_strategy_with_logging(symbol):
                StrategyClass = original_create_combined_strategy(symbol)
                
                class DateTrackingStrategy(StrategyClass):
                    def next(self):
                        current_time = self.data.index[-1]
                        
                        # Log date changes
                        if not hasattr(self, '_last_date') or current_time.date() != self._last_date:
                            print(f"\n=== BACKTEST DATE: {current_time.date()} - {current_time.strftime('%Y-%m-%d %H:%M')} ===")
                            self._last_date = current_time.date()
                            
                            # Check if we're past 2024-12-31
                            if current_time.date().year >= 2025:
                                print(f"*** ENTERED 2025: {current_time.date()} ***")
                        
                        # Call original next method
                        return super().next()
                
                return DateTrackingStrategy
            
            bt_adapter.create_combined_strategy = create_combined_strategy_with_logging
            
            # Run backtest
            bt, metrics, cycle_report = bt_adapter.run_backtest('AAPL', '2024-04-06', '2025-07-05', '1h', 100000)
            
            # Print results
            print(f"\n=== BACKTEST RESULTS FOR {os.path.basename(config_file)} ===")
            print(f"Total Trades: {metrics['# Trades']}")
            print(f"Total Cycles: {cycle_report.total_cycles}")
            print(f"Final Equity: ${metrics['Equity Final [$]']:,.2f}")
            print(f"Return: {metrics['Return [%]']}%")
            
        except Exception as e:
            print(f"Error running backtest with {config_file}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_both_configs()