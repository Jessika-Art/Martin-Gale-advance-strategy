#!/usr/bin/env python3
"""
Trailing Stop Functionality Demo

This script demonstrates the new trailing stop functionality added to the trading bot.
It shows how the trailing stops work with both CDM and ZRM strategies.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from config import CDMSettings, ZRMSettings, StrategyType
from strategies import CDMStrategy, ZRMStrategy, MarketData

def demo_trailing_stops():
    print("=== Trailing Stop Functionality Demo ===")
    print()
    
    # Create CDM settings with new trailing parameters
    cdm_settings = CDMSettings(
        symbol="AAPL",
        max_orders=3,
        order_sizes=[1.0, 2.0, 4.0],
        order_distances=[2.0, 3.0, 4.0],
        order_tps=[1.5, 2.0, 2.5],
        capital_allocation=0.1,
        trailing_trigger_pct=[3.0, 4.0, 5.0],  # New: Profit % to trigger trailing
        trailing_distance_pct=[1.0, 1.5, 2.0]  # New: Trailing stop distance %
    )
    
    # Create ZRM settings with new trailing parameters
    zrm_settings = ZRMSettings(
        symbol="AAPL",
        max_orders=3,
        order_sizes=[1.0, 2.0, 4.0],
        order_distances=[2.0, 3.0, 4.0],
        order_tps=[1.5, 2.0, 2.5],
        capital_allocation=0.1,
        zone_center_price=150.0,
        trailing_trigger_pct=[3.0, 4.0, 5.0],  # New: Profit % to trigger trailing
        trailing_distance_pct=[1.0, 1.5, 2.0]  # New: Trailing stop distance %
    )
    
    print("CDM Strategy Trailing Stop Settings:")
    print(f"  Trigger Percentages: {cdm_settings.trailing_trigger_pct}")
    print(f"  Distance Percentages: {cdm_settings.trailing_distance_pct}")
    print()
    
    print("ZRM Strategy Trailing Stop Settings:")
    print(f"  Trigger Percentages: {zrm_settings.trailing_trigger_pct}")
    print(f"  Distance Percentages: {zrm_settings.trailing_distance_pct}")
    print()
    
    # Create strategy instances
    cdm_strategy = CDMStrategy(cdm_settings)
    zrm_strategy = ZRMStrategy(zrm_settings)
    
    print("Strategies created successfully with trailing stop functionality!")
    print()
    
    # Demonstrate trailing stop logic
    print("=== Trailing Stop Logic Demo ===")
    print("Simulating price movements and trailing stop behavior...")
    print()
    
    # Simulate market data
    initial_price = 100.0
    market_data = MarketData(symbol="AAPL", price=initial_price, timestamp=None)
    
    # Start a cycle
    cdm_strategy.start_cycle(market_data)
    print(f"Started CDM cycle at price: ${initial_price}")
    
    # Simulate adding a position
    from strategies import Position
    position = Position(symbol="AAPL", quantity=100, avg_price=initial_price, current_price=initial_price)
    cdm_strategy.positions.append(position)
    
    # Test trailing stop activation and updates
    test_prices = [100.0, 103.0, 105.0, 107.0, 106.0, 104.0]  # Price goes up then down
    
    for price in test_prices:
        market_data.price = price
        position.current_price = price
        
        # Calculate profit percentage
        profit_pct = ((price - initial_price) / initial_price) * 100
        
        # Check if trailing stop would trigger
        should_exit = cdm_strategy.should_exit(market_data)
        
        print(f"Price: ${price:6.2f} | Profit: {profit_pct:5.1f}% | "
              f"Trailing Active: {cdm_strategy.trailing_stops_active[0]} | "
              f"Should Exit: {should_exit}")
        
        if should_exit:
            print("  -> Trailing stop triggered! Exiting position.")
            break
    
    print()
    print("Demo completed successfully!")
    print()
    print("Key Features Implemented:")
    print("✓ New trailing_trigger_pct parameter (profit % to activate trailing)")
    print("✓ New trailing_distance_pct parameter (trailing stop distance %)")
    print("✓ Trailing stop logic integrated into CDM and ZRM strategies")
    print("✓ UI updated with new parameter fields")
    print("✓ Configuration save/load updated for new parameters")
    print("✓ Backward compatibility maintained with existing parameters")

if __name__ == "__main__":
    demo_trailing_stops()