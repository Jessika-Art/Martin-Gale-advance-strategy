# MartinGales Trading Bot 📈

Hey there! Welcome to my MartinGales trading bot project. This is basically a fancy automated trading system that uses multiple Martingale strategies to trade stocks through Interactive Brokers.

## What's This All About? 🤔

So, this trading bot is designed to run different Martingale strategies on various stocks. It's got a nice web interface where you can:

- Monitor your trades in real-time
- Configure different strategies (CDM, WDM, ZRM, IZRM)
- Manage risk and position sizing
- Backtest your strategies
- Track performance and analytics

The bot connects to Interactive Brokers to execute actual trades, so it's the real deal - not just a simulation.

## Before You Start! ⚠️

**SUPER IMPORTANT**: You MUST have IBGateway (Interactive Brokers Gateway) running before you start the application. The bot won't work without it because that's how it talks to Interactive Brokers.

Make sure IBGateway is:
1. Installed on your computer
2. Running and connected
3. Configured with the right account (demo or live)

## How to Run This Thing 🚀

### Option 1: Web Interface (Recommended)

This is the fancy way with a nice web UI:

```cmd
# First, navigate to the UI folder
cd app/ui

# Install the required packages (do this once)
pip install -r requirements.txt

# Run the web interface
streamlit run app.py
```

Then open your browser and go to the URL that shows up (usually `http://localhost:8501`).

### Option 2: Command Line Interface

If you're more of a terminal person:

```cmd
# Navigate to the app folder
cd app

# Run the UI script
streamlit run app.py
```

This gives you a text-based menu where you can configure everything and start trading.

## What You Need Installed 📦

The main stuff you need:
- Python 3.8 or newer
- Interactive Brokers Gateway (IBGateway)
- All the Python packages listed in `app/ui/requirements.txt`

The bot uses these main libraries:
- Streamlit (for the web interface)
- Plotly (for charts and graphs)
- Pandas (for data handling)
- IBApi (to talk to Interactive Brokers)

## Quick Setup Guide 🛠️

1. **Get IBGateway running** - This is crucial!
2. **Install Python dependencies**:
   ```cmd
   cd app/ui
   pip install -r requirements.txt
   ```
3. **Run the app**:
   ```cmd
   streamlit run app.py
   ```
4. **Configure your settings** in the web interface
5. **Start trading** (carefully!)

## Features 🎯

- **Multiple Strategies**: CDM, WDM, ZRM, and IZRM Martingale strategies
- **Real-time Monitoring**: See your trades and P&L live
- **Risk Management**: Built-in position sizing and risk controls
- **Backtesting**: Test your strategies on historical data
- **Performance Analytics**: Track how you're doing
- **Web Interface**: Easy-to-use dashboard
- **Demo Mode**: Practice with paper trading first

## Important Notes 📝

- **Start with demo mode** if you're new to this
- **The bot trades real money** when in live mode - be careful!
- **Always have IBGateway running** before starting the app
- **Monitor your trades** - don't just set it and forget it
- **Understand the risks** - Martingale strategies can be risky

## File Structure 📁

```
MartinGales/
├── app/
│   ├── ui/                 # Web interface files
│   │   ├── app.py         # Main Streamlit app
│   │   └── requirements.txt
│   ├── main.py            # Command line interface
│   ├── strategies.py      # Trading strategies
│   ├── config.py          # Configuration management
│   └── ... (other modules)
└── README.md              # This file!
```

## Getting Help 🆘

If something's not working:
1. Check that IBGateway is running
2. Make sure all Python packages are installed
3. Check the logs for error messages
4. Try restarting IBGateway and the app

## Disclaimer ⚖️

This is trading software that deals with real money. Use it at your own risk! I'm not responsible if you lose money. Always test with demo accounts first and never risk more than you can afford to lose.

Happy trading! 🎉

---

*P.S. - If you're reading this and thinking "this person seems pretty casual about a trading bot," you're right. But don't worry, the code is serious business even if the README isn't!*