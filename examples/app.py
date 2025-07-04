import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MartinGales Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .status-connected {
        color: #28a745;
        font-weight: bold;
    }
    .status-disconnected {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Dashboard'
if 'ibkr_connected' not in st.session_state:
    st.session_state.ibkr_connected = False
if 'standalone_api' not in st.session_state:
    st.session_state.standalone_api = None
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 0.0
if 'positions_data' not in st.session_state:
    st.session_state.positions_data = pd.DataFrame()
if 'orders_data' not in st.session_state:
    st.session_state.orders_data = pd.DataFrame()
if 'pnl_data' not in st.session_state:
    st.session_state.pnl_data = pd.DataFrame()
if 'market_data' not in st.session_state:
    st.session_state.market_data = {}
if 'strategies' not in st.session_state:
    st.session_state.strategies = []
if 'active_tickers' not in st.session_state:
    st.session_state.active_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
if 'manual_balance' not in st.session_state:
    st.session_state.manual_balance = 250000.0

# Connection retry tracking with exponential backoff
if 'connection_initialized' not in st.session_state:
    st.session_state.connection_initialized = False
if 'last_connection_check' not in st.session_state:
    st.session_state.last_connection_check = None
if 'connection_retry_count' not in st.session_state:
    st.session_state.connection_retry_count = 0
if 'last_connection_attempt' not in st.session_state:
    st.session_state.last_connection_attempt = None
if 'connection_backoff_seconds' not in st.session_state:
    st.session_state.connection_backoff_seconds = 10

def initialize_ibkr_connection(retry_count=0, max_retries=3):
    """Initialize IBKR connection for account data retrieval with exponential backoff"""
    # Update last connection attempt timestamp
    st.session_state.last_connection_attempt = datetime.now()
    
    # Always check if existing connection is still valid after page refresh
    if st.session_state.standalone_api is not None:
        try:
            # Test if the existing connection is still alive
            if hasattr(st.session_state.standalone_api, 'check_connection_health'):
                if st.session_state.standalone_api.check_connection_health():
                    st.session_state.ibkr_connected = True
                    # Reset backoff on successful connection
                    st.session_state.connection_backoff_seconds = 10
                    st.session_state.connection_retry_count = 0
                    return True
                else:
                    # Connection is dead, clean up and recreate
                    st.session_state.standalone_api.disconnect_from_ib()
                    st.session_state.standalone_api = None
                    st.session_state.ibkr_connected = False
        except Exception as e:
            # Connection object is corrupted, clean up
            st.session_state.standalone_api = None
            st.session_state.ibkr_connected = False
    
    if st.session_state.ibkr_connected and st.session_state.standalone_api is not None:
        return True
        
    try:
        from ibkr_api import IBKRApi
        from config import TradingConfig
        
        # Get default config for connection settings
        config = TradingConfig()
        
        # Modify client_id for standalone connection to avoid conflicts
        standalone_config = config.ib_config
        standalone_config.client_id = 999
        
        # Always create a fresh API instance to avoid stale connections
        st.session_state.standalone_api = IBKRApi(
            config=standalone_config,
            account_type=config.account_type
        )
        
        # Attempt to connect to IBKR
        st.info(f"🔄 Attempting to connect to Interactive Brokers... (Attempt {retry_count + 1}/{max_retries + 1})")
        
        if st.session_state.standalone_api.connect_to_ib():
            st.session_state.ibkr_connected = True
            st.success("🔗 Successfully connected to Interactive Brokers for account data")
            
            # Reset backoff and retry count on successful connection
            st.session_state.connection_backoff_seconds = 10
            st.session_state.connection_retry_count = 0
            
            # Request initial data
            try:
                st.session_state.standalone_api.request_positions()
                st.session_state.standalone_api.request_account_updates()
                time.sleep(1)  # Allow time for data to be received
            except Exception as e:
                st.warning(f"Connected but could not request initial data: {str(e)}")
            
            return True
        else:
            raise Exception("Connection failed - no response from IBKR")
            
    except Exception as e:
        error_msg = f"IBKR connection attempt {retry_count + 1} failed: {str(e)}"
        
        # Increment retry count and apply exponential backoff
        st.session_state.connection_retry_count += 1
        
        if retry_count < max_retries:
            backoff_time = min(3 * (2 ** retry_count), 30)  # Cap at 30 seconds
            st.warning(f"⚠️ {error_msg}. Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
            return initialize_ibkr_connection(retry_count + 1, max_retries)
        else:
            # Apply exponential backoff for future attempts
            st.session_state.connection_backoff_seconds = min(st.session_state.connection_backoff_seconds * 2, 300)  # Cap at 5 minutes
            
            st.error(f"❌ {error_msg}. All retry attempts exhausted.")
            st.warning(f"⚠️ Could not connect to Interactive Brokers. Will retry in {st.session_state.connection_backoff_seconds} seconds.")
            st.session_state.ibkr_connected = False
            return False

def check_and_maintain_connection():
    """Check and maintain IBKR connection health with improved error handling and backoff"""
    try:
        # Check if we have an API instance
        if st.session_state.standalone_api is None:
            if not st.session_state.ibkr_connected:
                # Check if enough time has passed since last attempt
                current_time = datetime.now()
                if (st.session_state.last_connection_attempt and 
                    (current_time - st.session_state.last_connection_attempt).total_seconds() < st.session_state.connection_backoff_seconds):
                    return  # Still in backoff period
                
                # Try to re-initialize connection
                initialize_ibkr_connection()
            return
        
        # Check connection health with quick check first
        try:
            # Use quick check to avoid timeout cascades
            is_healthy = st.session_state.standalone_api.check_connection_health(quick_check=True)
            
            if not is_healthy:
                st.session_state.ibkr_connected = False
                
                # Check backoff before attempting reconnection
                current_time = datetime.now()
                if (st.session_state.last_connection_attempt and 
                    (current_time - st.session_state.last_connection_attempt).total_seconds() < st.session_state.connection_backoff_seconds):
                    return  # Still in backoff period
                
                st.warning("🔄 Connection lost, attempting to reconnect...")
                # Try to re-initialize connection
                initialize_ibkr_connection()
            elif not st.session_state.ibkr_connected:
                # Connection is healthy but session state says disconnected
                # This can happen after a page refresh
                st.session_state.ibkr_connected = True
                st.success("🔗 Connection restored")
                # Reset backoff on successful connection
                st.session_state.connection_backoff_seconds = 10
                st.session_state.connection_retry_count = 0
                
        except Exception as api_error:
            # API object might be corrupted
            st.session_state.standalone_api = None
            st.session_state.ibkr_connected = False
            st.warning(f"🔄 API error detected: {str(api_error)}. Reinitializing...")
            
            # Check backoff before attempting reconnection
            current_time = datetime.now()
            if (st.session_state.last_connection_attempt and 
                (current_time - st.session_state.last_connection_attempt).total_seconds() < st.session_state.connection_backoff_seconds):
                return  # Still in backoff period
            
            initialize_ibkr_connection()
            
    except Exception as e:
        st.error(f"❌ Error in connection maintenance: {str(e)}")
        st.session_state.ibkr_connected = False

# Auto-initialize IBKR connection on app start
if not st.session_state.connection_initialized:
    st.session_state.connection_initialized = True
    initialize_ibkr_connection()

# Periodic connection health check (every 30 seconds)
current_time = datetime.now()
if (st.session_state.last_connection_check is None or 
    (current_time - st.session_state.last_connection_check).total_seconds() > 30):
    
    # Only proceed if enough time has passed since last connection attempt
    if (st.session_state.last_connection_attempt is None or 
        (current_time - st.session_state.last_connection_attempt).total_seconds() >= st.session_state.connection_backoff_seconds):
        
        st.session_state.last_connection_check = current_time
        check_and_maintain_connection()

def get_standalone_account_info():
    """Get account information using standalone IBKR connection"""
    if not st.session_state.ibkr_connected or st.session_state.standalone_api is None:
        return None
    
    try:
        # Check connection health before requesting data
        if not st.session_state.standalone_api.check_connection_health():
            st.session_state.ibkr_connected = False
            return None
        
        # Request account summary
        account_info = st.session_state.standalone_api.get_account_summary()
        
        # If no data received immediately, try a brief wait and re-request
        if not account_info:
            time.sleep(1)
            account_info = st.session_state.standalone_api.get_account_summary()
        
        return account_info
        
    except Exception as e:
        st.error(f"Error getting account info: {str(e)}")
        st.session_state.ibkr_connected = False
        return None

def get_standalone_positions():
    """Get positions using standalone IBKR connection"""
    if not st.session_state.ibkr_connected or st.session_state.standalone_api is None:
        return pd.DataFrame()
    
    try:
        # Check connection health before requesting data
        if not st.session_state.standalone_api.check_connection_health():
            st.session_state.ibkr_connected = False
            return pd.DataFrame()
        
        positions = st.session_state.standalone_api.get_positions()
        if positions:
            return pd.DataFrame(positions)
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error getting positions: {str(e)}")
        st.session_state.ibkr_connected = False
        return pd.DataFrame()

def render_sidebar_navigation():
    """Render sidebar navigation with connection status"""
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        # Connection Status
        st.subheader("🔗 Connection Status")
        if st.session_state.ibkr_connected:
            st.markdown('<p class="status-connected">✅ Connected to IBKR</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-disconnected">❌ Disconnected from IBKR</p>', unsafe_allow_html=True)
            if st.button("🔄 Retry Connection"):
                initialize_ibkr_connection()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📊 Navigation")
        
        pages = {
            "📈 Dashboard": "Dashboard",
            "💼 Portfolio": "Portfolio", 
            "📋 Orders": "Orders",
            "🎯 Strategies": "Strategies",
            "⚙️ Settings": "Settings"
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Account Balance Input (when IBKR not connected)
        if not st.session_state.ibkr_connected:
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("💰 Manual Balance")
            new_balance = st.number_input(
                "Account Balance ($)",
                value=st.session_state.manual_balance,
                min_value=0.0,
                step=1000.0,
                format="%.2f"
            )
            if new_balance != st.session_state.manual_balance:
                st.session_state.manual_balance = new_balance
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard():
    """Render main dashboard"""
    # Header
    st.markdown(
        '<div class="main-header"><h1>🏛️ MartinGales Trading Dashboard</h1></div>',
        unsafe_allow_html=True
    )
    
    # Get account data
    account_info = None
    if st.session_state.ibkr_connected:
        account_info = get_standalone_account_info()
    
    # Account Overview Section
    st.subheader("💰 Account Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if account_info and 'TotalCashValue' in account_info:
            balance = float(account_info['TotalCashValue'])
            st.session_state.account_balance = balance
        else:
            balance = st.session_state.manual_balance
        
        st.metric(
            label="Account Balance",
            value=f"${balance:,.2f}",
            delta=f"+${balance * 0.016:,.2f}" if balance > 0 else None
        )
    
    with col2:
        total_equity = balance * 1.0  # Simplified calculation
        st.metric(
            label="Total Equity", 
            value=f"${total_equity:,.2f}",
            delta=f"+${total_equity * 0.016:,.2f}" if total_equity > 0 else None
        )
    
    with col3:
        pnl_percent = 398.70  # Mock data
        st.metric(
            label="P&L %",
            value=f"{pnl_percent:.2f}%",
            delta=f"+{pnl_percent:.2f}%"
        )
    
    with col4:
        buying_power = balance * 0.85  # Simplified calculation
        st.metric(
            label="Buying Power",
            value=f"${buying_power:,.2f}"
        )
    
    # Active Strategies Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Active Strategies")
        strategies_data = [
            {"Strategy": "CDM (Contrarian Dollar-cost averaging)", "Status": "Active", "P&L": "+$1,250"}
        ]
        
        for strategy in strategies_data:
            with st.container():
                st.markdown(f"**{strategy['Strategy']}**")
                col_status, col_pnl = st.columns([2, 1])
                with col_status:
                    st.success(f"✅ {strategy['Status']}")
                with col_pnl:
                    st.write(strategy['P&L'])
    
    with col2:
        st.subheader("📊 Active Tickers")
        
        # Get positions data
        positions_df = get_standalone_positions()
        
        if not positions_df.empty:
            for _, position in positions_df.iterrows():
                with st.container():
                    col_ticker, col_qty, col_value = st.columns([2, 1, 1])
                    with col_ticker:
                        st.write(f"**{position.get('symbol', 'N/A')}**")
                    with col_qty:
                        st.write(f"{position.get('position', 0):.0f}")
                    with col_value:
                        market_value = position.get('marketValue', 0)
                        st.write(f"${market_value:,.2f}")
        else:
            # Show mock data when no real positions
            mock_tickers = ["AAPL"]
            for ticker in mock_tickers:
                with st.container():
                    col_ticker, col_qty, col_value = st.columns([2, 1, 1])
                    with col_ticker:
                        st.write(f"**{ticker}**")
                    with col_qty:
                        st.write("100")
                    with col_value:
                        st.write("$15,000")
    
    # Performance Chart
    st.subheader("📈 Portfolio Performance")
    
    # Generate mock performance data
    dates = pd.date_range(start='2024-01-01', end='2024-12-25', freq='D')
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, len(dates))
    cumulative_returns = (1 + returns).cumprod()
    portfolio_values = balance * cumulative_returns
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio_values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#667eea', width=2)
    ))
    
    fig.update_layout(
        title="Portfolio Performance Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_portfolio():
    """Render portfolio page"""
    st.title("💼 Portfolio Management")
    
    # Get positions data
    positions_df = get_standalone_positions()
    
    if not positions_df.empty:
        st.subheader("Current Positions")
        
        # Display positions table
        display_columns = ['symbol', 'position', 'marketPrice', 'marketValue', 'unrealizedPNL']
        available_columns = [col for col in display_columns if col in positions_df.columns]
        
        if available_columns:
            st.dataframe(
                positions_df[available_columns],
                use_container_width=True
            )
        else:
            st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No positions data available. Connect to IBKR to view real positions.")
        
        # Show sample data structure
        st.subheader("Sample Portfolio View")
        sample_data = {
            'Symbol': ['AAPL', 'GOOGL', 'MSFT'],
            'Position': [100, 50, 75],
            'Market Price': [150.00, 2500.00, 300.00],
            'Market Value': [15000.00, 125000.00, 22500.00],
            'Unrealized P&L': [1500.00, 12500.00, 2250.00]
        }
        st.dataframe(pd.DataFrame(sample_data), use_container_width=True)

def render_orders():
    """Render orders page"""
    st.title("📋 Order Management")
    st.info("Order management functionality will be implemented here.")

def render_strategies():
    """Render strategies page"""
    st.title("🎯 Trading Strategies")
    st.info("Strategy management functionality will be implemented here.")

def render_settings():
    """Render settings page"""
    st.title("⚙️ Settings")
    
    st.subheader("IBKR Connection Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("TWS/Gateway Host", value="127.0.0.1", disabled=True)
        st.number_input("Port", value=7497, disabled=True)
    
    with col2:
        st.number_input("Client ID", value=999, disabled=True)
        st.selectbox("Account Type", ["Paper", "Live"], index=0, disabled=True)
    
    st.info("Connection settings are currently read-only. Modify config.py to change these values.")
    
    if st.button("Test Connection"):
        initialize_ibkr_connection()
        st.rerun()

# Main app logic
def main():
    """Main application logic"""
    # Render sidebar
    render_sidebar_navigation()
    
    # Render main content based on current page
    if st.session_state.current_page == "Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "Portfolio":
        render_portfolio()
    elif st.session_state.current_page == "Orders":
        render_orders()
    elif st.session_state.current_page == "Strategies":
        render_strategies()
    elif st.session_state.current_page == "Settings":
        render_settings()
    else:
        render_dashboard()  # Default fallback

if __name__ == "__main__":
    main()