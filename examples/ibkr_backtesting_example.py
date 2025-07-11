#!/usr/bin/env python3
"""
Example: Using IBKR for Backtesting Instead of Yahoo Finance

This example demonstrates how to switch from Yahoo Finance to Interactive Brokers
for historical data retrieval in backtesting.

Prerequisites:
1. TWS or IB Gateway running and connected
2. Valid IBKR account with market data permissions
3. Configure IBKR connection settings in config.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.backtesting_system import BacktestingSystem
from app.config import BacktestConfig
import logging

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create backtesting configuration
    config = BacktestConfig(
        initial_capital=100000,
        commission=0.001,  # 0.1% commission
        slippage=0.0005,   # 0.05% slippage
        max_risk_per_trade=0.02,  # 2% risk per trade
        max_portfolio_risk=0.10,  # 10% total portfolio risk
        stop_loss_pct=0.05,       # 5% stop loss
        take_profit_pct=0.10      # 10% take profit
    )
    
    # Initialize backtesting system
    backtester = BacktestingSystem(config)
    
    # Example 1: Using Yahoo Finance (default behavior)
    logger.info("=== Example 1: Using Yahoo Finance ===")
    try:
        yf_data = backtester.fetch_data(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-02-01",
            interval="1h",
            use_ibkr=False  # Use Yahoo Finance
        )
        logger.info(f"Yahoo Finance data shape: {yf_data.shape}")
        logger.info(f"Yahoo Finance data columns: {list(yf_data.columns)}")
        logger.info(f"Yahoo Finance data date range: {yf_data.index[0]} to {yf_data.index[-1]}")
    except Exception as e:
        logger.error(f"Yahoo Finance fetch failed: {e}")
    
    # Example 2: Using Interactive Brokers
    logger.info("\n=== Example 2: Using Interactive Brokers ===")
    try:
        ibkr_data = backtester.fetch_data(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-02-01",
            interval="1h",
            use_ibkr=True  # Use IBKR
        )
        logger.info(f"IBKR data shape: {ibkr_data.shape}")
        logger.info(f"IBKR data columns: {list(ibkr_data.columns)}")
        logger.info(f"IBKR data date range: {ibkr_data.index[0]} to {ibkr_data.index[-1]}")
    except Exception as e:
        logger.error(f"IBKR fetch failed: {e}")
        logger.info("Make sure TWS/IB Gateway is running and connected")
    
    # Example 3: Running a backtest with IBKR data
    logger.info("\n=== Example 3: Running Backtest with IBKR Data ===")
    try:
        # Select strategies for backtesting
        selected_strategies = ['martingale_rsi', 'martingale_macd']
        
        # Run backtest with IBKR data
        bt, metrics, cycle_report = backtester.run_backtest(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-02-01",
            interval="1h",
            use_ibkr=True  # Use IBKR for data fetching
        )
        
        logger.info("Backtest completed successfully with IBKR data")
        logger.info(f"Final portfolio value: ${metrics.get('Equity Final [$]', 'N/A')}")
        logger.info(f"Total return: {metrics.get('Return [%]', 'N/A')}%")
        logger.info(f"Number of trades: {metrics.get('# Trades', 'N/A')}")
        logger.info(f"Win rate: {metrics.get('Win Rate [%]', 'N/A')}%")
        
    except Exception as e:
        logger.error(f"Backtest with IBKR data failed: {e}")
    
    logger.info("\n=== Migration Guide ===")
    logger.info("To migrate from Yahoo Finance to IBKR:")
    logger.info("1. Ensure TWS or IB Gateway is running")
    logger.info("2. Configure IBKR settings in config.py")
    logger.info("3. Add use_ibkr=True parameter to fetch_data() calls")
    logger.info("4. Update run_backtest() method to support use_ibkr parameter")
    logger.info("5. Test with small date ranges first")

if __name__ == "__main__":
    main()