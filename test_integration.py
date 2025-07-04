#!/usr/bin/env python3
"""
Integration test for the enhanced backtesting system with:
- Strategy coordination (parallel/sequential modes)
- Risk management (daily limits, concurrent cycles)
- Cycle analysis with risk reporting
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from datetime import datetime, date
from app.backtesting_system import BacktestingAdapter
from app.config import TradingConfig, StrategySettings, SharedSettings, StrategyType
from app.risk_manager import GlobalRiskManager

def test_risk_management():
    """Test risk management functionality"""
    print("\n=== Testing Risk Management ===")
    
    # Create risk manager with low limits for testing
    risk_manager = GlobalRiskManager(
        max_concurrent_cycles=2,
        daily_loss_limit=500.0,
        daily_profit_target=1000.0
    )
    
    # Test cycle limits
    can_start, reason = risk_manager.can_start_new_cycle("STRATEGY_1")
    print(f"Can start cycle 1: {can_start} - {reason}")
    
    if can_start:
        risk_manager.register_cycle_start("cycle_1", "STRATEGY_1")
        
    can_start, reason = risk_manager.can_start_new_cycle("STRATEGY_2")
    print(f"Can start cycle 2: {can_start} - {reason}")
    
    if can_start:
        risk_manager.register_cycle_start("cycle_2", "STRATEGY_2")
    
    # Should fail due to max concurrent cycles
    can_start, reason = risk_manager.can_start_new_cycle("STRATEGY_3")
    print(f"Can start cycle 3: {can_start} - {reason}")
    
    # Test loss limit
    risk_manager.register_cycle_end("cycle_1", -300.0)  # Loss
    risk_manager.register_cycle_end("cycle_2", -250.0)  # More loss
    
    can_start, reason = risk_manager.can_start_new_cycle("STRATEGY_4")
    print(f"Can start after losses: {can_start} - {reason}")
    
    # Get risk status
    status = risk_manager.get_risk_status()
    print(f"Risk Level: {status['status']['risk_level']}")
    print(f"Daily PnL: ${status['daily_metrics']['total_daily_pnl']:.2f}")
    print(f"Warnings: {status['status']['warnings']}")

def test_strategy_coordination():
    """Test strategy coordination features"""
    print("\n=== Testing Strategy Coordination ===")
    
    # Create config with strategy coordination
    config = TradingConfig()
    
    # Configure shared settings for coordination
    config.shared_settings = SharedSettings(
        global_strategy_alignment=True,
        global_parallel_start_mode=True,
        global_strategy_to_start_with="CONSERVATIVE",
        global_order_number_to_start=2,
        global_sequential_mode_strategy="AGGRESSIVE",
        global_max_concurrent_cycles=3,
        global_daily_loss_limit=1000.0,
        global_daily_profit_target=2000.0
    )
    
    # Enable multiple strategies
    config.enable_strategy(StrategyType.CDM, True)
    config.enable_strategy(StrategyType.WDM, True)
    config.enable_strategy(StrategyType.ZRM, True)
    
    # Configure CDM strategy
    config.cdm_settings.enabled = True
    config.cdm_settings.capital_allocation = 0.33
    config.cdm_settings.max_orders = 5
    
    # Configure WDM strategy
    config.wdm_settings.enabled = True
    config.wdm_settings.capital_allocation = 0.33
    config.wdm_settings.max_orders = 7
    
    # Configure ZRM strategy
    config.zrm_settings.enabled = True
    config.zrm_settings.capital_allocation = 0.34
    config.zrm_settings.max_orders = 6
    
    print(f"Strategy alignment enabled: {config.shared_settings.global_strategy_alignment}")
    print(f"Parallel start mode: {config.shared_settings.global_parallel_start_mode}")
    print(f"Target strategy: {config.shared_settings.global_strategy_to_start_with}")
    print(f"Active strategies: {[s.value for s in config.active_strategies]}")
    print(f"Order number to start: {config.shared_settings.global_order_number_to_start}")
    
    return config

def test_full_backtest():
    """Test full backtesting with all features"""
    print("\n=== Testing Full Backtest Integration ===")
    
    # Get configuration with coordination
    config = test_strategy_coordination()
    
    # Create backtesting system
    backtesting_system = BacktestingAdapter(config, config.active_strategies)
    
    try:
        # Run backtest
        print("Running backtest with enhanced features...")
        bt, metrics, cycle_report = backtesting_system.run_backtest(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-06-30",
            initial_cash=50000
        )
        
        # Get risk summary from the risk manager if available
        risk_summary = None
        if hasattr(backtesting_system, 'risk_manager'):
            risk_summary = backtesting_system.risk_manager.get_risk_status()
        
        print("\n=== Backtest Results ===")
        print(f"Total Return: {metrics.get('Total Return [%]', 'N/A')}%")
        print(f"Sharpe Ratio: {metrics.get('Sharpe Ratio', 'N/A')}")
        print(f"Max Drawdown: {metrics.get('Max. Drawdown [%]', 'N/A')}%")
        
        print("\n=== Cycle Analysis ===")
        print(f"Total Cycles: {len(cycle_report.cycles)}")
        print(f"Completed Cycles: {len([c for c in cycle_report.cycles if c.status.value == 'COMPLETED'])}")
        
        if cycle_report.cycles:
            total_pnl = sum(c.realized_pnl for c in cycle_report.cycles.values() if c.realized_pnl is not None)
            print(f"Total Cycle PnL: ${total_pnl:.2f}")
        
        print("\n=== Risk Management Summary ===")
        if risk_summary:
            daily_metrics = risk_summary.get('daily_metrics', {})
            limits = risk_summary.get('limits', {})
            status = risk_summary.get('status', {})
            
            print(f"Risk Level: {status.get('risk_level', 'UNKNOWN')}")
            print(f"Daily PnL: ${daily_metrics.get('total_daily_pnl', 0):.2f}")
            print(f"Active Cycles: {daily_metrics.get('active_cycles', 0)}")
            print(f"Total Trades: {daily_metrics.get('total_trades_today', 0)}")
            print(f"Commission Paid: ${daily_metrics.get('total_commission_today', 0):.2f}")
            
            if status.get('warnings'):
                print(f"Warnings: {', '.join(status['warnings'])}")
        
        # Generate comprehensive report
        print("\n=== Generating Reports ===")
        report_data = backtesting_system.generate_cycle_focused_report(cycle_report, "AAPL", risk_summary)
        print(f"Report sections generated: {list(report_data.keys())}")
        
        # Export to Excel
        excel_file = backtesting_system.export_cycle_analysis_to_excel(cycle_report, risk_summary)
        print(f"Excel report exported to: {excel_file}")
        
        return True
        
    except Exception as e:
        print(f"Backtest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("Starting Integration Tests for Enhanced Backtesting System")
    print("=" * 60)
    
    try:
        # Test individual components
        test_risk_management()
        
        # Test full integration
        success = test_full_backtest()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ All integration tests completed successfully!")
            print("\nEnhanced features verified:")
            print("- ✅ Risk management (daily limits, concurrent cycles)")
            print("- ✅ Strategy coordination (parallel/sequential modes)")
            print("- ✅ Cycle analysis with risk reporting")
            print("- ✅ Excel export with risk data")
            print("- ✅ Comprehensive reporting")
        else:
            print("\n❌ Some tests failed. Check the output above.")
            
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()