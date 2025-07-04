#!/usr/bin/env python3
"""
Test script to verify conf.json position sizing calculation
"""

import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from config import TradingConfig, StrategyType
from app.ui.config_manager import dict_to_config

def test_position_sizing():
    """Test position sizing calculation with conf.json"""
    
    # Load conf.json
    with open('conf.json', 'r') as f:
        config_dict = json.load(f)
    
    print("=== Configuration Analysis ===")
    print(f"Account Type: {config_dict['account_type']}")
    print(f"Execution Mode: {config_dict['execution_mode']}")
    print(f"Active Strategies: {config_dict['active_strategies']}")
    print(f"Tickers: {config_dict['tickers']}")
    print(f"Position Size Type: {config_dict['position_size_type']}")
    print(f"Position Size Value: {config_dict['position_size_value']}")
    
    # CDM Settings Analysis
    cdm_settings = config_dict['cdm_settings']
    print("\n=== CDM Strategy Settings ===")
    print(f"Enabled: {cdm_settings['enabled']}")
    print(f"Capital Allocation: {cdm_settings['capital_allocation']} ({cdm_settings['capital_allocation']*100}%)")
    print(f"Symbol: {cdm_settings['symbol']}")
    print(f"Max Orders: {cdm_settings['max_orders']}")
    print(f"Order Sizes (first 5): {cdm_settings['order_sizes'][:5]}")
    
    # Convert to TradingConfig object
    config = dict_to_config(config_dict)
    
    print("\n=== Position Sizing Calculation Test ===")
    
    # Test parameters
    account_balance = 100000.0  # $100,000
    spy_price = 450.0  # Approximate SPY price
    
    print(f"Test Account Balance: ${account_balance:,.2f}")
    print(f"SPY Price: ${spy_price:.2f}")
    
    # Test position sizing for CDM strategy
    cdm_strategy_settings = config.get_strategy_settings(StrategyType.CDM)
    
    print(f"\nCDM Strategy Enabled: {cdm_strategy_settings.enabled}")
    print(f"CDM Capital Allocation: {cdm_strategy_settings.capital_allocation} ({cdm_strategy_settings.capital_allocation*100}%)")
    
    # Calculate position sizes for first few legs
    print("\n=== Position Size Calculations ===")
    
    for leg in range(5):
        # Get size multiplier for this leg
        if leg < len(cdm_strategy_settings.order_sizes):
            size_multiplier = cdm_strategy_settings.order_sizes[leg]
        else:
            size_multiplier = cdm_strategy_settings.order_sizes[-1]
        
        # Calculate dollar amount
        base_allocation = cdm_strategy_settings.capital_allocation
        dollar_amount = account_balance * base_allocation * size_multiplier
        
        # Calculate shares
        shares = dollar_amount / spy_price
        
        print(f"Leg {leg + 1}:")
        print(f"  Size Multiplier: {size_multiplier}x")
        print(f"  Dollar Amount: ${dollar_amount:,.2f}")
        print(f"  Shares: {shares:.2f}")
        print(f"  Percentage of Account: {(dollar_amount/account_balance)*100:.2f}%")
        
        # Check for potential issues
        if dollar_amount > account_balance:
            print(f"  ⚠️  WARNING: Dollar amount exceeds account balance!")
        if shares < 1:
            print(f"  ⚠️  WARNING: Less than 1 share - may cause issues!")
        if (dollar_amount/account_balance) > 1.0:
            print(f"  ⚠️  WARNING: Position exceeds 100% of account!")
        
        print()
    
    # Test effective position size method
    print("=== Effective Position Size Test ===")
    effective_size = config.get_effective_position_size_for_strategy(
        StrategyType.CDM, account_balance, spy_price
    )
    print(f"Effective Position Size (base): {effective_size:.2f} shares")
    print(f"Effective Dollar Value: ${effective_size * spy_price:,.2f}")
    
    # Check for NaN or invalid values
    if effective_size != effective_size:  # NaN check
        print("❌ ERROR: Effective position size is NaN!")
        return False
    elif effective_size <= 0:
        print("❌ ERROR: Effective position size is zero or negative!")
        return False
    else:
        print("✅ Position sizing calculation appears valid")
        return True

if __name__ == "__main__":
    try:
        success = test_position_sizing()
        if success:
            print("\n🎉 Configuration test completed successfully!")
        else:
            print("\n❌ Configuration test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)