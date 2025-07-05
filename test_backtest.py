#!/usr/bin/env python3

import sys
import os
sys.path.append('C:\\Users\\amari\\Desktop\\MartinGales')
sys.path.append('C:\\Users\\amari\\Desktop\\MartinGales\\app')

# Change to the app directory to make relative imports work
os.chdir('C:\\Users\\amari\\Desktop\\MartinGales\\app')

from backtesting_system import BacktestingAdapter
from config import TradingConfig
import json
from ui.config_manager import dict_to_config

def test_backtest():
    try:
        # Load configuration from JSON file
        config_file = 'C:\\Users\\amari\\Desktop\\MartinGales\\config_my_64.json'
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        config = dict_to_config(config_dict)
        
        # Create backtesting adapter
        from config import StrategyType
        selected_strategies = [StrategyType.CDM]  # Only CDM is enabled
        bt_adapter = BacktestingAdapter(config, selected_strategies)
        
        # Run backtest (using recent dates for 1h data)
        bt, metrics, cycle_report = bt_adapter.run_backtest('AAPL', '2024-01-01', '2024-12-01', '1h', 100000)
        
        # Print results
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Total Trades: {metrics['# Trades']}")
        print(f"Total Cycles: {cycle_report.total_cycles}")
        print(f"Completed Cycles: {cycle_report.completed_cycles}")
        print(f"Win Rate: {metrics['Win Rate [%]']}%")
        print(f"Final Equity: ${metrics['Equity Final [$]']:,.2f}")
        print(f"Return: {metrics['Return [%]']}%")
        print(f"Max Drawdown: {metrics['Max. Drawdown [%]']}%")
        
        if cycle_report.total_cycles > 0:
            print(f"\n=== CYCLE ANALYSIS ===")
            print(f"Average Cycle PnL: ${cycle_report.average_cycle_pnl:.2f}")
            print(f"Best Cycle PnL: ${cycle_report.best_cycle_pnl:.2f}")
            print(f"Worst Cycle PnL: ${cycle_report.worst_cycle_pnl:.2f}")
            print(f"Total Realized PnL: ${cycle_report.total_realized_pnl:.2f}")
        
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backtest()