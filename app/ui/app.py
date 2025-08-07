import streamlit as st
import sys
import os
import time
from datetime import datetime, timedelta

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dashboard components
from dashboard import *
from config_manager import render_config_manager
from performance import render_performance_analytics
from backtesting_ui import render_backtesting_interface
from cycle_analysis_ui import render_cycle_analysis_page
from money_management_ui import render_money_management_page
from risk_management_ui import render_risk_management_page

# Page configuration
st.set_page_config(
    page_title="MartinGales Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Navigation styling */
    .nav-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    
    /* Status indicators */
    .status-running {
        color: #28a745;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .sidebar-divider {
        border-top: 1px solid #e0e0e0;
        margin: 1rem 0;
        width: 100%;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        border-top: 1px solid #e0e0e0;
        margin-top: 3rem;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Initialize trading components
if 'trading_engine' not in st.session_state:
    st.session_state.trading_engine = None
if 'control_panel' not in st.session_state:
    st.session_state.control_panel = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'ibkr_connected' not in st.session_state:
    st.session_state.ibkr_connected = False
if 'standalone_api' not in st.session_state:
    st.session_state.standalone_api = None

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

# Initialize connection retry tracking with exponential backoff
if 'connection_initialized' not in st.session_state:
    st.session_state.connection_initialized = False
if 'last_connection_check' not in st.session_state:
    st.session_state.last_connection_check = datetime.now()
if 'connection_retry_count' not in st.session_state:
    st.session_state.connection_retry_count = 0
if 'last_connection_attempt' not in st.session_state:
    st.session_state.last_connection_attempt = datetime.now() - timedelta(minutes=5)
if 'connection_backoff_seconds' not in st.session_state:
    st.session_state.connection_backoff_seconds = 10

# Initialize IBKR connection automatically when app starts
if not st.session_state.connection_initialized:
    st.session_state.connection_initialized = True
    initialize_ibkr_connection()

# Periodic connection health check with exponential backoff
current_time = datetime.now()
time_since_last_check = (current_time - st.session_state.last_connection_check).seconds
time_since_last_attempt = (current_time - st.session_state.last_connection_attempt).seconds

# Only check connection health if enough time has passed and we're not in backoff period
if time_since_last_check >= 30 and time_since_last_attempt >= st.session_state.connection_backoff_seconds:
    st.session_state.last_connection_check = current_time
    check_and_maintain_connection()

def get_standalone_account_info():
    """Get account information from standalone API connection"""
    if st.session_state.ibkr_connected and st.session_state.standalone_api:
        try:
            api = st.session_state.standalone_api
            
            # Check connection health before requesting data
            if not api.check_connection_health():
                st.session_state.ibkr_connected = False
                return None
            
            # Request fresh account data
            api.request_account_summary()
            time.sleep(0.5)  # Allow time for data to be received
            
            account_info = api.account_info
            
            if not account_info:
                # Try to request data again
                api.request_account_summary()
                time.sleep(1)
                account_info = api.account_info
                
            if not account_info:
                return None
                
            # Get real account data from IBKR API
            net_liquidation = account_info.get('NetLiquidation', 0.0)
            total_cash = account_info.get('TotalCashValue', 0.0)
            buying_power = account_info.get('BuyingPower', 0.0)
            available_funds = account_info.get('AvailableFunds', 0.0)
            
            # Request positions data to calculate real P&L
            api.request_positions()
            time.sleep(0.3)  # Allow time for positions data
            
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
            
            # Calculate P&L based on configured starting balance
            from config import TradingConfig
            config = TradingConfig()
            configured_starting_balance = config.shared_settings.initial_balance
            
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
            st.warning(f"Error fetching account info: {str(e)}")
            st.session_state.ibkr_connected = False
            return None
    return None

def get_standalone_positions():
    """Get current positions from standalone API connection"""
    if st.session_state.ibkr_connected and st.session_state.standalone_api:
        try:
            api = st.session_state.standalone_api
            
            # Check connection health before requesting data
            if not api.check_connection_health():
                st.session_state.ibkr_connected = False
                return []
            
            # Request fresh positions data
            api.request_positions()
            time.sleep(0.5)  # Allow time for data to be received
            
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
            st.warning(f"Error fetching positions: {str(e)}")
            st.session_state.ibkr_connected = False
            return []
    return []

def render_sidebar_navigation():
    """Render sidebar navigation and controls"""
    with st.sidebar:
        # App title and logo
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: #1f77b4; margin-bottom: 0;">📈</h1>
            <h2 style="color: #1f77b4; margin-top: 0;">MartinGales</h2>
            <p style="color: #666; font-size: 0.9rem;">Advanced Trading Bot</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu
        st.markdown('<div class="nav-section">', unsafe_allow_html=True)
        st.subheader("🧭 Navigation")
        
        # Navigation buttons
        pages = {
            "📊 Dashboard": "Dashboard",
            "⚙️ Configuration": "Configuration",
            "📈 Performance": "Performance",
            "🧪 Backtesting": "Backtesting",
            "🔄 Cycle Analysis": "CycleAnalysis",
            "💰 Money Management": "MoneyManagement",
            "🛡️ Risk Management": "RiskManagement",
            "ℹ️ About": "About"
        }
        
        for page_label, page_key in pages.items():
            if st.button(page_label, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Connection and Trading status
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.subheader("🎛️ System Status")
        
        # IBKR Connection Status
        if st.session_state.ibkr_connected:
            st.markdown('<p class="status-running">🟢 IBKR CONNECTED</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-stopped">🔴 IBKR DISCONNECTED</p>', unsafe_allow_html=True)
            if st.button("🔄 Retry Connection", key="retry_connection"):
                initialize_ibkr_connection()
                st.rerun()
        
        # Trading Status
        st.write("**Trading Bot:**")
        if st.session_state.is_running:
            st.markdown('<p class="status-running">🟢 RUNNING</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-stopped">🔴 STOPPED</p>', unsafe_allow_html=True)
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ START", disabled=st.session_state.is_running, key="start_btn"):
                start_trading_from_sidebar()
        
        with col2:
            if st.button("⏹️ STOP", disabled=not st.session_state.is_running, key="stop_btn"):
                stop_trading_from_sidebar()
        
        # Emergency stop
        if st.session_state.is_running:
            if st.button("🚨 EMERGENCY STOP", key="emergency_stop", help="Immediately stop all trading"):
                emergency_stop()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Strategy Selection Section
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.subheader("🎯 Strategy Selection")
        
        # Initialize config if needed
        if st.session_state.control_panel is None:
            from control_panel import ControlPanel
            from config import TradingConfig
            st.session_state.control_panel = ControlPanel()
            st.session_state.control_panel.config = TradingConfig()
        
        config = st.session_state.control_panel.config
        if config is None:
            from config import TradingConfig
            config = TradingConfig()
            st.session_state.control_panel.config = config
        
        # Strategy toggles
        from config import StrategyType
        available_strategies = ['cdm', 'wdm', 'zrm', 'izrm']
        strategy_names = {
            'cdm': 'CDM (Contrarian Dollar-cost averaging)',
            'wdm': 'WDM (Weighted Dollar-cost averaging)', 
            'zrm': 'ZRM (Zero-Risk Martingale)',
            'izrm': 'IZRM (Inverse Zero-Risk Martingale)'
        }
        
        # Map string to enum
        strategy_enum_map = {
            'cdm': StrategyType.CDM,
            'wdm': StrategyType.WDM,
            'zrm': StrategyType.ZRM,
            'izrm': StrategyType.IZRM
        }
        
        st.write("**Select Strategies:**")
        for strategy in available_strategies:
            strategy_enum = strategy_enum_map[strategy]
            current_active = strategy_enum in config.active_strategies
            new_active = st.checkbox(strategy_names[strategy], value=current_active, key=f"strategy_{strategy}")
            
            # Only update if the state changed
            if new_active != current_active:
                config.enable_strategy(strategy_enum, new_active)
        
        # Timeframe Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("⏰ Timeframe Selection")
        
        # Available timeframes
        available_timeframes = ["1 min", "5 mins", "15 mins", "30 mins", "1 hour", "2 hours", "4 hours", "1 day", "1 week", "1 month"]
        current_timeframe = config.timeframe
        
        # Timeframe selector
        selected_timeframe = st.selectbox(
            "Select Timeframe:",
            available_timeframes,
            index=available_timeframes.index(current_timeframe) if current_timeframe in available_timeframes else 0,
            key="timeframe_selector"
        )
        
        # Check if timeframe changed and bot is running
        if selected_timeframe != current_timeframe:
            config.timeframe = selected_timeframe
            
            # If bot is running, show restart notification
            if st.session_state.is_running:
                st.warning("⚠️ Timeframe changed! Bot needs to restart.")
                if st.button("🔄 Restart Bot", key="restart_bot_timeframe"):
                    restart_bot_with_new_timeframe()
            else:
                st.success(f"✅ Timeframe set to {selected_timeframe}")
        
        # Display current timeframe info
        st.info(f"Current: {config.timeframe}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Shared Settings Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("⚙️ Account Settings")
        
        # Get real account balance from standalone IBKR connection
        if st.session_state.ibkr_connected and st.session_state.standalone_api:
            account_info = get_standalone_account_info()
            if account_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Account Balance",
                        f"${account_info['equity']:,.2f}",
                        delta=f"P&L: ${account_info['pnl']:,.2f}",
                        help="Live balance from IBKR account"
                    )
                with col2:
                    st.metric(
                        "Buying Power",
                        f"${account_info['buying_power']:,.2f}",
                        delta=f"{account_info['pnl_percent']:.2f}%",
                        help="Available buying power"
                    )
                
                # Update config with real balance
                if st.session_state.control_panel and st.session_state.control_panel.config:
                    st.session_state.control_panel.config.shared_settings.initial_balance = account_info['equity']
            else:
                st.warning("⚠️ Could not retrieve account data. Connection may be lost.")
        else:
            st.warning("⚠️ Not connected to IBKR. Cannot retrieve real account balance.")
            current_balance = config.shared_settings.initial_balance
            new_balance = st.number_input(
                "Initial Account Balance ($):",
                min_value=1000.0,
                max_value=1000000.0,
                value=current_balance,
                step=1000.0,
                help="Set your starting account balance for accurate P&L calculation",
                key="initial_balance_input"
            )
            
            if new_balance != current_balance:
                config.shared_settings.initial_balance = new_balance
                st.success(f"✅ Initial balance set to ${new_balance:,.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Ticker Selection Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📊 Ticker Selection")
        
        # Current tickers display
        st.write("**Active Tickers:**")
        if config.tickers:
            for i, ticker in enumerate(config.tickers):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {ticker}")
                with col2:
                    if st.button("❌", key=f"remove_ticker_{ticker}_{i}", help=f"Remove {ticker}"):
                        config.tickers.remove(ticker)
                        st.rerun()
        else:
            st.info("No tickers selected")
        
        # Add new ticker
        new_ticker = st.text_input("Add Ticker:", placeholder="e.g., AAPL", key="sidebar_new_ticker")
        if st.button("➕ Add Ticker", key="sidebar_add_ticker"):
            if new_ticker and new_ticker.upper() not in config.tickers:
                config.tickers.append(new_ticker.upper())
                st.success(f"Added {new_ticker.upper()}")
                st.rerun()
            elif new_ticker.upper() in config.tickers:
                st.warning(f"{new_ticker.upper()} already exists")
        
        # Quick ticker presets
        st.write("**Quick Add:**")
        preset_tickers = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
        cols = st.columns(3)
        for i, ticker in enumerate(preset_tickers):
            with cols[i % 3]:
                if st.button(ticker, key=f"preset_{ticker}", help=f"Add {ticker}"):
                    if ticker not in config.tickers:
                        config.tickers.append(ticker)
                        st.success(f"Added {ticker}")
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        

        
        # Configuration Management Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("💾 Configuration")
        
        # Save current configuration
        config_name = st.text_input("Config Name:", value="my_config", key="sidebar_config_name")
        if st.button("💾 Save Config", key="sidebar_save_config"):
            if config_name:
                try:
                    filename = f"{config_name}.json"
                    st.session_state.control_panel.save_config(filename)
                    st.success(f"Saved as {filename}")
                except Exception as e:
                    st.error(f"Failed to save: {str(e)}")
        
        # Load configuration
        config_files = [f for f in os.listdir('.') if f.endswith('.json')]
        if config_files:
            selected_config = st.selectbox("Load Config:", config_files, key="sidebar_load_config")
            if st.button("📂 Load", key="sidebar_load_btn"):
                try:
                    st.session_state.control_panel.load_config(selected_config)
                    st.success(f"Loaded {selected_config}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Account Overview section removed - now displayed in main area only
        
        # Current Positions - Show when connected to IBKR
        if st.session_state.ibkr_connected:
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("📈 Current Positions")
            
            # Get positions from appropriate source
            if st.session_state.is_running:
                positions = get_positions()
            else:
                positions = get_standalone_positions()
            
            if positions and len(positions) > 0:
                for pos in positions[:3]:  # Show max 3 positions in sidebar
                    with st.container():
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**{pos['symbol']}**")
                            st.write(f"{pos['quantity']} shares")
                        with col2:
                             # Handle both 'pnl' (from trading engine) and 'unrealized_pnl' (from standalone API)
                             pnl_value = pos.get('pnl', pos.get('unrealized_pnl', 0))
                             pnl_color = "green" if pnl_value >= 0 else "red"
                             st.markdown(f"<span style='color: {pnl_color}'>${pnl_value:,.2f}</span>", unsafe_allow_html=True)
                        st.divider()
                
                if len(positions) > 3:
                    st.write(f"... and {len(positions) - 3} more positions")
            else:
                st.write("No open positions")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # System info
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("🖥️ System Info")
        
        # Connection status
        connection_status = check_connection_status()
        if connection_status == "connected":
            st.markdown('<p style="color: green;">🟢 IB Gateway Connected</p>', unsafe_allow_html=True)
        elif connection_status == "connecting":
            st.markdown('<p class="status-warning loading">🟡 Connecting...</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color: red;">🔴 Disconnected</p>', unsafe_allow_html=True)
        
        # Last update time
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Manual refresh button
        if st.button("🔄 Refresh", key="manual_refresh", help="Refresh dashboard data"):
            # Update connection check time and trigger refresh
            st.session_state.last_connection_check = datetime.now()
            check_and_maintain_connection()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def start_trading_from_sidebar():
    """Start trading from sidebar controls"""
    try:
        initialize_components()
        if st.session_state.control_panel and st.session_state.control_panel.config:
            from trading_engine import TradingEngine
            st.session_state.trading_engine = TradingEngine(st.session_state.control_panel.config)
            
            # Actually start the engine
            if st.session_state.trading_engine.start():
                st.session_state.is_running = True
                st.success("✅ Trading engine started successfully!")
            else:
                st.session_state.is_running = False
                st.error("❌ Failed to start trading engine")
        else:
            st.error("❌ No configuration loaded. Please configure the bot first.")
    except Exception as e:
        st.error(f"❌ Failed to start trading engine: {str(e)}")
        st.session_state.is_running = False

def stop_trading_from_sidebar():
    """Stop trading from sidebar controls"""
    try:
        if st.session_state.trading_engine:
            st.session_state.trading_engine.stop()
            st.session_state.trading_engine = None
        st.session_state.is_running = False
        # Clean up refresh timers to prevent memory leaks
        if 'last_refresh_time' in st.session_state:
            del st.session_state.last_refresh_time
        if 'last_dashboard_refresh' in st.session_state:
            del st.session_state.last_dashboard_refresh
        st.success("✅ Trading engine stopped successfully!")
    except Exception as e:
        st.error(f"❌ Failed to stop trading engine: {str(e)}")

def emergency_stop():
    """Emergency stop all trading activities"""
    try:
        if st.session_state.trading_engine:
            st.session_state.trading_engine.stop()
            st.session_state.trading_engine = None
        st.session_state.is_running = False
        st.warning("🚨 EMERGENCY STOP ACTIVATED - All trading stopped!")
    except Exception as e:
        st.error(f"❌ Emergency stop failed: {str(e)}")

def restart_bot_with_new_timeframe():
    """Restart the bot with the new timeframe configuration"""
    try:
        # Stop the current trading engine
        if st.session_state.trading_engine:
            st.session_state.trading_engine.stop()
            st.session_state.trading_engine = None
        
        # Wait a moment for cleanup
        time.sleep(1)
        
        # Start with new configuration
        if st.session_state.control_panel and st.session_state.control_panel.config:
            from trading_engine import TradingEngine
            st.session_state.trading_engine = TradingEngine(st.session_state.control_panel.config)
            
            # Start the engine
            if st.session_state.trading_engine.start():
                st.session_state.is_running = True
                st.success(f"✅ Bot restarted with {st.session_state.control_panel.config.timeframe} timeframe!")
            else:
                st.session_state.is_running = False
                st.error("❌ Failed to start trading engine after restart")
        else:
            st.error("❌ No configuration available for restart")
            st.session_state.is_running = False
            
    except Exception as e:
        st.error(f"❌ Failed to restart bot: {str(e)}")
        st.session_state.is_running = False

def check_connection_status():
    """Check IB Gateway connection status"""
    if st.session_state.trading_engine and st.session_state.trading_engine.api:
        try:
            # Mock connection check - replace with actual API call
            return "connected"
        except:
            return "disconnected"
    return "disconnected"

def render_about_page():
    """Render about page"""
    st.markdown('<h1 class="main-header">ℹ️ About MartinGales Trading Bot</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 🚀 Overview
        
        MartinGales is an advanced algorithmic trading bot designed for Interactive Brokers (IBKR) 
        that implements multiple Martingale-based trading strategies. The bot is built with Python 
        and features a modern Streamlit dashboard for monitoring and control.
        
        ## 📈 Supported Strategies
        
        - **CDM (Contrarian Dollar-cost averaging Martingale)**: Contrarian approach with dollar-cost averaging
        - **WDM (Weighted Dollar-cost averaging Martingale)**: Weighted position sizing with rebalancing
        - **ZRM (Zero-Risk Martingale)**: Risk-minimized Martingale approach
        - **IZRM (Inverse Zero-Risk Martingale)**: Inverse implementation of ZRM
        
        ## 🛠️ Features
        
        - **Real-time Trading**: Live market data and order execution
        - **Multi-Strategy Support**: Run multiple strategies simultaneously
        - **Risk Management**: Built-in position sizing and risk controls
        - **Performance Analytics**: Comprehensive performance tracking
        - **Configuration Management**: Easy strategy and parameter configuration
        - **Modern UI**: Intuitive Streamlit-based dashboard
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### 📊 System Requirements
        
        - Python 3.8+
        - Interactive Brokers Account
        - IB Gateway or TWS
        - Stable Internet Connection
        
        ### 📄 Version Info
        
        **Version:** 1.0.0  
        **Build:** 2024.12.01  
        **License:** MIT  
        """, unsafe_allow_html=True)

# Render sidebar navigation
render_sidebar_navigation()

# Main content area based on current page
if st.session_state.current_page == "Dashboard":
    # Initialize components for dashboard
    initialize_components()
    
    # Render dashboard content
    render_dashboard()

elif st.session_state.current_page == "Configuration":
    render_config_manager()

elif st.session_state.current_page == "Performance":
    render_performance_analytics()

elif st.session_state.current_page == "Backtesting":
    # Load config for backtesting
    try:
        from config import TradingConfig
        # Store config in session state to persist across reruns
        if 'backtest_config' not in st.session_state:
            st.session_state.backtest_config = TradingConfig()
        render_backtesting_interface(st.session_state.backtest_config)
    except Exception as e:
        st.error(f"Error loading backtesting interface: {str(e)}")

elif st.session_state.current_page == "CycleAnalysis":
    # Load cycle analysis data
    try:
        from cycle_analysis import CycleAnalysisReport
        from config import TradingConfig
        
        # Check if we have cycle data available
        if 'cycle_report' not in st.session_state:
            st.session_state.cycle_report = None
        
        # Try to load existing cycle data or create empty report
        if st.session_state.cycle_report is None:
            st.info("No cycle data available. Run backtesting or live trading to generate cycle analysis data.")
            st.session_state.cycle_report = CycleAnalysisReport()
        
        render_cycle_analysis_page(st.session_state.cycle_report, "Portfolio")
    except Exception as e:
        st.error(f"Error loading cycle analysis interface: {str(e)}")
        st.info("Please ensure you have run backtesting or live trading to generate cycle data.")

elif st.session_state.current_page == "MoneyManagement":
    # Load money management interface
    try:
        from config import TradingConfig
        
        # Initialize config if needed
        if 'money_management_config' not in st.session_state:
            st.session_state.money_management_config = TradingConfig()
        
        render_money_management_page(st.session_state.money_management_config)
    except Exception as e:
        st.error(f"Error loading money management interface: {str(e)}")
        st.info("Please check your configuration and try again.")

elif st.session_state.current_page == "RiskManagement":
    # Load risk management interface
    try:
        from config import TradingConfig
        
        # Initialize config if needed
        if 'risk_management_config' not in st.session_state:
            st.session_state.risk_management_config = TradingConfig()
        
        render_risk_management_page(st.session_state.risk_management_config)
    except Exception as e:
        st.error(f"Error loading risk management interface: {str(e)}")
        st.info("Please check your configuration and try again.")

elif st.session_state.current_page == "About":
    render_about_page()

# Footer
st.markdown("""
<div class="footer">
    <p>🤖 MartinGales Trading Bot v1.0 | 
    Last updated: {}</p>
    <p style="font-size: 0.8rem; color: #999;">
    ⚠️ Trading involves risk. Past performance does not guarantee future results.
    </p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)