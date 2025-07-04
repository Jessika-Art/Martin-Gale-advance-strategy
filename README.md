# 📈 MartinGales Trading Bot for Interactive Brokers

A sophisticated multi-strategy trading bot designed for Interactive Brokers (IBKR) that implements various Martingale-based trading strategies with advanced risk management, position sizing, and performance analytics.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Interactive Brokers TWS (Trader Workstation) or IB Gateway
- Active IBKR account (Paper Trading or Live)

### Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r app/ui/requirements.txt
   ```
3. Configure Interactive Brokers connection (see [IBKR Setup](#-interactive-brokers-setup))

### Launch Application
```bash
streamlit run app/ui/app.py
```

The web interface will open at `http://localhost:8501`

## 🔗 Interactive Brokers Setup

### Connection Requirements
- **TWS/IB Gateway**: Must be running and logged in
- **API Settings**: Enable API connections in TWS/Gateway
  - Go to File → Global Configuration → API → Settings
  - Check "Enable ActiveX and Socket Clients"
  - Add your client ID (default: 1)
- **Ports**:
  - Paper Trading: 4002 (default)
  - Live Trading: 4001 (default)

### Account Configuration
The bot supports both:
- **Demo/Paper Trading**: Safe testing environment
- **Live Trading**: Real money trading (use with caution)

Switch between accounts in the Configuration Manager within the UI.

## 🎯 Core Features

### Multi-Strategy Trading
- **CDM (Counter Direction Martingale)**: Trades against the trend
- **WDM (With Direction Martingale)**: Trades with the trend
- **ZRM (Zone Recovery Martingale)**: Zone-based recovery strategy
- **IZRM (Inverse Zone Recovery Martingale)**: Inverse zone recovery

### Execution Modes
- **Single Strategy**: Run one strategy at a time
- **Parallel Execution**: Multiple strategies simultaneously
- **Sequential Execution**: Strategies run in sequence

### Advanced Position Management
- **Multi-Symbol Trading**: Trade multiple symbols with different strategies
- **Flexible Position Sizing**: Percentage, fixed shares, or USD-based
- **Dynamic Leg Sizing**: Customizable multipliers for each trading leg
- **Trailing Stops**: Configurable trailing stop-loss protection

## 📁 Project Structure

### Core Application (`app/`)

#### Main Components
- **`main.py`** - Main application entry point and orchestration
- **`config.py`** - Configuration classes, enums, and validation logic
- **`trading_engine.py`** - Core trading engine coordinating all strategies
- **`strategies.py`** - Implementation of all Martingale trading strategies
- **`ibkr_api.py`** - Interactive Brokers API wrapper and connection management
- **`control_panel.py`** - Configuration and control interface for the trading bot

#### Risk & Money Management
- **`risk_manager.py`** - Real-time risk monitoring and position limits
- **`enhanced_risk_management.py`** - Advanced risk controls and drawdown protection
- **`advanced_money_management.py`** - Portfolio growth and capital allocation strategies
- **`financial_metrics.py`** - Financial calculations and performance metrics

#### Analytics & Performance
- **`performance_monitor.py`** - Real-time performance tracking and reporting
- **`cycle_analysis.py`** - Trading cycle analysis and optimization
- **`backtesting_system.py`** - Historical strategy testing and validation

#### User Interface (`app/ui/`)
- **`app.py`** - Main Streamlit web application
- **`dashboard.py`** - Real-time trading dashboard and status monitoring
- **`config_manager.py`** - Interactive configuration management interface
- **`performance.py`** - Performance analytics and visualization
- **`backtesting_ui.py`** - Backtesting interface and results visualization
- **`cycle_analysis_ui.py`** - Trading cycle analysis dashboard
- **`money_management_ui.py`** - Money management configuration interface
- **`risk_management_ui.py`** - Risk management settings and monitoring

#### Testing & Demo
- **`demo.py`** - Demo scripts and testing utilities

## 🛠️ Key Features Breakdown

### Strategy Management
- **Multi-Strategy Coordination**: Run multiple strategies with intelligent coordination
- **Strategy Alignment**: Parallel or sequential execution modes
- **Dynamic Entry/Exit**: Market condition-based entry and exit logic
- **Leg Management**: Progressive position building with customizable multipliers

### Risk Management
- **Position Limits**: Maximum concurrent positions and order limits
- **Drawdown Protection**: Portfolio-level drawdown monitoring
- **Daily Limits**: Configurable daily profit targets and loss limits
- **Emergency Exits**: Automatic emergency exit conditions
- **Trailing Stops**: Dynamic trailing stop-loss protection

### Position Sizing
- **Flexible Units**: Support for SHARES, USD, and PERCENTAGE-based sizing
- **Fixed Position Size**: Set fixed position sizes with multipliers
- **Portfolio Percentage**: Risk-based percentage allocation
- **Dynamic Sizing**: Adaptive position sizing based on market conditions
- **Capital Allocation**: Intelligent capital distribution across strategies

### Performance Analytics
- **Real-Time Monitoring**: Live P&L tracking and performance metrics
- **Cycle Analysis**: Detailed analysis of trading cycles and patterns
- **Win Rate Tracking**: Success rate monitoring across strategies
- **Drawdown Analysis**: Maximum drawdown and recovery tracking
- **Performance Reports**: Comprehensive performance reporting

### Backtesting System
- **Historical Testing**: Test strategies on historical data
- **Performance Validation**: Validate strategy performance before live trading
- **Parameter Optimization**: Optimize strategy parameters
- **Risk Assessment**: Historical risk analysis and validation

### User Interface Features
- **Web-Based Dashboard**: Modern, responsive web interface
- **Real-Time Updates**: Live data updates and status monitoring
- **Configuration Management**: Easy-to-use configuration interface
- **Performance Visualization**: Interactive charts and analytics
- **Multi-Page Navigation**: Organized interface with dedicated sections

## 🔧 Configuration

The bot offers extensive configuration options:

- **Account Settings**: Demo/Live account selection
- **Strategy Parameters**: Individual strategy configuration
- **Risk Parameters**: Risk limits and protection settings
- **Position Sizing**: Flexible position sizing options
- **Market Data**: Timeframe and data source configuration
- **Execution Settings**: Order types and execution preferences

## 📊 Monitoring & Analytics

### Real-Time Dashboard
- Live P&L tracking
- Active positions monitoring
- Strategy performance metrics
- Risk exposure analysis

### Performance Analytics
- Historical performance charts
- Win/loss ratio analysis
- Drawdown tracking
- Cycle performance analysis

### Risk Monitoring
- Real-time risk exposure
- Position limit monitoring
- Drawdown alerts
- Emergency exit triggers

## ⚠️ Risk Disclaimer

**IMPORTANT**: This trading bot involves substantial risk of loss. Past performance does not guarantee future results. Only trade with capital you can afford to lose.

- Start with paper trading to familiarize yourself with the system
- Thoroughly test strategies before live trading
- Monitor positions actively
- Use appropriate position sizing
- Set strict risk limits

## 🤝 Support

For questions, issues, or contributions:
- Review the documentation in the `app/` folder
- Check the `BACKTESTING_GUIDE.md` for backtesting instructions
- Examine example configurations and improvements in the `examples/` folder

## 📄 License

This project is for educational and research purposes. Use at your own risk.

---

**Happy Trading! 📈**
