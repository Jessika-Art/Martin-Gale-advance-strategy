"""Main script for Multi-Martingales Trading Bot"""

import sys
import time
import signal
import argparse
from typing import Optional
import logging

from control_panel import ControlPanel
from config import StrategyType

class TradingBotMain:
    """Main application class for the trading bot"""
    
    def __init__(self):
        self.panel: Optional[ControlPanel] = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown (only in main thread)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Signal handling only works in main thread, skip in Streamlit
            pass
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutdown signal received. Stopping trading bot...")
        self.shutdown()
        sys.exit(0)
    
    def setup_logging(self, debug: bool = False):
        """Setup logging configuration"""
        log_level = logging.DEBUG if debug else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize(self, config_file: str = "trading_config.json") -> bool:
        """Initialize the trading bot"""
        try:
            print("Initializing Multi-Martingales Trading Bot...")
            
            # Create control panel
            self.panel = ControlPanel(config_file)
            
            # Load or create configuration
            config = self.panel.load_config()
            if not config:
                print("Creating default configuration...")
                config = self.panel.create_default_config("demo")
                self.panel.save_config(config)
                print(f"Default configuration saved to {config_file}")
            
            print("Trading bot initialized successfully!")
            return True
            
        except Exception as e:
            print(f"Failed to initialize trading bot: {e}")
            return False
    
    def run_interactive_mode(self):
        """Run the bot in interactive mode"""
        if not self.panel:
            print("Bot not initialized. Call initialize() first.")
            return
        
        print("\n" + "="*60)
        print("MULTI-MARTINGALES TRADING BOT - INTERACTIVE MODE")
        print("="*60)
        
        while True:
            try:
                self._show_main_menu()
                choice = input("\nEnter your choice: ").strip()
                
                if choice == '1':
                    self._configure_account()
                elif choice == '2':
                    self._configure_symbols()
                elif choice == '3':
                    self._configure_strategies()
                elif choice == '4':
                    self._configure_position_sizing()
                elif choice == '5':
                    self._start_trading()
                elif choice == '6':
                    self._stop_trading()
                elif choice == '7':
                    self._show_status()
                elif choice == '8':
                    self._force_exit_all()
                elif choice == '9':
                    self._save_configuration()
                elif choice == '10':
                    self._load_configuration()
                elif choice == '0' or choice.lower() == 'q':
                    self.shutdown()
                    break
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\nShutdown requested.")
                self.shutdown()
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")
    
    def _show_main_menu(self):
        """Display the main menu"""
        print("\n" + "-"*40)
        print("MAIN MENU")
        print("-"*40)
        print("1. Configure Account (Demo/Live)")
        print("2. Configure Symbols")
        print("3. Configure Strategies")
        print("4. Configure Position Sizing")
        print("5. Start Trading")
        print("6. Stop Trading")
        print("7. Show Status")
        print("8. Force Exit All Positions")
        print("9. Save Configuration")
        print("10. Load Configuration")
        print("0. Exit")
    
    def _configure_account(self):
        """Configure account settings"""
        print("\nAccount Configuration")
        print("Current account type:", self.panel.config.ib_config.account_type.value if self.panel.config else "None")
        
        account_type = input("Enter account type (demo/live): ").strip().lower()
        
        if account_type in ['demo', 'live']:
            if self.panel.update_account_type(account_type):
                print(f"Account type updated to {account_type.upper()}")
            else:
                print("Failed to update account type")
        else:
            print("Invalid account type. Use 'demo' or 'live'.")
    
    def _configure_symbols(self):
        """Configure trading symbols"""
        print("\nSymbol Configuration")
        if self.panel.config:
            print("Current symbols:", ", ".join(self.panel.config.symbols))
        
        symbols_input = input("Enter symbols (comma-separated, e.g., AAPL,TSLA,MSFT): ").strip()
        
        if symbols_input:
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
            if symbols:
                if self.panel.update_symbols(symbols):
                    print(f"Symbols updated to: {', '.join(symbols)}")
                else:
                    print("Failed to update symbols")
            else:
                print("No valid symbols provided")
        else:
            print("No symbols entered")
    
    def _configure_strategies(self):
        """Configure strategy settings"""
        print("\nStrategy Configuration")
        
        if not self.panel.config or not self.panel.config.symbols:
            print("No symbols configured. Please configure symbols first.")
            return
        
        strategies = ['CDM', 'WDM', 'ZRM', 'IZRM']
        
        for symbol in self.panel.config.symbols:
            print(f"\nConfiguring strategies for {symbol}:")
            
            for strategy in strategies:
                current_status = "Enabled" if (symbol in self.panel.config.strategy_settings and 
                                             StrategyType(strategy) in self.panel.config.strategy_settings[symbol] and
                                             self.panel.config.strategy_settings[symbol][StrategyType(strategy)].enabled) else "Disabled"
                
                print(f"  {strategy} - Currently: {current_status}")
                
                enable = input(f"    Enable {strategy} for {symbol}? (y/n): ").strip().lower()
                
                if enable in ['y', 'yes']:
                    self.panel.enable_strategy(strategy, symbol, True)
                elif enable in ['n', 'no']:
                    self.panel.enable_strategy(strategy, symbol, False)
    
    def _configure_position_sizing(self):
        """Configure position sizing"""
        print("\nPosition Sizing Configuration")
        print("1. Percentage of account balance")
        print("2. Fixed dollar amount")
        
        sizing_choice = input("Choose sizing method (1/2): ").strip()
        
        if sizing_choice == '1':
            percentage = input("Enter percentage of account balance (e.g., 5 for 5%): ").strip()
            try:
                pct_value = float(percentage)
                if 0 < pct_value <= 100:
                    if self.panel.update_position_sizing("percentage", pct_value):
                        print(f"Position sizing set to {pct_value}% of account balance")
                    else:
                        print("Failed to update position sizing")
                else:
                    print("Percentage must be between 0 and 100")
            except ValueError:
                print("Invalid percentage value")
        
        elif sizing_choice == '2':
            amount = input("Enter fixed dollar amount per strategy: ").strip()
            try:
                amount_value = float(amount)
                if amount_value > 0:
                    if self.panel.update_position_sizing("fixed_amount", amount_value):
                        print(f"Position sizing set to ${amount_value} per strategy")
                    else:
                        print("Failed to update position sizing")
                else:
                    print("Amount must be positive")
            except ValueError:
                print("Invalid amount value")
        else:
            print("Invalid choice")
    
    def _start_trading(self):
        """Start the trading engine"""
        print("\nStarting trading engine...")
        
        if not self.panel.config:
            print("No configuration loaded. Please configure the bot first.")
            return
        
        # Show current configuration
        print("\nCurrent Configuration:")
        print(f"Account Type: {self.panel.config.ib_config.account_type.value}")
        print(f"Symbols: {', '.join(self.panel.config.symbols)}")
        
        enabled_strategies = []
        for symbol, strategies in self.panel.config.strategy_settings.items():
            for strategy_type, settings in strategies.items():
                if settings.enabled:
                    enabled_strategies.append(f"{strategy_type.value}_{symbol}")
        
        print(f"Enabled Strategies: {', '.join(enabled_strategies) if enabled_strategies else 'None'}")
        
        if not enabled_strategies:
            print("No strategies enabled. Please enable at least one strategy.")
            return
        
        confirm = input("\nConfirm to start trading with this configuration? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            if self.panel.start_trading():
                print("Trading engine started successfully!")
                print("\nIMPORTANT: Make sure Interactive Brokers TWS/Gateway is running and connected.")
                self.running = True
            else:
                print("Failed to start trading engine. Check logs for details.")
        else:
            print("Trading start cancelled.")
    
    def _stop_trading(self):
        """Stop the trading engine"""
        print("\nStopping trading engine...")
        
        if self.panel.stop_trading():
            print("Trading engine stopped successfully.")
            self.running = False
        else:
            print("Failed to stop trading engine.")
    
    def _show_status(self):
        """Show current status"""
        print("\nCurrent Status:")
        self.panel.print_status()
    
    def _force_exit_all(self):
        """Force exit all positions"""
        print("\nForce Exit All Positions")
        print("WARNING: This will immediately close all open positions!")
        
        confirm = input("Are you sure you want to force exit all positions? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            if self.panel.force_exit_all():
                print("Force exit command sent to all strategies.")
            else:
                print("Failed to send force exit command.")
        else:
            print("Force exit cancelled.")
    
    def _save_configuration(self):
        """Save current configuration"""
        filename = input("Enter filename (or press Enter for default): ").strip()
        
        if not filename:
            filename = None
        
        if self.panel.save_config(self.panel.config, filename):
            print(f"Configuration saved successfully.")
        else:
            print("Failed to save configuration.")
    
    def _load_configuration(self):
        """Load configuration from file"""
        filename = input("Enter filename (or press Enter for default): ").strip()
        
        if not filename:
            filename = None
        
        config = self.panel.load_config(filename)
        if config:
            print("Configuration loaded successfully.")
        else:
            print("Failed to load configuration.")
    
    def run_automated(self, config_file: str = "trading_config.json", 
                     account_type: str = "demo", symbols: list = None, 
                     strategies: list = None):
        """Run the bot in automated mode with specified parameters"""
        if not self.initialize(config_file):
            return False
        
        print(f"\nRunning in automated mode...")
        
        # Configure account type
        if not self.panel.update_account_type(account_type):
            print(f"Failed to set account type to {account_type}")
            return False
        
        # Configure symbols
        if symbols:
            if not self.panel.update_symbols(symbols):
                print(f"Failed to set symbols to {symbols}")
                return False
        
        # Configure strategies
        if strategies and self.panel.config:
            # Disable all strategies first
            for symbol in self.panel.config.symbols:
                for strategy_type in ['CDM', 'WDM', 'ZRM', 'IZRM']:
                    self.panel.enable_strategy(strategy_type, symbol, False)
            
            # Enable specified strategies
            for symbol in self.panel.config.symbols:
                for strategy in strategies:
                    self.panel.enable_strategy(strategy.upper(), symbol, True)
        
        # Save configuration
        self.panel.save_config(self.panel.config)
        
        # Start trading
        if not self.panel.start_trading():
            print("Failed to start trading engine")
            return False
        
        print("Trading bot started successfully!")
        print("Press Ctrl+C to stop the bot.")
        
        self.running = True
        
        try:
            # Keep running and show status periodically
            while self.running:
                time.sleep(30)  # Show status every 30 seconds
                print("\n" + "="*50)
                print(f"Status Update - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.panel.print_status()
                
        except KeyboardInterrupt:
            print("\nShutdown requested by user.")
        
        self.shutdown()
        return True
    
    def shutdown(self):
        """Shutdown the trading bot gracefully"""
        print("\nShutting down trading bot...")
        
        if self.panel:
            self.panel.stop_trading()
        
        self.running = False
        print("Trading bot shutdown complete.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Multi-Martingales Trading Bot')
    parser.add_argument('--mode', choices=['interactive', 'auto'], default='interactive',
                       help='Run mode: interactive or automated')
    parser.add_argument('--config', default='trading_config.json',
                       help='Configuration file path')
    parser.add_argument('--account', choices=['demo', 'live'], default='demo',
                       help='Account type for automated mode')
    parser.add_argument('--symbols', nargs='+', default=['AAPL'],
                       help='Trading symbols for automated mode')
    parser.add_argument('--strategies', nargs='+', choices=['CDM', 'WDM', 'ZRM', 'IZRM'], 
                       default=['CDM'],
                       help='Strategies to enable for automated mode')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Initialize bot
    bot = TradingBotMain()
    bot.setup_logging(args.debug)
    
    if args.mode == 'interactive':
        if bot.initialize(args.config):
            bot.run_interactive_mode()
    else:
        bot.run_automated(
            config_file=args.config,
            account_type=args.account,
            symbols=args.symbols,
            strategies=args.strategies
        )

if __name__ == "__main__":
    main()