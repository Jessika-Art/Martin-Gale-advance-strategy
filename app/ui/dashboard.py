import streamlit as st
import pandas as pd
import time
import json
import os
from datetime import datetime
import sys

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control_panel import ControlPanel
from trading_engine import TradingEngine
from config import TradingConfig, StrategyType

def render_title_with_tooltip(title: str, tooltip: str, level: str = "subheader"):
    """Render a title with a tooltip question mark icon"""
    col1, col2 = st.columns([0.95, 0.05])
    with col1:
        if level == "header":
            st.header(title)
        elif level == "subheader":
            st.subheader(title)
        elif level == "markdown":
            st.markdown(f"### {title}")
    with col2:
        st.markdown(f"<div title='{tooltip}' style='cursor: help; font-size: 16px; color: #666; margin-top: 8px;'>❓</div>", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="MartinGales Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar-section {
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'trading_engine' not in st.session_state:
    st.session_state.trading_engine = None
if 'control_panel' not in st.session_state:
    st.session_state.control_panel = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def initialize_components():
    """Initialize trading components"""
    if st.session_state.control_panel is None:
        st.session_state.control_panel = ControlPanel()
        # Try to load existing configuration
        config_files = ['demo_single.json', 'demo_multiple.json', 'config.json']
        for config_file in config_files:
            if os.path.exists(config_file):
                st.session_state.control_panel.load_config(config_file)
                break
        else:
            # Create default configuration if none exists
            config = TradingConfig()
            config.tickers = ['AAPL']
            config.active_strategies = [StrategyType.CDM]
            st.session_state.control_panel.config = config

def start_trading():
    """Start the trading engine"""
    try:
        if st.session_state.control_panel and st.session_state.control_panel.config:
            st.session_state.trading_engine = TradingEngine(st.session_state.control_panel.config)
            st.session_state.is_running = True
            st.success("Trading engine started successfully!")
        else:
            st.error("No configuration loaded. Please configure the bot first.")
    except Exception as e:
        st.error(f"Failed to start trading engine: {str(e)}")
        st.session_state.is_running = False

def stop_trading():
    """Stop the trading engine"""
    try:
        if st.session_state.trading_engine:
            st.session_state.trading_engine.stop()
            st.session_state.trading_engine = None
        st.session_state.is_running = False
        st.success("Trading engine stopped successfully!")
    except Exception as e:
        st.error(f"Failed to stop trading engine: {str(e)}")

def get_account_info():
    """Get account information from trading engine"""
    if st.session_state.trading_engine and st.session_state.trading_engine.api:
        try:
            api = st.session_state.trading_engine.api
            
            # Request fresh account data
            api.request_account_summary()
            api.request_positions()
            time.sleep(0.5)  # Allow time for data to be received
            
            account_info = api.account_info
            
            if not account_info:
                return None
                
            # Get real account data from IBKR API
            net_liquidation = account_info.get('NetLiquidation', 0.0)
            total_cash = account_info.get('TotalCashValue', 0.0)
            buying_power = account_info.get('BuyingPower', 0.0)
            available_funds = account_info.get('AvailableFunds', 0.0)
            
            # Calculate total unrealized P&L from all positions
            total_unrealized_pnl = 0.0
            for symbol, ib_position in api.positions.items():
                if ib_position.position != 0:
                    # Get current market price
                    market_data = api.get_market_data(symbol)
                    current_price = market_data.price if market_data else ib_position.avg_cost
                    
                    # Calculate unrealized P&L for this position
                    position_value = ib_position.position * current_price
                    cost_basis = ib_position.position * ib_position.avg_cost
                    unrealized_pnl = position_value - cost_basis
                    total_unrealized_pnl += unrealized_pnl
                    
                    # Update the position object with current data
                    ib_position.market_price = current_price
                    ib_position.market_value = abs(position_value)
                    ib_position.unrealized_pnl = unrealized_pnl
            
            # Calculate P&L metrics - use configured starting balance
            config = st.session_state.control_panel.config if st.session_state.control_panel else None
            configured_starting_balance = config.shared_settings.initial_balance if config else 50000.0
            
            # Calculate P&L based on total equity vs starting balance
            pnl = net_liquidation - configured_starting_balance
            pnl_percent = (pnl / configured_starting_balance * 100) if configured_starting_balance > 0 else 0.0
            
            return {
                'balance': total_cash,
                'equity': net_liquidation,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'buying_power': buying_power,
                'margin_used': net_liquidation - available_funds if available_funds > 0 else 0.0
            }
        except Exception as e:
            st.error(f"Error fetching account info: {str(e)}")
            return None
    return None

def close_position(symbol: str, quantity: int):
    """Close a position by placing a market order"""
    try:
        # Import here to avoid circular imports
        from strategies import OrderRequest, OrderAction
        
        # Get the API instance
        api = None
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            api = st.session_state.trading_engine.api
        elif st.session_state.ibkr_connected and st.session_state.standalone_api:
            api = st.session_state.standalone_api
        
        if not api:
            st.error("No API connection available")
            return False
        
        # Determine the action (opposite of current position)
        action = OrderAction.SELL if quantity > 0 else OrderAction.BUY
        close_quantity = abs(quantity)
        
        # Create order request to close position
        order_request = OrderRequest(
            symbol=symbol,
            action=action,
            quantity=close_quantity,
            order_type="MKT"  # Market order for immediate execution
        )
        
        # Place the order
        order_id = api.place_order(order_request)
        
        if order_id:
            st.success(f"Close order placed for {symbol}: {action.value} {close_quantity} shares (Order ID: {order_id})")
            # Refresh the page to update positions
            time.sleep(1)
            st.rerun()
            return True
        else:
            st.error(f"Failed to place close order for {symbol}")
            return False
            
    except Exception as e:
        st.error(f"Error closing position for {symbol}: {str(e)}")
        return False

def get_positions():
    """Get current positions from trading engine or standalone API"""
    # First try trading engine API
    if st.session_state.trading_engine and st.session_state.trading_engine.api:
        try:
            api = st.session_state.trading_engine.api
            positions_data = []
            
            # Get real positions from IBKR API
            for symbol, ib_position in api.positions.items():
                if ib_position.position != 0:  # Only show non-zero positions
                    # Get current market data for the symbol
                    market_data = api.get_market_data(symbol)
                    current_price = market_data.price if market_data else ib_position.avg_cost
                    
                    # Calculate market value and P&L
                    market_value = abs(ib_position.position) * current_price
                    
                    # Calculate unrealized P&L properly
                    position_value = ib_position.position * current_price
                    cost_basis = ib_position.position * ib_position.avg_cost
                    unrealized_pnl = position_value - cost_basis
                    
                    # Calculate unrealized P&L percentage
                    cost_basis_abs = abs(ib_position.position) * ib_position.avg_cost
                    unrealized_pnl_percent = (unrealized_pnl / cost_basis_abs * 100) if cost_basis_abs > 0 else 0.0
                    
                    # Update the position object with current data
                    ib_position.market_price = current_price
                    ib_position.market_value = market_value
                    ib_position.unrealized_pnl = unrealized_pnl
                    
                    positions_data.append({
                        'symbol': symbol,
                        'quantity': int(ib_position.position),
                        'avg_price': ib_position.avg_cost,
                        'current_price': current_price,
                        'market_value': market_value,
                        'unrealized_pnl': unrealized_pnl,
                        'unrealized_pnl_percent': unrealized_pnl_percent
                    })
            
            return positions_data
        except Exception as e:
            st.error(f"Error fetching positions from trading engine: {str(e)}")
    
    # Fallback to standalone API if available
    if st.session_state.ibkr_connected and st.session_state.standalone_api:
        try:
            api = st.session_state.standalone_api
            positions_data = []
            
            # Get positions from standalone API
            if hasattr(api, 'positions') and api.positions:
                for symbol, ib_position in api.positions.items():
                    if ib_position.position != 0:  # Only show non-zero positions
                        # Get current market data for the symbol
                        market_data = api.get_market_data(symbol) if hasattr(api, 'get_market_data') else None
                        current_price = market_data.price if market_data else ib_position.avg_cost
                        
                        # Calculate market value and P&L
                        market_value = abs(ib_position.position) * current_price
                        
                        # Calculate unrealized P&L properly
                        position_value = ib_position.position * current_price
                        cost_basis = ib_position.position * ib_position.avg_cost
                        unrealized_pnl = position_value - cost_basis
                        
                        # Calculate unrealized P&L percentage
                        cost_basis_abs = abs(ib_position.position) * ib_position.avg_cost
                        unrealized_pnl_percent = (unrealized_pnl / cost_basis_abs * 100) if cost_basis_abs > 0 else 0.0
                        
                        # Update the position object with current data
                        ib_position.market_price = current_price
                        ib_position.market_value = market_value
                        ib_position.unrealized_pnl = unrealized_pnl
                        
                        positions_data.append({
                            'symbol': symbol,
                            'quantity': int(ib_position.position),
                            'avg_price': ib_position.avg_cost,
                            'current_price': current_price,
                            'market_value': market_value,
                            'unrealized_pnl': unrealized_pnl,
                            'unrealized_pnl_percent': unrealized_pnl_percent
                        })
                
                return positions_data
        except Exception as e:
            st.error(f"Error fetching positions from standalone API: {str(e)}")
    
    return []

# Initialize components
initialize_components()

# Sidebar rendering is handled by app.py
# This prevents duplicate sidebar content

def render_dashboard():
    """Render the main dashboard content"""
    # Main Content Area
    st.markdown('<h1 class="main-header">📈 MartinGales Trading Dashboard</h1>', unsafe_allow_html=True)

    # Configuration Status
    if st.session_state.control_panel and st.session_state.control_panel.config:
        config = st.session_state.control_panel.config
        
        # Strategy and Ticker Status
        col1, col2 = st.columns(2)
        
        with col1:
            render_title_with_tooltip(
                "🎯 Active Strategies", 
                "Currently configured trading strategies that will be used for automated trading",
                "subheader"
            )
            if config.active_strategies:
                strategy_names = {
                    'cdm': 'CDM (Contrarian Dollar-cost averaging)',
                    'wdm': 'WDM (Weighted Dollar-cost averaging)', 
                    'zrm': 'ZRM (Zero-Risk Martingale)',
                    'izrm': 'IZRM (Inverse Zero-Risk Martingale)'
                }
                for strategy in config.active_strategies:
                    strategy_key = strategy.value if hasattr(strategy, 'value') else str(strategy)
                    strategy_display = strategy_names.get(strategy_key, strategy_key.upper())
                    st.success(f"✅ {strategy_display}")
            else:
                st.warning("⚠️ No strategies selected")
        
        with col2:
            render_title_with_tooltip(
                "📊 Active Tickers", 
                "Stock symbols that are being monitored and traded by the active strategies",
                "subheader"
            )
            if config.tickers:
                for ticker in config.tickers:
                    st.info(f"📈 {ticker}")
            else:
                st.warning("⚠️ No tickers selected")

    st.divider()

    # Account Overview Section
    render_title_with_tooltip(
        "💰 Account Overview", 
        "Real-time account information including balance, equity, profit/loss, and buying power from your broker",
        "subheader"
    )
    account_info = get_account_info()
    
    # Also check standalone API connection for account data
    standalone_account_info = None
    if st.session_state.ibkr_connected and st.session_state.standalone_api:
        try:
            api = st.session_state.standalone_api
            if hasattr(api, 'account_info') and api.account_info:
                account_data = api.account_info
                net_liquidation = account_data.get('NetLiquidation', 0.0)
                total_cash = account_data.get('TotalCashValue', 0.0)
                buying_power = account_data.get('BuyingPower', 0.0)
                
                # Calculate P&L metrics
                config = st.session_state.control_panel.config if st.session_state.control_panel else None
                configured_starting_balance = config.shared_settings.initial_balance if config else 50000.0
                
                # Calculate P&L based on total equity vs starting balance
                pnl = net_liquidation - configured_starting_balance
                pnl_percent = (pnl / configured_starting_balance * 100) if configured_starting_balance > 0 else 0.0
                
                standalone_account_info = {
                    'balance': total_cash,
                    'equity': net_liquidation,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'buying_power': buying_power
                }
        except Exception as e:
            pass
    
    # Use trading engine account info if available, otherwise use standalone API
    display_account_info = account_info or standalone_account_info

    if display_account_info:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Account Balance",
                value=f"${display_account_info['balance']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Total Equity",
                value=f"${display_account_info['equity']:,.2f}",
                delta=f"${display_account_info['pnl']:,.2f}"
            )
        
        with col3:
            st.metric(
                label="P&L %",
                value=f"{display_account_info['pnl_percent']:.2f}%",
                delta=f"{display_account_info['pnl_percent']:.2f}%"
            )
        
        with col4:
            st.metric(
                label="Buying Power",
                value=f"${display_account_info['buying_power']:,.2f}",
                delta=None
            )
        
        # Show helpful info about P&L calculation
        st.info(
            "💡 **P&L Calculation**: P&L is calculated based on your configured starting balance. "
            "To ensure accurate P&L tracking, make sure your 'Initial Account Balance' in the configuration matches your actual starting balance when you began trading."
        )
        
        # Show connection source
        if account_info:
            st.caption("📊 Data from Trading Engine")
        elif standalone_account_info:
            st.caption("📊 Data from Standalone IBKR Connection")
    else:
        # Show different messages based on connection status
        if st.session_state.ibkr_connected:
            st.info("📊 Connected to IBKR. Account data will appear shortly...")
        else:
            st.info("Account information will be available when connected to Interactive Brokers.")

    # Positions Section
    render_title_with_tooltip(
        "📊 Current Positions", 
        "All currently open positions with real-time market values, unrealized P&L, and quick close options",
        "subheader"
    )
    positions = get_positions()

    if positions:
        # Add header row
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1.2, 1.2, 1.5, 1.5, 1.5, 1])
        with col1:
            st.write("**Symbol**")
        with col2:
            st.write("**Qty**")
        with col3:
            st.write("**Avg Price**")
        with col4:
            st.write("**Current**")
        with col5:
            st.write("**Market Value**")
        with col6:
            st.write("**Unrealized P&L**")
        with col7:
            st.write("**P&L %**")
        with col8:
            st.write("**Action**")
        
        st.markdown("---")
        
        # Display positions with close buttons
        for i, position in enumerate(positions):
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1.2, 1.2, 1.5, 1.5, 1.5, 1])
            
            with col1:
                st.write(f"{position['symbol']}")
            with col2:
                st.write(f"{position['quantity']}")
            with col3:
                st.write(f"${position['avg_price']:.2f}")
            with col4:
                st.write(f"${position['current_price']:.2f}")
            with col5:
                st.write(f"${position['market_value']:,.2f}")
            with col6:
                pnl_color = "green" if position['unrealized_pnl'] >= 0 else "red"
                st.markdown(f"<span style='color: {pnl_color}'>${position['unrealized_pnl']:,.2f}</span>", unsafe_allow_html=True)
            with col7:
                pnl_percent_color = "green" if position['unrealized_pnl_percent'] >= 0 else "red"
                st.markdown(f"<span style='color: {pnl_percent_color}'>{position['unrealized_pnl_percent']:.2f}%</span>", unsafe_allow_html=True)
            with col8:
                # Close position button
                if st.button("❌ Close", key=f"close_{position['symbol']}_{i}", help=f"Close {position['symbol']} position", type="secondary"):
                    with st.spinner(f"Closing {position['symbol']} position..."):
                        close_position(position['symbol'], position['quantity'])
        
    else:
        st.info("No positions currently open.")

    # Trading Activity Section
    render_title_with_tooltip(
        "📈 Recent Trading Activity", 
        "Live feed of recent trades, orders, and trading engine activity",
        "subheader"
    )
    if st.session_state.is_running:
        st.info("Trading activity will be displayed here when trades are executed.")
        
        # Placeholder for recent trades table
        st.write("Recent trades will appear here...")
    else:
        st.info("Start the trading engine to see trading activity.")

    # Footer
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: #666;'>"
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"MartinGales Trading Bot v1.0"
        f"</p>", 
        unsafe_allow_html=True
    )