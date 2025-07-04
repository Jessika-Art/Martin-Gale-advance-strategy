"""Demo script for Multi-Martingales Trading Bot"""

import time
import logging
from control_panel import ControlPanel
from config import StrategyType

def setup_demo_logging():
    """Setup logging for demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('demo.log'),
            logging.StreamHandler()
        ]
    )

def demo_single_strategy():
    """Demo running a single CDM strategy on AAPL"""
    print("\n" + "="*60)
    print("DEMO: Single CDM Strategy on AAPL (Demo Account)")
    print("="*60)
    
    # Create control panel
    panel = ControlPanel("demo_single.json")
    
    try:
        # Create demo configuration
        config = panel.create_default_config("demo")
        
        # Assign config to panel so methods can work
        panel.config = config
        
        # Configure for single strategy
        panel.update_symbols(["AAPL"])
        panel.enable_strategy("CDM", True)
        panel.enable_strategy("WDM", False)
        panel.enable_strategy("ZRM", False)
        panel.enable_strategy("IZRM", False)
        
        # Set position sizing to 5% of account
        panel.update_position_sizing("percentage", 5.0)
        
        # Save and load configuration
        panel.save_config(config)
        panel.load_config()
        
        print("\nConfiguration:")
        print(f"Account: {config.account_type.value}")
        print(f"Symbol: AAPL")
        print(f"Strategy: CDM only")
        print(f"Position Size: 5% of account")
        
        # Start trading
        print("\nStarting trading engine...")
        if panel.start_trading():
            print("✓ Trading engine started successfully!")
            print("\nIMPORTANT: Make sure IB Gateway/TWS is running on demo account")
            
            # Run for demo period
            print("\nRunning demo for 60 seconds...")
            for i in range(12):  # 12 * 5 = 60 seconds
                time.sleep(5)
                print(f"Demo running... {(i+1)*5}/60 seconds")
                
                if i % 3 == 0:  # Show status every 15 seconds
                    print("\nStatus Update:")
                    panel.print_status()
            
            print("\nDemo completed. Stopping trading engine...")
            panel.stop_trading()
            print("✓ Trading engine stopped.")
            
        else:
            print("✗ Failed to start trading engine")
            print("Check that IB Gateway/TWS is running and configured properly")
    
    except Exception as e:
        print(f"Demo failed: {e}")
        panel.stop_trading()

def demo_multiple_strategies():
    """Demo running multiple strategies on TSLA"""
    print("\n" + "="*60)
    print("DEMO: Multiple Strategies on TSLA (Demo Account)")
    print("="*60)
    
    # Create control panel
    panel = ControlPanel("demo_multiple.json")
    
    try:
        # Create demo configuration
        config = panel.create_default_config("demo")
        
        # Assign config to panel so methods can work
        panel.config = config
        
        # Configure for multiple strategies
        panel.update_symbols(["TSLA"])
        panel.enable_strategy("CDM", True)
        panel.enable_strategy("WDM", True)
        panel.enable_strategy("ZRM", False)  # Keep ZRM/IZRM disabled for demo
        panel.enable_strategy("IZRM", False)
        
        # Set position sizing to 3% of account per strategy
        panel.update_position_sizing("percentage", 3.0)
        
        # Save and load configuration
        panel.save_config(config)
        panel.load_config()
        
        print("\nConfiguration:")
        print(f"Account: {config.account_type.value}")
        print(f"Symbol: TSLA")
        print(f"Strategies: CDM + WDM")
        print(f"Position Size: 3% of account per strategy")
        
        # Start trading
        print("\nStarting trading engine...")
        if panel.start_trading():
            print("✓ Trading engine started successfully!")
            print("\nIMPORTANT: Make sure IB Gateway/TWS is running on demo account")
            
            # Run for demo period
            print("\nRunning demo for 90 seconds...")
            for i in range(18):  # 18 * 5 = 90 seconds
                time.sleep(5)
                print(f"Demo running... {(i+1)*5}/90 seconds")
                
                if i % 4 == 0:  # Show status every 20 seconds
                    print("\nStatus Update:")
                    panel.print_status()
            
            print("\nDemo completed. Stopping trading engine...")
            panel.stop_trading()
            print("✓ Trading engine stopped.")
            
        else:
            print("✗ Failed to start trading engine")
            print("Check that IB Gateway/TWS is running and configured properly")
    
    except Exception as e:
        print(f"Demo failed: {e}")
        panel.stop_trading()

def demo_multiple_symbols():
    """Demo running strategies on multiple symbols"""
    print("\n" + "="*60)
    print("DEMO: CDM Strategy on Multiple Symbols (Demo Account)")
    print("="*60)
    
    # Create control panel
    panel = ControlPanel("demo_multi_symbols.json")
    
    try:
        # Create demo configuration
        config = panel.create_default_config("demo")
        
        # Assign config to panel so methods can work
        panel.config = config
        
        # Configure for multiple symbols
        symbols = ["AAPL", "MSFT", "GOOGL"]
        panel.update_symbols(symbols)
        
        # Enable CDM for all symbols
        for symbol in symbols:
            panel.enable_strategy("CDM", True)
            panel.enable_strategy("WDM", False)
            panel.enable_strategy("ZRM", False)
            panel.enable_strategy("IZRM", False)
        
        # Set position sizing to 2% of account per strategy
        panel.update_position_sizing("percentage", 2.0)
        
        # Save and load configuration
        panel.save_config(config)
        panel.load_config()
        
        print("\nConfiguration:")
        print(f"Account: {config.account_type.value}")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Strategy: CDM on all symbols")
        print(f"Position Size: 2% of account per strategy")
        
        # Start trading
        print("\nStarting trading engine...")
        if panel.start_trading():
            print("✓ Trading engine started successfully!")
            print("\nIMPORTANT: Make sure IB Gateway/TWS is running on demo account")
            
            # Run for demo period
            print("\nRunning demo for 120 seconds...")
            for i in range(24):  # 24 * 5 = 120 seconds
                time.sleep(5)
                print(f"Demo running... {(i+1)*5}/120 seconds")
                
                if i % 5 == 0:  # Show status every 25 seconds
                    print("\nStatus Update:")
                    panel.print_status()
            
            print("\nDemo completed. Stopping trading engine...")
            panel.stop_trading()
            print("✓ Trading engine stopped.")
            
        else:
            print("✗ Failed to start trading engine")
            print("Check that IB Gateway/TWS is running and configured properly")
    
    except Exception as e:
        print(f"Demo failed: {e}")
        panel.stop_trading()

def interactive_demo():
    """Interactive demo menu"""
    print("\n" + "="*60)
    print("MULTI-MARTINGALES TRADING BOT - DEMO MODE")
    print("="*60)
    print("\nAvailable Demos:")
    print("1. Single Strategy Demo (CDM on AAPL)")
    print("2. Multiple Strategies Demo (CDM + WDM on TSLA)")
    print("3. Multiple Symbols Demo (CDM on AAPL, MSFT, GOOGL)")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect demo (1-4): ").strip()
            
            if choice == '1':
                demo_single_strategy()
            elif choice == '2':
                demo_multiple_strategies()
            elif choice == '3':
                demo_multiple_symbols()
            elif choice == '4':
                print("Exiting demo mode.")
                break
            else:
                print("Invalid choice. Please select 1-4.")
                continue
            
            input("\nPress Enter to return to demo menu...")
            
        except KeyboardInterrupt:
            print("\nDemo interrupted by user.")
            break
        except Exception as e:
            print(f"Demo error: {e}")
            input("Press Enter to continue...")

def quick_test():
    """Quick test to verify all components work"""
    print("\n" + "="*60)
    print("QUICK COMPONENT TEST")
    print("="*60)
    
    try:
        print("\n1. Testing Control Panel...")
        panel = ControlPanel("test_config.json")
        print("✓ Control Panel created")
        
        print("\n2. Testing Configuration Creation...")
        config = panel.create_default_config("demo")
        print("✓ Default configuration created")
        
        print("\n3. Testing Symbol Configuration...")
        panel.update_symbols(["AAPL", "TSLA"])
        print("✓ Symbols configured")
        
        print("\n4. Testing Strategy Configuration...")
        panel.enable_strategy("CDM", True)
        panel.enable_strategy("WDM", True)
        print("✓ Strategies configured")
        
        print("\n5. Testing Position Sizing...")
        panel.update_position_sizing("percentage", 5.0)
        print("✓ Position sizing configured")
        
        print("\n6. Testing Configuration Save/Load...")
        panel.save_config(config)
        loaded_config = panel.load_config()
        print("✓ Configuration save/load works")
        
        print("\n7. Testing Status Display...")
        panel.print_status()
        print("✓ Status display works")
        
        print("\n" + "="*60)
        print("ALL COMPONENT TESTS PASSED!")
        print("The trading bot is ready to use.")
        print("="*60)
        
        print("\nNext steps:")
        print("1. Make sure IB Gateway/TWS is running")
        print("2. Configure your account settings")
        print("3. Run the main script or demos")
        
    except Exception as e:
        print(f"\n✗ Component test failed: {e}")
        print("Please check the error and fix any issues.")

def main():
    """Main demo entry point"""
    setup_demo_logging()
    
    print("\n" + "="*60)
    print("MULTI-MARTINGALES TRADING BOT - DEMO LAUNCHER")
    print("="*60)
    print("\nDemo Options:")
    print("1. Quick Component Test")
    print("2. Interactive Demo Menu")
    print("3. Single Strategy Demo")
    print("4. Multiple Strategies Demo")
    print("5. Multiple Symbols Demo")
    print("6. Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                quick_test()
            elif choice == '2':
                interactive_demo()
            elif choice == '3':
                demo_single_strategy()
            elif choice == '4':
                demo_multiple_strategies()
            elif choice == '5':
                demo_multiple_symbols()
            elif choice == '6':
                print("Exiting demo launcher.")
                break
            else:
                print("Invalid choice. Please select 1-6.")
                continue
            
            input("\nPress Enter to return to main menu...")
            
        except KeyboardInterrupt:
            print("\nExiting demo launcher.")
            break
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()