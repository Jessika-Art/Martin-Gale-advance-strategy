# Multi-Martingales Trading Bot for IBKR

A sophisticated algorithmic trading bot implementing four different martingale strategies for Interactive Brokers.

## Features

### Trading Strategies
- **CDM (Classic Down Martingale)**: Traditional martingale with position recovery
- **WDM (Windowed Down Martingale)**: Martingale with stop-loss and take-profit
- **ZRM (Zone Recovery Martingale)**: Zone-based recovery with trailing stops
- **IZRM (Inverse Zone Recovery Martingale)**: Inverse zone recovery strategy

### Key Capabilities
- **Multi-Strategy Execution**: Run single or multiple strategies simultaneously
- **Multi-Symbol Trading**: Trade multiple symbols with different strategies
- **Account Switching**: Easy switching between Demo and Live accounts
- **Position Management**: Sophisticated multi-leg position tracking
- **Risk Management**: Configurable stop-loss, take-profit, and position sizing
- **Performance Analytics**: Comprehensive cycle analysis and metrics

## Quick Start

### Prerequisites
1. **Interactive Brokers Account** with API access enabled
2. **IB Gateway or TWS** running and configured
3. **Python 3.8+** with required packages installed

### Installation
```bash
# Install required packages
pip install ibapi python-dotenv pandas numpy

# Navigate to the app directory
cd app
```

### Quick Test
```bash
# Run component test to verify everything works
python demo.py
# Select option 1 for Quick Component Test
```

### Demo Mode
```bash
# Run interactive demos
python demo.py

# Or run specific demos directly:
python -c "from demo import demo_single_strategy; demo_single_strategy()"
python -c "from demo import demo_multiple_strategies; demo_multiple_strategies()"
python -c "from demo import demo_multiple_symbols; demo_multiple_symbols()"
```

### Interactive Mode
```bash
# Run the main application in interactive mode
python main.py --mode interactive

# Or simply:
python main.py
```

### Automated Mode
```bash
# Run with specific configuration
python main.py --mode auto --account demo --symbols AAPL TSLA --strategies CDM WDM

# Run single strategy on single symbol
python main.py --mode auto --account demo --symbols AAPL --strategies CDM

# Run multiple strategies on multiple symbols
python main.py --mode auto --account demo --symbols AAPL TSLA MSFT --strategies CDM WDM ZRM
```

## Configuration

### Account Setup
The bot supports easy switching between Demo and Live accounts:

```python
from control_panel import ControlPanel

panel = ControlPanel()

# Switch to demo account
panel.update_account_type("demo")

# Switch to live account (be careful!)
panel.update_account_type("live")
```

### Symbol Configuration
```python
# Configure trading symbols
panel.update_symbols(["AAPL", "TSLA", "MSFT", "GOOGL"])
```

### Strategy Configuration
```python
# Enable specific strategies for specific symbols
panel.enable_strategy("CDM", "AAPL", True)
panel.enable_strategy("WDM", "TSLA", True)
panel.enable_strategy("ZRM", "MSFT", True)
panel.enable_strategy("IZRM", "GOOGL", True)
```

### Position Sizing
```python
# Set position sizing as percentage of account
panel.update_position_sizing("percentage", 5.0)  # 5% per strategy

# Or set fixed dollar amount
panel.update_position_sizing("fixed_amount", 1000.0)  # $1000 per strategy
```

## Strategy Details

### CDM (Classic Down Martingale)
- **Entry**: Price drops below trigger level
- **Legs**: Add positions as price continues down
- **Exit**: Price recovers to break-even or profit
- **Risk**: No stop-loss (recovery-based)

### WDM (Windowed Down Martingale)
- **Entry**: Price drops below trigger level
- **Legs**: Add positions with increasing size
- **Exit**: Stop-loss or take-profit levels
- **Risk**: Limited by stop-loss

### ZRM (Zone Recovery Martingale)
- **Entry**: Price enters defined zone
- **Legs**: Add positions within zone
- **Exit**: Price exits zone or trailing stop
- **Risk**: Zone-based with trailing stops

### IZRM (Inverse Zone Recovery Martingale)
- **Entry**: Price moves inverse to expected direction
- **Legs**: Add positions on continued inverse movement
- **Exit**: Price returns to zone or stop-loss
- **Risk**: Limited by zone boundaries

## File Structure

```
app/
├── main.py              # Main application entry point
├── demo.py              # Demo scripts and testing
├── control_panel.py     # Configuration and control interface
├── trading_engine.py    # Main trading engine
├── strategies.py        # Strategy implementations
├── ibkr_api.py         # Interactive Brokers API wrapper
├── config.py           # Configuration classes and enums
└── README.md           # This file
```

## Usage Examples

### Example 1: Single Strategy Demo Account
```python
from control_panel import ControlPanel

# Create control panel
panel = ControlPanel("my_config.json")

# Configure for demo trading
config = panel.create_default_config("demo")
panel.update_symbols(["AAPL"])
panel.enable_strategy("CDM", "AAPL", True)
panel.update_position_sizing("percentage", 5.0)

# Start trading
panel.start_trading()

# Monitor and stop when needed
panel.print_status()
panel.stop_trading()
```

### Example 2: Multiple Strategies Live Account
```python
from control_panel import ControlPanel

# Create control panel
panel = ControlPanel("live_config.json")

# Configure for live trading (be careful!)
config = panel.create_default_config("live")
panel.update_symbols(["TSLA", "AAPL"])
panel.enable_strategy("CDM", "TSLA", True)
panel.enable_strategy("WDM", "AAPL", True)
panel.update_position_sizing("fixed_amount", 2000.0)

# Start trading
panel.start_trading()
```

### Example 3: Command Line Usage
```bash
# Demo account with multiple strategies
python main.py --mode auto --account demo --symbols AAPL TSLA MSFT --strategies CDM WDM

# Live account with single strategy (be careful!)
python main.py --mode auto --account live --symbols AAPL --strategies CDM

# Interactive mode for manual configuration
python main.py --mode interactive
```

## Configuration Files

The bot uses JSON configuration files to store settings:

```json
{
  "ib_config": {
    "account_type": "demo",
    "host": "127.0.0.1",
    "demo_port": 7497,
    "live_port": 7496,
    "client_id": 1
  },
  "shared_settings": {
    "execution_mode": "parallel",
    "position_sizing_method": "percentage",
    "position_sizing_value": 5.0
  },
  "symbols": ["AAPL"],
  "strategy_settings": {
    "AAPL": {
      "CDM": {
        "enabled": true,
        "price_trigger": -0.02,
        "max_orders": 5,
        "order_distances": [0.01, 0.015, 0.02, 0.025],
        "order_sizes": [1.0, 1.5, 2.0, 2.5]
      }
    }
  }
}
```

## Safety Features

### Account Protection
- **Demo Mode Default**: Always starts in demo mode
- **Explicit Live Confirmation**: Requires explicit confirmation for live trading
- **Position Limits**: Configurable maximum positions and sizes
- **Stop-Loss Protection**: Built-in risk management

### Error Handling
- **Connection Monitoring**: Automatic reconnection attempts
- **Order Validation**: Pre-trade validation checks
- **Exception Handling**: Graceful error recovery
- **Logging**: Comprehensive logging for debugging

## Monitoring and Analytics

### Real-time Monitoring
```python
# Check current status
panel.print_status()

# Force exit all positions if needed
panel.force_exit_all()
```

### Performance Metrics
- **Cycle Analysis**: Win rate, profit/loss, duration
- **Risk Metrics**: Sharpe ratio, maximum drawdown, recovery factor
- **Efficiency Metrics**: ROE, capital efficiency, time-weighted returns

## Important Notes

### Before Trading
1. **Test Thoroughly**: Always test strategies in demo mode first
2. **Understand Risks**: Martingale strategies can have significant drawdowns
3. **Position Sizing**: Use appropriate position sizing for your account
4. **Market Conditions**: Consider current market volatility and conditions

### IB Gateway/TWS Setup
1. **Enable API**: Configure API settings in TWS/Gateway
2. **Ports**: Demo (7497), Live (7496)
3. **Permissions**: Ensure trading permissions are enabled
4. **Connection**: Verify connection before starting bot

### Risk Management
1. **Start Small**: Begin with small position sizes
2. **Monitor Closely**: Watch the bot especially during initial runs
3. **Set Limits**: Use appropriate stop-losses and position limits
4. **Emergency Stop**: Know how to quickly stop all trading

## Troubleshooting

### Common Issues
1. **Connection Failed**: Check IB Gateway/TWS is running and API is enabled
2. **Invalid Orders**: Verify account permissions and margin requirements
3. **Strategy Not Triggering**: Check price triggers and market conditions
4. **Configuration Errors**: Validate JSON configuration files

### Debug Mode
```bash
# Run with debug logging
python main.py --debug

# Check log files
tail -f trading_bot.log
tail -f demo.log
```

## Support

For issues and questions:
1. Check the log files for error messages
2. Verify IB Gateway/TWS configuration
3. Test with demo account first
4. Review strategy documentation

---

**⚠️ IMPORTANT DISCLAIMER ⚠️**

This trading bot is for educational and research purposes. Trading involves significant risk of loss. Always:
- Test thoroughly in demo mode
- Understand the strategies and risks
- Use appropriate position sizing
- Monitor your trades closely
- Never risk more than you can afford to lose

The authors are not responsible for any trading losses incurred using this software.