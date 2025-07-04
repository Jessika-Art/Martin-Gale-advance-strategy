# 📈 MartinGales Trading Bot

Advanced Multi-Strategy Martingale Trading Bot for Interactive Brokers (IBKR)

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- Interactive Brokers account (Paper Trading or Live)
- IB Gateway or TWS (Trader Workstation)

### 1. Download and Setup IB Gateway

1. **Download IB Gateway**:
   - Visit [Interactive Brokers Gateway Download](https://www.interactivebrokers.com/en/trading/ib-gateway-download.php)
   - Download the appropriate version for your operating system
   - Install following the provided instructions

2. **Configure IB Gateway**:
   - Launch IB Gateway
   - Login with your IBKR credentials
   - Configure API settings:
     - Enable "Enable ActiveX and Socket Clients"
     - Set Socket port based on your trading mode:
       - **Paper Trading (Demo)**: Port `4002`
       - **Live Trading**: Port `4001`
     - Add `127.0.0.1` to trusted IP addresses
     - Disable "Read-Only API"

### 2. Install Dependencies

1. **Clone or download this repository**
2. **Navigate to the project directory**:
   ```bash
   cd MartinGales
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv env
   ```

4. **Activate the virtual environment**:
   - **Windows**:
     ```bash
     env\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source env/bin/activate
     ```

5. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Run the Application

#### Option 1: Using the Launcher Script (Recommended)

1. **Ensure IB Gateway is running** and connected
2. **Start the application using the launcher**:
   - **Windows**: Double-click `start_app.bat` or run:
     ```bash
     start_app.bat
     ```
   - **macOS/Linux**: Run:
     ```bash
     python run_app.py
     ```

3. **Access the application**:
   - Open your web browser
   - Navigate to: `http://localhost:8501`

4. **To stop the application**:
   - Press `Ctrl+C` in the terminal - **the application will stop immediately**

#### Option 2: Direct Streamlit Command

1. **Ensure IB Gateway is running** and connected
2. **Start the Streamlit application**:
   ```bash
   streamlit run app/ui/app.py
   ```

3. **Access the application**:
   - Open your web browser
   - Navigate to: `http://localhost:8501`

⚠️ **Note**: With the direct Streamlit command, `Ctrl+C` may not stop the application immediately. Use the launcher script for better control.

## 🔧 Configuration

### Port Configuration

| Trading Mode | Port | Description |
|--------------|------|-------------|
| **Paper Trading** | `4002` | IB Gateway demo/paper trading port |
| **Live Trading** | `4001` | IB Gateway live trading port |

### Account Setup

1. **Paper Trading** (Recommended for testing):
   - Use your paper trading credentials
   - Set account type to "Demo" in the application
   - Port: 4002

2. **Live Trading** (Real money):
   - Use your live trading credentials
   - Set account type to "Live" in the application
   - Port: 4001
   - ⚠️ **Warning**: Live trading involves real money and risk

## 📊 Features

- **Multiple Martingale Strategies**:
  - Counter Direction Martingale (CDM)
  - With Direction Martingale (WDM)
  - Zone Recovery Martingale (ZRM)
  - Inverse Zone Recovery Martingale (IZRM)

- **Advanced Configuration**:
  - Multi-timeframe support (1min to 1month)
  - Multi-symbol trading
  - Risk management controls
  - Position sizing options

- **Real-time Monitoring**:
  - Live P&L tracking
  - Performance analytics
  - Trade history
  - Account balance monitoring

- **Backtesting System**:
  - Historical strategy testing
  - Performance analysis
  - Risk assessment

## 🛡️ Risk Management

⚠️ **Important Risk Disclaimers**:

- **Martingale strategies involve significant risk** and can lead to substantial losses
- **Always test with paper trading** before using real money
- **Never risk more than you can afford to lose**
- **Past performance does not guarantee future results**
- **Use appropriate position sizing** and risk controls

## 📁 Project Structure

```
MartinGales/
├── app/
│   ├── ui/                 # Streamlit user interface
│   ├── config.py          # Configuration management
│   ├── trading_engine.py  # Main trading engine
│   ├── strategies.py      # Trading strategies
│   ├── ibkr_api.py       # IBKR API wrapper
│   └── backtesting_system.py
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Ensure IB Gateway is running
   - Check port configuration (4001 for live, 4002 for paper)
   - Verify API settings in IB Gateway
   - Check firewall settings
   - The IB Gateway must be running on the same machine and before running the trading bot application.

2. **Authentication Error**:
   - Verify IBKR credentials
   - Ensure account has API access enabled
   - Check if account is funded (for live trading)

3. **Module Import Errors**:
   - Ensure virtual environment is activated
   - Reinstall requirements: `pip install -r requirements.txt`


## ⚖️ License

This software is provided for educational and research purposes. Use at your own risk.

---

**Happy Trading! 📈**
