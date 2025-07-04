#!/usr/bin/env python3
"""
Shared Settings Implementation Demo

This script demonstrates the new SharedSettings functionality implemented
for the Multi-Martingales Trading Bot. It shows how to:

1. Create and configure shared settings
2. Validate configuration parameters
3. Manage risk settings
4. Control strategy coordination
5. Set up advanced position sizing
6. Enable trailing stops and emergency exits
"""

import sys
import os
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.control_panel import ControlPanel
from app.config import StrategyType, ExecutionMode

def demo_basic_shared_settings():
    """Demonstrate basic shared settings configuration"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Shared Settings Configuration")
    print("="*60)
    
    # Create control panel and load/create configuration
    panel = ControlPanel("demo_shared_settings.json")
    config = panel.load_config()
    
    if not config:
        print("Creating new configuration...")
        config = panel.create_default_config("demo")
        panel.config = config
    
    # Display current shared settings
    print("\nCurrent Shared Settings Summary:")
    summary = panel.get_shared_settings_summary()
    
    if 'error' in summary:
        print(f"Error: {summary['error']}")
    else:
        for category, settings in summary.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {settings}")
    
    # Validate configuration
    print("\nConfiguration Validation:")
    errors = panel.validate_configuration()
    if errors:
        print("Validation Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration is valid")
    
    return panel

def demo_risk_management(panel: ControlPanel):
    """Demonstrate risk management settings"""
    print("\n" + "="*60)
    print("DEMO 2: Risk Management Configuration")
    print("="*60)
    
    # Update risk management settings
    print("\nUpdating risk management settings...")
    success = panel.update_risk_management(
        daily_loss_limit=500.0,
        daily_profit_target=1000.0,
        max_drawdown_pct=8.0,
        max_concurrent_cycles=3
    )
    
    if success:
        print("✓ Risk management settings updated successfully")
    else:
        print("✗ Failed to update risk management settings")
    
    # Check risk status
    print("\nRisk Status Check:")
    risk_status = panel.get_risk_status(current_loss=200.0, current_drawdown_pct=3.0)
    for key, value in risk_status.items():
        print(f"  {key}: {value}")
    
    # Test emergency conditions
    print("\nTesting Emergency Conditions:")
    emergency_status = panel.get_risk_status(current_loss=600.0, current_drawdown_pct=12.0)
    for key, value in emergency_status.items():
        print(f"  {key}: {value}")

def demo_strategy_coordination(panel: ControlPanel):
    """Demonstrate strategy coordination settings"""
    print("\n" + "="*60)
    print("DEMO 3: Strategy Coordination")
    print("="*60)
    
    # Enable strategy coordination
    print("\nEnabling strategy coordination...")
    success = panel.enable_strategy_coordination(
        enabled=True,
        alignment="SEQUENTIAL",
        start_strategy="CDM"
    )
    
    if success:
        print("✓ Strategy coordination enabled")
    else:
        print("✗ Failed to enable strategy coordination")
    
    # Enable multiple strategies
    print("\nEnabling multiple strategies for coordination...")
    panel.enable_strategy("CDM", True)
    panel.enable_strategy("WDM", True)
    panel.enable_strategy("ZRM", True)
    
    # Test coordination methods
    if panel.config:
        print("\nStrategy Coordination Status:")
        print(f"  Coordination Enabled: {panel.config.is_strategy_coordination_enabled()}")
        
        # Test sequential mode
        next_strategy = panel.config.get_next_strategy_in_sequence(StrategyType.CDM)
        if next_strategy:
            print(f"  Next Strategy after CDM: {next_strategy.value}")
        
        # Test strategy priorities
        for strategy in [StrategyType.CDM, StrategyType.WDM, StrategyType.ZRM]:
            priority = panel.config.get_strategy_start_priority(strategy)
            print(f"  {strategy.value} Priority: {priority}")

def demo_position_sizing(panel: ControlPanel):
    """Demonstrate advanced position sizing"""
    print("\n" + "="*60)
    print("DEMO 4: Advanced Position Sizing")
    print("="*60)
    
    # Test different position sizing methods
    sizing_configs = [
        {"size_unit": "PERCENTAGE", "percentage": 2.5, "enable_dynamic": False},
        {"size_unit": "USD", "fixed_size": 1000.0, "enable_dynamic": False},
        {"size_unit": "SHARES", "fixed_size": 100.0, "enable_dynamic": False},
        {"size_unit": "PERCENTAGE", "percentage": 3.0, "enable_dynamic": True, "dynamic_factor": 1.5}
    ]
    
    for i, config in enumerate(sizing_configs, 1):
        print(f"\nTesting Position Sizing Configuration {i}:")
        success = panel.update_position_sizing_advanced(**config)
        
        if success and panel.config:
            # Test position size calculation
            account_balance = 50000.0
            symbol_price = 150.0
            
            for strategy in [StrategyType.CDM, StrategyType.WDM]:
                position_size = panel.config.get_effective_position_size_for_strategy(
                    strategy, account_balance, symbol_price
                )
                print(f"  {strategy.value} Position Size: {position_size:.2f} shares")
                print(f"  {strategy.value} Dollar Value: ${position_size * symbol_price:.2f}")

def demo_trailing_stops(panel: ControlPanel):
    """Demonstrate trailing stops configuration"""
    print("\n" + "="*60)
    print("DEMO 5: Trailing Stops Configuration")
    print("="*60)
    
    # Enable trailing stops
    print("\nEnabling global trailing stops...")
    success = panel.enable_trailing_stops(
        enabled=True,
        trailing_pct=1.5,
        activation_pct=0.8
    )
    
    if success:
        print("✓ Trailing stops enabled")
    else:
        print("✗ Failed to enable trailing stops")
    
    # Update additional trailing stop settings
    print("\nUpdating trailing stop frequency...")
    panel.update_shared_settings(
        trailing_stop_update_frequency_seconds=15
    )
    
    # Display current trailing stop configuration
    summary = panel.get_shared_settings_summary()
    trailing_config = summary.get('trailing_stops', {})
    print("\nTrailing Stops Configuration:")
    for key, value in trailing_config.items():
        print(f"  {key}: {value}")

def demo_comprehensive_configuration(panel: ControlPanel):
    """Demonstrate comprehensive configuration setup"""
    print("\n" + "="*60)
    print("DEMO 6: Comprehensive Configuration")
    print("="*60)
    
    # Set up a comprehensive trading configuration
    print("\nSetting up comprehensive configuration...")
    
    # Update multiple shared settings at once
    comprehensive_updates = {
        # Trading settings
        'continue_trading': True,
        'money_management': True,
        'initial_balance': 100000.0,
        
        # Strategy coordination
        'enable_strategy_coordination': True,
        'global_strategy_alignment': 'PARALLEL',
        'global_parallel_start_mode': True,
        
        # Position sizing
        'global_position_size_unit': 'PERCENTAGE',
        'global_percentage_of_balance': 4.0,
        'enable_dynamic_sizing': True,
        'dynamic_sizing_factor': 1.2,
        
        # Risk management
        'enable_daily_limits': True,
        'global_daily_loss_limit': 800.0,
        'global_daily_profit_target': 1500.0,
        'enable_drawdown_protection': True,
        'max_portfolio_drawdown_pct': 7.0,
        'global_max_concurrent_cycles': 4,
        
        # Trailing stops
        'enable_global_trailing_stops': True,
        'global_trailing_stop_pct': 2.0,
        'global_trailing_activation_pct': 1.0,
        
        # Emergency exit
        'enable_emergency_exit': True,
        'emergency_loss_threshold_pct': 12.0,
        
        # Trading hours
        'enable_trading_hours_restriction': True,
        'trading_start_time': '09:30',
        'trading_end_time': '15:30',
        
        # Order management
        'enable_order_timeout': True,
        'order_timeout_minutes': 45,
        'max_pending_orders_per_strategy': 8
    }
    
    success = panel.update_shared_settings(**comprehensive_updates)
    
    if success:
        print("✓ Comprehensive configuration applied successfully")
    else:
        print("✗ Failed to apply comprehensive configuration")
    
    # Validate the final configuration
    print("\nFinal Configuration Validation:")
    errors = panel.validate_configuration()
    if errors:
        print("Validation Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Final configuration is valid")
    
    # Save the configuration
    print("\nSaving configuration...")
    if panel.save_config(panel.config, "comprehensive_shared_settings.json"):
        print("✓ Configuration saved to 'comprehensive_shared_settings.json'")
    else:
        print("✗ Failed to save configuration")

def main():
    """Run all shared settings demos"""
    print("Multi-Martingales Trading Bot - Shared Settings Implementation Demo")
    print("This demo showcases the new SharedSettings functionality")
    
    try:
        # Run all demos
        panel = demo_basic_shared_settings()
        demo_risk_management(panel)
        demo_strategy_coordination(panel)
        demo_position_sizing(panel)
        demo_trailing_stops(panel)
        demo_comprehensive_configuration(panel)
        
        # Final status display
        print("\n" + "="*60)
        print("FINAL STATUS")
        print("="*60)
        panel.print_status()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nThe SharedSettings implementation provides:")
        print("✓ Comprehensive global configuration management")
        print("✓ Advanced risk management controls")
        print("✓ Strategy coordination capabilities")
        print("✓ Flexible position sizing options")
        print("✓ Global trailing stops functionality")
        print("✓ Emergency exit conditions")
        print("✓ Configuration validation")
        print("✓ Real-time settings updates")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()