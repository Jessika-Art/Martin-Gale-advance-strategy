#!/usr/bin/env python3
"""
Test script to clarify position sizing calculation with capital allocation vs order size multipliers
"""

import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from config import TradingConfig, StrategyType
from app.ui.config_manager import dict_to_config

def test_position_sizing_clarification():
    """Test to clarify how capital allocation and order size multipliers interact"""
    
    print("=== Position Sizing Calculation Clarification ===")
    print("\nTesting the interaction between capital_allocation and order_sizes...\n")
    
    # Test parameters
    account_balance = 100000.0  # $100,000
    spy_price = 450.0  # Approximate SPY price
    
    print(f"Account Balance: ${account_balance:,.2f}")
    print(f"SPY Price: ${spy_price:.2f}")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Original Problematic Config",
            "capital_allocation": 0.1,  # 10%
            "order_sizes": [200.0, 200.0, 200.0],  # 200% multipliers
            "description": "10% allocation with 200% multipliers"
        },
        {
            "name": "Fixed Config", 
            "capital_allocation": 0.1,  # 10%
            "order_sizes": [1.0, 1.5, 2.0],  # Progressive multipliers
            "description": "10% allocation with progressive multipliers"
        },
        {
            "name": "High Multiplier with Low Allocation",
            "capital_allocation": 0.05,  # 5%
            "order_sizes": [10.0, 20.0, 30.0],  # High multipliers
            "description": "5% allocation with high multipliers"
        },
        {
            "name": "Low Multiplier with High Allocation",
            "capital_allocation": 0.5,  # 50%
            "order_sizes": [0.5, 1.0, 1.5],  # Low multipliers
            "description": "50% allocation with low multipliers"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Capital Allocation: {scenario['capital_allocation']} ({scenario['capital_allocation']*100}%)")
        print(f"Order Sizes: {scenario['order_sizes']}")
        print(f"{'='*60}")
        
        # Calculate position sizes for each leg
        for leg in range(len(scenario['order_sizes'])):
            capital_allocation = scenario['capital_allocation']
            size_multiplier = scenario['order_sizes'][leg]
            
            # This is the actual calculation from strategies.py:
            # dollar_amount = account_balance * base_allocation * size_multiplier
            dollar_amount = account_balance * capital_allocation * size_multiplier
            shares = dollar_amount / spy_price
            
            # Calculate what percentage of total account this represents
            account_percentage = (dollar_amount / account_balance) * 100
            
            print(f"\nLeg {leg + 1}:")
            print(f"  Formula: ${account_balance:,.0f} × {capital_allocation} × {size_multiplier} = ${dollar_amount:,.2f}")
            print(f"  Shares: {shares:.2f}")
            print(f"  Percentage of Total Account: {account_percentage:.2f}%")
            
            # Check for issues
            if dollar_amount > account_balance:
                print(f"  ❌ PROBLEM: Position exceeds total account balance!")
            elif account_percentage > 100:
                print(f"  ❌ PROBLEM: Position exceeds 100% of account!")
            elif shares < 1:
                print(f"  ⚠️  WARNING: Less than 1 share")
            else:
                print(f"  ✅ Position size is reasonable")
    
    print(f"\n{'='*80}")
    print("KEY INSIGHTS:")
    print("1. Capital allocation sets the BASE amount available to the strategy")
    print("2. Order size multipliers scale UP from that base amount")
    print("3. The formula is: account_balance × capital_allocation × order_size_multiplier")
    print("4. A 10% capital allocation with 200% multiplier = 2000% of the base allocation")
    print("5. This means 20% of the TOTAL account balance, not just 10%")
    print("6. Multiple legs with high multipliers can quickly exceed account balance")
    print(f"{'='*80}")
    
    # Demonstrate the math clearly
    print("\nMATH EXAMPLE:")
    print("Account: $100,000")
    print("Capital Allocation: 10% = $10,000 base")
    print("Order Size Multiplier: 200% = 2.0x")
    print("Result: $10,000 × 2.0 = $20,000 (20% of total account)")
    print("\nWith multiple legs:")
    print("Leg 1: $10,000 × 2.0 = $20,000 (20%)")
    print("Leg 2: $10,000 × 2.0 = $20,000 (20%)")
    print("Leg 3: $10,000 × 2.0 = $20,000 (20%)")
    print("Total if all legs trigger: $60,000 (60% of account)")
    print("\nThis is why the original config was problematic!")

if __name__ == "__main__":
    test_position_sizing_clarification()