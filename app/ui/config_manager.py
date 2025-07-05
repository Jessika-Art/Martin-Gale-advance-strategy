import streamlit as st
import json
import os
import sys
import streamlit as st
from typing import List, Dict, Any

# Add parent directory to path to import our modules
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import required modules
from config import TradingConfig, StrategyType, CDMSettings, WDMSettings, ZRMSettings, IZRMSettings
from control_panel import ControlPanel

# Verify StrategyType is properly imported
if 'StrategyType' not in globals():
    raise ImportError("StrategyType not properly imported")

def render_config_manager():
    """Render the configuration management interface"""
    st.title("⚙️ Configuration Manager")
    
    # Initialize control panel if not exists
    if 'control_panel' not in st.session_state:
        st.session_state.control_panel = ControlPanel()
    
    control_panel = st.session_state.control_panel
    
    # Configuration tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Symbols", "🎯 Strategies", "⚙️ Shared Settings", "💾 Save/Load"])
    
    with tab1:
        render_symbols_config(control_panel)
    
    with tab2:
        render_strategies_config(control_panel)
    
    with tab3:
        render_shared_settings_config(control_panel)
    
    with tab4:
        render_save_load_config(control_panel)

def render_symbols_config(control_panel: ControlPanel):
    """Render symbols configuration section"""
    st.subheader("📊 Trading Symbols Configuration")
    
    # Ensure config exists
    if control_panel.config is None:
        control_panel.config = TradingConfig()
    
    config = control_panel.config
    
    # Current symbols display
    st.write("**Current Symbols:**")
    if config.tickers:
        for i, ticker in enumerate(config.tickers):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {ticker}")
            with col2:
                if st.button("❌", key=f"remove_{ticker}_{i}", help=f"Remove {ticker}"):
                    config.tickers.remove(ticker)
                    st.rerun()
    else:
        st.info("No symbols configured")
    
    # Add new symbol
    st.write("**Add New Symbol:**")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("Symbol (e.g., AAPL, TSLA)", key="new_symbol")
    with col2:
        if st.button("➕ Add", key="add_symbol"):
            if new_symbol and new_symbol.upper() not in config.tickers:
                config.tickers.append(new_symbol.upper())
                st.success(f"Added {new_symbol.upper()}")
                st.rerun()
            elif new_symbol.upper() in config.tickers:
                st.warning(f"{new_symbol.upper()} already exists")
    
    # Bulk add symbols
    st.write("**Bulk Add Symbols:**")
    bulk_symbols = st.text_area(
        "Enter symbols separated by commas (e.g., AAPL, MSFT, GOOGL)",
        key="bulk_symbols"
    )
    if st.button("➕ Add All", key="add_bulk_symbols"):
        if bulk_symbols:
            symbols = [s.strip().upper() for s in bulk_symbols.split(',') if s.strip()]
            added = []
            for symbol in symbols:
                if symbol not in config.tickers:
                    config.tickers.append(symbol)
                    added.append(symbol)
            if added:
                st.success(f"Added: {', '.join(added)}")
                st.rerun()

def get_strategy_value(strategy):
    """Helper function to get strategy value whether it's an enum or string"""
    return strategy.value if hasattr(strategy, 'value') else strategy

def render_strategies_config(control_panel: ControlPanel):
    """Render strategies configuration section"""
    # Import StrategyType within function scope to avoid scoping issues
    from config import StrategyType
    
    st.subheader("🎯 Trading Strategies Configuration")
    
    config = control_panel.config
    if config is None:
        config = TradingConfig()
        control_panel.config = config
    
    # Available strategies
    available_strategies = [e.value for e in StrategyType]
    strategy_descriptions = {
        'cdm': 'Contrarian Dollar-cost averaging Martingale',
        'wdm': 'Weighted Dollar-cost averaging Martingale',
        'zrm': 'Zero-Risk Martingale',
        'izrm': 'Inverse Zero-Risk Martingale'
    }
    
    # Generate unique key suffix based on session state
    if 'strategy_config_counter' not in st.session_state:
        st.session_state.strategy_config_counter = 0
    
    key_suffix = st.session_state.strategy_config_counter
    
    st.write("**Available Strategies:**")
    
    for strategy in available_strategies:
        col1, col2, col3 = st.columns([1, 3, 1])
        strategy_val = get_strategy_value(strategy)
        
        with col1:
            # Show strategy status (read-only)
            # Convert string strategy to enum for comparison
            from config import StrategyType
            strategy_enum_map = {
                'cdm': StrategyType.CDM,
                'wdm': StrategyType.WDM,
                'zrm': StrategyType.ZRM,
                'izrm': StrategyType.IZRM
            }
            strategy_enum = strategy_enum_map.get(strategy)
            is_active = strategy_enum in config.active_strategies if strategy_enum else False
            status_text = "✅ Active" if is_active else "⭕ Inactive"
            st.write(f"**{strategy_val.upper()}**")
            st.write(status_text)
        
        with col2:
            st.write(strategy_descriptions.get(strategy, "Strategy description"))
            st.caption("💡 Use sidebar 'Strategy Selection' to activate/deactivate strategies")
        
        with col3:
            if st.button("⚙️", key=f"config_{strategy_val}_{key_suffix}", help=f"Configure {strategy_val.upper()}"):
                st.session_state[f'show_config_{strategy_val}_{key_suffix}'] = True
                st.rerun()
    
    # Strategy-specific settings
    if config.active_strategies:
        st.write("**Strategy Settings:**")
        
        for strategy in config.active_strategies:
            # Check if configuration should be shown
            strategy_val = get_strategy_value(strategy)
            show_config = st.session_state.get(f'show_config_{strategy_val}_{key_suffix}', False)
            
            if show_config:
                with st.expander(f"{strategy_val.upper()} Settings", expanded=True):
                    render_strategy_settings(config, strategy, key_suffix)
                    
                    # Close configuration button
                    if st.button("Close Configuration", key=f"close_{strategy_val}_{key_suffix}"):
                        st.session_state[f'show_config_{strategy_val}_{key_suffix}'] = False
                        st.rerun()

def render_strategy_settings(config: TradingConfig, strategy, key_suffix: int = 0):
    """Render settings for a specific strategy"""
    strategy_val = get_strategy_value(strategy)
    if strategy_val == 'cdm':
        render_cdm_settings(config, key_suffix)
    elif strategy_val == 'wdm':
        render_wdm_settings(config, key_suffix)
    elif strategy_val == 'zrm':
        render_zrm_settings(config, key_suffix)
    elif strategy_val == 'izrm':
        render_izrm_settings(config, key_suffix)

def render_cdm_settings(config: TradingConfig, key_suffix: int = 0):
    """Render CDM (Counter Direction Martingale) strategy settings"""
    st.write("**CDM Strategy Settings:")
    
    # Get current CDM settings
    cdm_settings = config.cdm_settings
    
    # Base Strategy Settings
    st.subheader("Base Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        # Strategy activation is controlled from sidebar
        st.info("💡 Strategy activation is controlled from the sidebar 'Strategy Selection'")
        
        cdm_settings.capital_allocation = st.number_input(
            "Capital Allocation (0.0-1.0)",
            min_value=0.01,
            max_value=1.0,
            value=cdm_settings.capital_allocation,
            step=0.01,
            key=f"cdm_capital_allocation_{key_suffix}",
            help="Percentage of total capital to allocate to this strategy"
        )
        
        cdm_settings.symbol = st.text_input(
            "Symbol",
            value=cdm_settings.symbol,
            key=f"cdm_symbol_{key_suffix}"
        )
        
        cdm_settings.max_orders = st.number_input(
            "Maximum Orders",
            min_value=1,
            max_value=50,
            value=cdm_settings.max_orders,
            step=1,
            key=f"cdm_max_orders_{key_suffix}"
        )
    
    with col2:
        cdm_settings.initial_trade_type = st.selectbox(
            "Initial Trade Type",
            ["BUY", "SELL"],
            index=0 if cdm_settings.initial_trade_type == "BUY" else 1,
            key=f"cdm_initial_trade_type_{key_suffix}"
        )
        
        cdm_settings.price_trigger = st.number_input(
            "Price Trigger (Optional)",
            min_value=0.0,
            value=cdm_settings.price_trigger if cdm_settings.price_trigger else 0.0,
            step=0.01,
            key=f"cdm_price_trigger_{key_suffix}",
            help="Leave 0 for immediate entry"
        )
        if cdm_settings.price_trigger == 0.0:
            cdm_settings.price_trigger = None
            
        cdm_settings.hold_previous = st.checkbox(
            "Hold Previous Positions",
            value=cdm_settings.hold_previous,
            key=f"cdm_hold_previous_{key_suffix}"
        )
    
    # CDM Specific Settings
    st.subheader("CDM Specific Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        cdm_settings.trailing_stops = st.checkbox(
            "Enable Trailing Stops",
            value=cdm_settings.trailing_stops,
            key=f"cdm_trailing_stops_{key_suffix}"
        )
    
    # Order Configuration
    st.subheader("Order Configuration")
    
    # Ensure lists have the right length
    max_orders = cdm_settings.max_orders
    while len(cdm_settings.order_distances) < max_orders:
        cdm_settings.order_distances.append(1.0)
    while len(cdm_settings.order_sizes) < max_orders:
        cdm_settings.order_sizes.append(1.0)
    while len(cdm_settings.order_tps) < max_orders:
        cdm_settings.order_tps.append(2.0)
    # Initialize new trailing parameters if they don't exist
    if not hasattr(cdm_settings, 'trailing_trigger_pct'):
        cdm_settings.trailing_trigger_pct = [5.0] * max_orders
    if not hasattr(cdm_settings, 'trailing_distance_pct'):
        cdm_settings.trailing_distance_pct = [1.0] * max_orders
    
    while len(cdm_settings.trailing_trigger_pct) < max_orders:
        cdm_settings.trailing_trigger_pct.append(5.0)
    while len(cdm_settings.trailing_distance_pct) < max_orders:
        cdm_settings.trailing_distance_pct.append(1.0)
    while len(cdm_settings.first_distance_trailing) < max_orders:
        cdm_settings.first_distance_trailing.append(1.0)
    while len(cdm_settings.trailing_progress) < max_orders:
        cdm_settings.trailing_progress.append(0.5)
    
    # Trim lists if too long
    cdm_settings.order_distances = cdm_settings.order_distances[:max_orders]
    cdm_settings.order_sizes = cdm_settings.order_sizes[:max_orders]
    cdm_settings.order_tps = cdm_settings.order_tps[:max_orders]
    cdm_settings.trailing_trigger_pct = cdm_settings.trailing_trigger_pct[:max_orders]
    cdm_settings.trailing_distance_pct = cdm_settings.trailing_distance_pct[:max_orders]
    cdm_settings.first_distance_trailing = cdm_settings.first_distance_trailing[:max_orders]
    cdm_settings.trailing_progress = cdm_settings.trailing_progress[:max_orders]
    
    for i in range(max_orders):
        st.write(f"**Order Level {i+1}:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cdm_settings.order_distances[i] = st.number_input(
                f"Distance %",
                min_value=0.01,
                max_value=100000.0,
                value=cdm_settings.order_distances[i],
                step=0.01,
                key=f"cdm_distance_{i}_{key_suffix}"
            )
            
        with col2:
            cdm_settings.order_sizes[i] = st.number_input(
                f"Size Multiplier",
                min_value=0.001,
                max_value=100000.0,
                value=cdm_settings.order_sizes[i],
                step=0.001,
                key=f"cdm_size_{i}_{key_suffix}",
                help="Multiplier for position size (supports fractional values like 0.01)"
            )
            
        with col3:
            cdm_settings.order_tps[i] = st.number_input(
                f"Take Profit %",
                min_value=0.01,
                max_value=100000.0,
                value=cdm_settings.order_tps[i],
                step=0.01,
                key=f"cdm_tp_{i}_{key_suffix}"
            )
        
        if cdm_settings.trailing_stops:
            col1, col2 = st.columns(2)
            with col1:
                cdm_settings.trailing_trigger_pct[i] = st.number_input(
                    f"Profit Trigger % (Leg {i+1})",
                    min_value=0.01,
                    max_value=100000.0,
                    value=cdm_settings.trailing_trigger_pct[i],
                    step=0.01,
                    key=f"cdm_trail_trigger_{i}_{key_suffix}",
                    help="Profit percentage required to activate trailing stop"
                )
            with col2:
                cdm_settings.trailing_distance_pct[i] = st.number_input(
                    f"Trailing Distance % (Leg {i+1})",
                    min_value=0.01,
                    max_value=100000.0,
                    value=cdm_settings.trailing_distance_pct[i],
                    step=0.01,
                    key=f"cdm_trail_distance_{i}_{key_suffix}",
                    help="Distance percentage for trailing stop from current price"
                )

def render_wdm_settings(config: TradingConfig, key_suffix: int = 0):
    """Render WDM (With Direction Martingale) strategy settings"""
    st.write("**WDM Strategy Settings:**")
    
    # Get current WDM settings
    wdm_settings = config.wdm_settings
    
    # Base Strategy Settings
    st.subheader("Base Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        # Strategy activation is controlled from sidebar
        st.info("💡 Strategy activation is controlled from the sidebar 'Strategy Selection'")
        
        wdm_settings.capital_allocation = st.number_input(
            "Capital Allocation (0.0-1.0)",
            min_value=0.01,
            max_value=1.0,
            value=wdm_settings.capital_allocation,
            step=0.01,
            key=f"wdm_capital_allocation_{key_suffix}"
        )
        
        wdm_settings.symbol = st.text_input(
            "Symbol",
            value=wdm_settings.symbol,
            key=f"wdm_symbol_{key_suffix}"
        )
        
        wdm_settings.max_orders = st.number_input(
            "Maximum Orders",
            min_value=1,
            max_value=50,
            value=wdm_settings.max_orders,
            step=1,
            key=f"wdm_max_orders_{key_suffix}"
        )
    
    with col2:
        wdm_settings.initial_trade_type = st.selectbox(
            "Initial Trade Type",
            ["BUY", "SELL"],
            index=0 if wdm_settings.initial_trade_type == "BUY" else 1,
            key=f"wdm_initial_trade_type_{key_suffix}"
        )
        
        wdm_settings.price_trigger = st.number_input(
            "Price Trigger (Optional)",
            min_value=0.0,
            value=wdm_settings.price_trigger if wdm_settings.price_trigger else 0.0,
            step=0.01,
            key=f"wdm_price_trigger_{key_suffix}"
        )
        if wdm_settings.price_trigger == 0.0:
            wdm_settings.price_trigger = None
            
        wdm_settings.hold_previous = st.checkbox(
            "Hold Previous Positions",
            value=wdm_settings.hold_previous,
            key=f"wdm_hold_previous_{key_suffix}"
        )
    
    # Order Configuration
    st.subheader("Order Configuration")
    
    # Ensure lists have the right length
    max_orders = wdm_settings.max_orders
    while len(wdm_settings.order_distances) < max_orders:
        wdm_settings.order_distances.append(1.0)
    while len(wdm_settings.order_sizes) < max_orders:
        wdm_settings.order_sizes.append(1.0)
    while len(wdm_settings.order_sls) < max_orders:
        wdm_settings.order_sls.append(2.0)
    
    # Trim lists if too long
    wdm_settings.order_distances = wdm_settings.order_distances[:max_orders]
    wdm_settings.order_sizes = wdm_settings.order_sizes[:max_orders]
    wdm_settings.order_sls = wdm_settings.order_sls[:max_orders]
    
    for i in range(max_orders):
        st.write(f"**Order Level {i+1}:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wdm_settings.order_distances[i] = st.number_input(
                f"Distance %",
                min_value=0.01,
                max_value=100000.0,
                value=wdm_settings.order_distances[i],
                step=0.01,
                key=f"wdm_distance_{i}_{key_suffix}"
            )
            
        with col2:
            wdm_settings.order_sizes[i] = st.number_input(
                f"Size Multiplier",
                min_value=0.001,
                max_value=100000.0,
                value=wdm_settings.order_sizes[i],
                step=0.001,
                key=f"wdm_size_{i}_{key_suffix}",
                help="Multiplier for position size (supports fractional values like 0.01)"
            )
            
        with col3:
            wdm_settings.order_sls[i] = st.number_input(
                f"Stop Loss %",
                min_value=0.01,
                max_value=100000.0,
                value=wdm_settings.order_sls[i],
                step=0.01,
                key=f"wdm_sl_{i}_{key_suffix}"
            )

def render_zrm_settings(config: TradingConfig, key_suffix: int = 0):
    """Render ZRM (Zone Recovery Martingale) strategy settings"""
    st.write("**ZRM Strategy Settings:**")
    
    # Get current ZRM settings
    zrm_settings = config.zrm_settings
    
    # Base Strategy Settings
    st.subheader("Base Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        # Strategy activation is controlled from sidebar
        st.info("💡 Strategy activation is controlled from the sidebar 'Strategy Selection'")
        
        zrm_settings.capital_allocation = st.number_input(
            "Capital Allocation (0.0-1.0)",
            min_value=0.01,
            max_value=1.0,
            value=zrm_settings.capital_allocation,
            step=0.01,
            key=f"zrm_capital_allocation_{key_suffix}"
        )
        
        zrm_settings.symbol = st.text_input(
            "Symbol",
            value=zrm_settings.symbol,
            key=f"zrm_symbol_{key_suffix}"
        )
        
        zrm_settings.max_orders = st.number_input(
            "Maximum Orders",
            min_value=1,
            max_value=50,
            value=zrm_settings.max_orders,
            step=1,
            key=f"zrm_max_orders_{key_suffix}"
        )
    
    with col2:
        zrm_settings.initial_trade_type = st.selectbox(
            "Initial Trade Type",
            ["BUY", "SELL"],
            index=0 if zrm_settings.initial_trade_type == "BUY" else 1,
            key=f"zrm_initial_trade_type_{key_suffix}"
        )
        
        zrm_settings.price_trigger = st.number_input(
            "Price Trigger (Optional)",
            min_value=0.0,
            value=zrm_settings.price_trigger if zrm_settings.price_trigger else 0.0,
            step=0.01,
            key=f"zrm_price_trigger_{key_suffix}"
        )
        if zrm_settings.price_trigger == 0.0:
            zrm_settings.price_trigger = None
            
        zrm_settings.hold_previous = st.checkbox(
            "Hold Previous Positions",
            value=zrm_settings.hold_previous,
            key=f"zrm_hold_previous_{key_suffix}"
        )
    
    # ZRM Specific Settings
    st.subheader("ZRM Specific Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        zrm_settings.zone_center_price = st.number_input(
            "Zone Center Price (Optional)",
            min_value=0.0,
            value=zrm_settings.zone_center_price if zrm_settings.zone_center_price else 0.0,
            step=0.01,
            key=f"zrm_zone_center_price_{key_suffix}"
        )
        if zrm_settings.zone_center_price == 0.0:
            zrm_settings.zone_center_price = None
    
    with col2:
        zrm_settings.zone_width_pct = st.number_input(
            "Zone Width %",
            min_value=0.1,
            max_value=50.0,
            value=zrm_settings.zone_width_pct,
            step=0.1,
            key=f"zrm_zone_width_pct_{key_suffix}"
        )
    
    with col3:
        zrm_settings.trailing_stops = st.checkbox(
            "Enable Trailing Stops",
            value=zrm_settings.trailing_stops,
            key=f"zrm_trailing_stops_{key_suffix}"
        )
    
    # Order Configuration
    st.subheader("Order Configuration")
    
    # Ensure lists have the right length
    max_orders = zrm_settings.max_orders
    while len(zrm_settings.order_distances) < max_orders:
        zrm_settings.order_distances.append(1.0)
    while len(zrm_settings.order_sizes) < max_orders:
        zrm_settings.order_sizes.append(1.0)
    while len(zrm_settings.order_tps) < max_orders:
        zrm_settings.order_tps.append(1.0)
    # Initialize new trailing parameters if they don't exist
    if not hasattr(zrm_settings, 'trailing_trigger_pct'):
        zrm_settings.trailing_trigger_pct = [3.0] * max_orders
    if not hasattr(zrm_settings, 'trailing_distance_pct'):
        zrm_settings.trailing_distance_pct = [0.5] * max_orders
    
    while len(zrm_settings.trailing_trigger_pct) < max_orders:
        zrm_settings.trailing_trigger_pct.append(3.0)
    while len(zrm_settings.trailing_distance_pct) < max_orders:
        zrm_settings.trailing_distance_pct.append(0.5)
    while len(zrm_settings.first_distance_trailing) < max_orders:
        zrm_settings.first_distance_trailing.append(0.5)
    while len(zrm_settings.trailing_progress) < max_orders:
        zrm_settings.trailing_progress.append(0.3)
    
    # Trim lists if too long
    zrm_settings.order_distances = zrm_settings.order_distances[:max_orders]
    zrm_settings.order_sizes = zrm_settings.order_sizes[:max_orders]
    zrm_settings.order_tps = zrm_settings.order_tps[:max_orders]
    zrm_settings.trailing_trigger_pct = zrm_settings.trailing_trigger_pct[:max_orders]
    zrm_settings.trailing_distance_pct = zrm_settings.trailing_distance_pct[:max_orders]
    zrm_settings.first_distance_trailing = zrm_settings.first_distance_trailing[:max_orders]
    zrm_settings.trailing_progress = zrm_settings.trailing_progress[:max_orders]
    
    for i in range(max_orders):
        st.write(f"**Order Level {i+1}:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            zrm_settings.order_distances[i] = st.number_input(
                f"Distance %",
                min_value=0.01,
                max_value=100000.0,
                value=zrm_settings.order_distances[i],
                step=0.01,
                key=f"zrm_distance_{i}_{key_suffix}"
            )
            
        with col2:
            zrm_settings.order_sizes[i] = st.number_input(
                f"Size Multiplier",
                min_value=0.001,
                max_value=100000.0,
                value=zrm_settings.order_sizes[i],
                step=0.001,
                key=f"zrm_size_{i}_{key_suffix}",
                help="Multiplier for position size (supports fractional values like 0.01)"
            )
            
        with col3:
            zrm_settings.order_tps[i] = st.number_input(
                f"Take Profit %",
                min_value=0.01,
                max_value=100000.0,
                value=zrm_settings.order_tps[i],
                step=0.01,
                key=f"zrm_tp_{i}_{key_suffix}"
            )
        
        if zrm_settings.trailing_stops:
            col1, col2 = st.columns(2)
            with col1:
                zrm_settings.trailing_trigger_pct[i] = st.number_input(
                    f"Profit Trigger % (Leg {i+1})",
                    min_value=0.01,
                    max_value=100000.0,
                    value=zrm_settings.trailing_trigger_pct[i],
                    step=0.01,
                    key=f"zrm_trail_trigger_{i}_{key_suffix}",
                    help="Profit percentage required to activate trailing stop"
                )
            with col2:
                zrm_settings.trailing_distance_pct[i] = st.number_input(
                    f"Trailing Distance % (Leg {i+1})",
                    min_value=0.01,
                    max_value=100000.0,
                    value=zrm_settings.trailing_distance_pct[i],
                    step=0.01,
                    key=f"zrm_trail_distance_{i}_{key_suffix}",
                    help="Distance percentage for trailing stop from current price"
                )

def render_izrm_settings(config: TradingConfig, key_suffix: int = 0):
    """Render IZRM (Inverse Zone Recovery Martingale) strategy settings"""
    st.write("**IZRM Strategy Settings:**")
    
    # Get current IZRM settings
    izrm_settings = config.izrm_settings
    
    # Base Strategy Settings
    st.subheader("Base Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        # Strategy activation is controlled from sidebar
        st.info("💡 Strategy activation is controlled from the sidebar 'Strategy Selection'")
        
        izrm_settings.capital_allocation = st.number_input(
            "Capital Allocation (0.0-1.0)",
            min_value=0.01,
            max_value=1.0,
            value=izrm_settings.capital_allocation,
            step=0.01,
            key=f"izrm_capital_allocation_{key_suffix}"
        )
        
        izrm_settings.symbol = st.text_input(
            "Symbol",
            value=izrm_settings.symbol,
            key=f"izrm_symbol_{key_suffix}"
        )
        
        izrm_settings.max_orders = st.number_input(
            "Maximum Orders",
            min_value=1,
            max_value=50,
            value=izrm_settings.max_orders,
            step=1,
            key=f"izrm_max_orders_{key_suffix}"
        )
    
    with col2:
        izrm_settings.initial_trade_type = st.selectbox(
            "Initial Trade Type",
            ["BUY", "SELL"],
            index=0 if izrm_settings.initial_trade_type == "BUY" else 1,
            key=f"izrm_initial_trade_type_{key_suffix}"
        )
        
        izrm_settings.price_trigger = st.number_input(
            "Price Trigger (Optional)",
            min_value=0.0,
            value=izrm_settings.price_trigger if izrm_settings.price_trigger else 0.0,
            step=0.01,
            key=f"izrm_price_trigger_{key_suffix}"
        )
        if izrm_settings.price_trigger == 0.0:
            izrm_settings.price_trigger = None
            
        izrm_settings.hold_previous = st.checkbox(
            "Hold Previous Positions",
            value=izrm_settings.hold_previous,
            key=f"izrm_hold_previous_{key_suffix}"
        )
    
    # IZRM Specific Settings
    st.subheader("IZRM Specific Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        izrm_settings.zone_center_price = st.number_input(
            "Zone Center Price (Optional)",
            min_value=0.0,
            value=izrm_settings.zone_center_price if izrm_settings.zone_center_price else 0.0,
            step=0.01,
            key=f"izrm_zone_center_price_{key_suffix}"
        )
        if izrm_settings.zone_center_price == 0.0:
            izrm_settings.zone_center_price = None
    
    with col2:
        izrm_settings.zone_width_pct = st.number_input(
            "Zone Width %",
            min_value=0.1,
            max_value=50.0,
            value=izrm_settings.zone_width_pct,
            step=0.1,
            key=f"izrm_zone_width_pct_{key_suffix}"
        )
    
    # Order Configuration
    st.subheader("Order Configuration")
    
    # Ensure lists have the right length
    max_orders = izrm_settings.max_orders
    while len(izrm_settings.order_distances) < max_orders:
        izrm_settings.order_distances.append(1.0)
    while len(izrm_settings.order_sizes) < max_orders:
        izrm_settings.order_sizes.append(1.0)
    while len(izrm_settings.order_sls) < max_orders:
        izrm_settings.order_sls.append(2.0)
    
    # Trim lists if too long
    izrm_settings.order_distances = izrm_settings.order_distances[:max_orders]
    izrm_settings.order_sizes = izrm_settings.order_sizes[:max_orders]
    izrm_settings.order_sls = izrm_settings.order_sls[:max_orders]
    
    for i in range(max_orders):
        st.write(f"**Order Level {i+1}:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            izrm_settings.order_distances[i] = st.number_input(
                f"Distance %",
                min_value=0.01,
                max_value=100000.0,
                value=izrm_settings.order_distances[i],
                step=0.01,
                key=f"izrm_distance_{i}_{key_suffix}"
            )
            
        with col2:
            izrm_settings.order_sizes[i] = st.number_input(
                f"Size Multiplier",
                min_value=0.001,
                max_value=100000.0,
                value=izrm_settings.order_sizes[i],
                step=0.001,
                key=f"izrm_size_{i}_{key_suffix}",
                help="Multiplier for position size (supports fractional values like 0.01)"
            )
            
        with col3:
            izrm_settings.order_sls[i] = st.number_input(
                f"Stop Loss %",
                min_value=0.01,
                max_value=100000.0,
                value=izrm_settings.order_sls[i],
                step=0.01,
                key=f"izrm_sl_{i}_{key_suffix}"
            )
        

def render_shared_settings_config(control_panel: ControlPanel):
    """Render shared settings configuration section"""
    st.subheader("⚙️ Shared Settings Configuration")
    
    # Ensure config exists
    if control_panel.config is None:
        control_panel.config = TradingConfig()
    
    config = control_panel.config
    shared = config.shared_settings
    
    # Trading Control Settings
    st.write("**Trading Control:**")
    col1, col2 = st.columns(2)
    
    with col1:
        shared.continue_trading = st.checkbox(
            "Continue Trading",
            value=shared.continue_trading,
            key="continue_trading",
            help="Enable continuous trading operations"
        )
        
        shared.pre_after_hours = st.checkbox(
            "Pre/After Hours Trading",
            value=shared.pre_after_hours,
            key="pre_after_hours",
            help="Allow trading during pre-market and after-hours sessions"
        )
        
        shared.repeat_on_close = st.checkbox(
            "Repeat on Close",
            value=shared.repeat_on_close,
            key="repeat_on_close",
            help="Automatically repeat strategy when positions close"
        )
    
    with col2:
        shared.order_type = st.selectbox(
             "Order Filing Type",
             options=["MARKET", "LIMIT"],
             index=0 if shared.order_type == "MARKET" else 1,
             key="order_type",
             help="Default order type for all strategies"
         )
    
    st.divider()
    
    # Money Management (MM) Settings
    st.write("**Money Management (MM) Plan:**")
    col1, col2 = st.columns(2)
    
    with col1:
        shared.money_management = st.checkbox(
             "Enable MM (Profit Reinvestment) Plan",
             value=shared.money_management,
             key="money_management",
             help="Enable automatic profit reinvestment strategy"
         )
        
        if shared.money_management:
            shared.growth_threshold = st.number_input(
                "Growth Threshold ($)",
                min_value=0.0,
                value=shared.growth_threshold,
                step=100.0,
                key="growth_threshold",
                help="Minimum profit threshold to trigger reinvestment"
            )
            
            shared.increase_value = st.number_input(
                "Increase Value",
                min_value=0.0,
                value=shared.increase_value,
                step=10.0,
                key="increase_value",
                help="Amount to increase position size (Dollar, shares, or %)"
            )
    
    with col2:
        if shared.money_management:
            # Note: increase_value_type is not in SharedSettings, using increase_value as percentage
            st.info("💡 Increase value is treated as percentage in the current implementation")
            
            shared.progressive_reinvestment_step = st.number_input(
                "Progressive Reinvestment Step (%)",
                min_value=0.0,
                max_value=1.0,
                value=shared.progressive_reinvestment_step,
                step=0.01,
                key="progressive_reinvestment_step",
                help="Percentage step for progressive reinvestment increases (as decimal)"
            )
    
    st.divider()
    
    # Global Position Sizing
    st.write("**Global Position Sizing:**")
    col1, col2 = st.columns(2)
    
    with col1:
        shared.global_position_size_unit = st.selectbox(
            "Position Size Unit",
            options=["SHARES", "USD", "PERCENTAGE"],
            index=["SHARES", "USD", "PERCENTAGE"].index(shared.global_position_size_unit),
            key="global_position_size_unit",
            help="Unit for position sizing across all strategies"
        )
        
        shared.global_fixed_position_size = st.number_input(
            "Fixed Position Size",
            min_value=0.0,
            value=shared.global_fixed_position_size,
            step=0.01,
            key="global_fixed_position_size",
            help="Fixed position size value (supports fractional values)"
        )
    
    with col2:
        shared.global_percentage_of_portfolio = st.number_input(
            "Portfolio Percentage (%)",
            min_value=0.0,
            max_value=100.0,
            value=shared.global_percentage_of_portfolio,
            step=1.0,
            key="global_percentage_of_portfolio",
            help="Percentage of portfolio to use for position sizing"
        )
        
        # Dynamic sizing is now handled by individual strategy multipliers
        # shared.enable_dynamic_sizing = st.checkbox(
        #     "Enable Dynamic Sizing",
        #     value=shared.enable_dynamic_sizing,
        #     key="enable_dynamic_sizing",
        #     help="Enable dynamic position sizing based on market conditions"
        # )
    
    st.divider()
    
    # Strategy Coordination
    st.write("**Strategy Coordination:**")
    col1, col2 = st.columns(2)
    
    with col1:
        shared.enable_strategy_coordination = st.checkbox(
            "Enable Strategy Coordination",
            value=shared.enable_strategy_coordination,
            key="enable_strategy_coordination",
            help="Enable coordination between multiple strategies"
        )
        
        if shared.enable_strategy_coordination:
            shared.global_strategy_alignment = st.selectbox(
                "Strategy Alignment",
                options=["PARALLEL", "SEQUENTIAL"],
                index=0 if shared.global_strategy_alignment == "PARALLEL" else 1,
                key="global_strategy_alignment",
                help="How strategies should be executed"
            )
    
    with col2:
        if shared.enable_strategy_coordination:
            shared.global_strategy_to_start_with = st.selectbox(
                "Starting Strategy",
                options=["CDM", "WDM", "ZRM", "IZRM"],
                index=["CDM", "WDM", "ZRM", "IZRM"].index(shared.global_strategy_to_start_with),
                key="global_strategy_to_start_with",
                help="Which strategy to start with"
            )
            
            shared.max_concurrent_strategies = st.number_input(
                "Max Concurrent Strategies",
                min_value=1,
                max_value=10,
                value=shared.max_concurrent_strategies,
                step=1,
                key="max_concurrent_strategies",
                help="Maximum number of strategies running simultaneously"
            )
    
    # Sequential Strategy Execution Order
    if shared.enable_strategy_coordination and shared.global_strategy_alignment == "SEQUENTIAL":
        st.write("**Sequential Strategy Execution Order:**")
        st.write("Configure the order in which strategies will be executed sequentially:")
        
        # Get current strategy priority order
        current_order = getattr(shared, 'strategy_priority_order', ["CDM", "WDM", "ZRM", "IZRM"])
        
        # Create columns for reordering
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.write("**Current Order:**")
            for i, strategy in enumerate(current_order, 1):
                st.write(f"{i}. {strategy}")
        
        with col2:
            st.write("**Actions:**")
            if st.button("⬆️ Move Up", key="move_up_strategy", help="Move selected strategy up"):
                if 'selected_strategy_index' in st.session_state and st.session_state.selected_strategy_index > 0:
                    idx = st.session_state.selected_strategy_index
                    current_order[idx], current_order[idx-1] = current_order[idx-1], current_order[idx]
                    shared.strategy_priority_order = current_order
                    st.session_state.selected_strategy_index -= 1
                    st.rerun()
            
            if st.button("⬇️ Move Down", key="move_down_strategy", help="Move selected strategy down"):
                if 'selected_strategy_index' in st.session_state and st.session_state.selected_strategy_index < len(current_order) - 1:
                    idx = st.session_state.selected_strategy_index
                    current_order[idx], current_order[idx+1] = current_order[idx+1], current_order[idx]
                    shared.strategy_priority_order = current_order
                    st.session_state.selected_strategy_index += 1
                    st.rerun()
        
        with col3:
            st.write("**Select Strategy to Reorder:**")
            selected_strategy = st.selectbox(
                "Strategy",
                options=current_order,
                key="strategy_to_reorder",
                help="Select a strategy to move up or down in the execution order"
            )
            
            if selected_strategy:
                st.session_state.selected_strategy_index = current_order.index(selected_strategy)
        
        # Quick preset orders
        st.write("**Quick Preset Orders:**")
        preset_col1, preset_col2, preset_col3 = st.columns(3)
        
        with preset_col1:
            if st.button("📈 Trend First", key="trend_first_order", help="WDM → CDM → ZRM → IZRM"):
                shared.strategy_priority_order = ["WDM", "CDM", "ZRM", "IZRM"]
                st.success("Order set to: Trend First")
                st.rerun()
        
        with preset_col2:
            if st.button("📉 Mean Reversion First", key="mean_reversion_first", help="CDM → WDM → ZRM → IZRM"):
                shared.strategy_priority_order = ["CDM", "WDM", "ZRM", "IZRM"]
                st.success("Order set to: Mean Reversion First")
                st.rerun()
        
        with preset_col3:
            if st.button("🎯 Zone First", key="zone_first_order", help="ZRM → IZRM → CDM → WDM"):
                shared.strategy_priority_order = ["ZRM", "IZRM", "CDM", "WDM"]
                st.success("Order set to: Zone First")
                st.rerun()
        
        # Apply order button
        if st.button("✅ Apply Sequential Order", key="apply_sequential_order"):
            try:
                # Update the shared settings with the new order
                shared.strategy_priority_order = current_order
                st.success(f"Sequential execution order applied: {' → '.join(current_order)}")
            except Exception as e:
                st.error(f"Failed to apply sequential order: {str(e)}")
    
    st.divider()
    
    # Risk Management
    st.write("**Risk Management:**")
    col1, col2 = st.columns(2)
    
    with col1:
        shared.enable_daily_limits = st.checkbox(
             "Enable Global Risk Management",
             value=shared.enable_daily_limits,
             key="enable_daily_limits",
             help="Enable global risk management controls"
         )
        
        if shared.enable_daily_limits:
             shared.global_daily_loss_limit = st.number_input(
                 "Daily Loss Limit ($)",
                 min_value=0.0,
                 value=shared.global_daily_loss_limit,
                 step=100.0,
                 key="global_daily_loss_limit",
                 help="Maximum daily loss before stopping all strategies"
             )
             
             shared.max_portfolio_drawdown_pct = st.number_input(
                 "Max Drawdown (%)",
                 min_value=0.0,
                 max_value=100.0,
                 value=shared.max_portfolio_drawdown_pct,
                 step=0.01,
                 key="max_portfolio_drawdown_pct",
                 help="Maximum drawdown percentage before emergency stop"
             )
    
    with col2:
        if shared.enable_daily_limits:
            shared.enable_global_trailing_stops = st.checkbox(
                "Enable Global Trailing Stops",
                value=shared.enable_global_trailing_stops,
                key="enable_global_trailing_stops",
                help="Enable trailing stops across all strategies")
            
            if shared.enable_global_trailing_stops:
                shared.global_trailing_distance_pct = st.number_input(
                     "Trailing Stop (%)",
                     min_value=0.0,
                     max_value=100.0,
                     value=shared.global_trailing_distance_pct,
                     step=0.01,
                     key="global_trailing_distance_pct",
                     help="Trailing stop percentage")
                 
                shared.global_trailing_trigger_pct = st.number_input(
                     "Trailing Activation (%)",
                     min_value=0.0,
                     max_value=100.0,
                     value=shared.global_trailing_trigger_pct,
                     step=0.01,
                     key="global_trailing_trigger_pct",
                     help="Profit percentage to activate trailing stops"
                 )
    
    # Apply Settings Button
    st.divider()
    if st.button("✅ Apply Shared Settings", key="apply_shared_settings"):
        try:
            # Apply shared settings to all strategies
            config.apply_shared_settings_to_strategies()
            st.success("Shared settings applied successfully!")
        except Exception as e:
            st.error(f"Failed to apply shared settings: {str(e)}")

def render_save_load_config(control_panel: ControlPanel):
    """Render save/load configuration section"""
    st.subheader("💾 Save & Load Configuration")
    
    # Preset configurations
    st.write("**Preset Configurations:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 CDM Default", key="preset_cdm"):
            load_preset_config(control_panel, "cdm")
            st.success("CDM preset loaded!")
            st.rerun()
    
    with col2:
        if st.button("📈 WDM Default", key="preset_wdm"):
            load_preset_config(control_panel, "wdm")
            st.success("WDM preset loaded!")
            st.rerun()
    
    with col3:
        if st.button("🎯 ZRM Default", key="preset_zrm"):
            load_preset_config(control_panel, "zrm")
            st.success("ZRM preset loaded!")
            st.rerun()
    
    with col4:
        if st.button("🔄 IZRM Default", key="preset_izrm"):
            load_preset_config(control_panel, "izrm")
            st.success("IZRM preset loaded!")
            st.rerun()
    
    st.divider()
    
    # Save configuration
    st.write("**Save Configuration:**")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        config_name = st.text_input(
            "Configuration Name",
            value="my_config",
            key="config_name"
        )
    
    with col2:
        if st.button("💾 Save", key="save_config"):
            if config_name and control_panel.config:
                try:
                    filename = f"{config_name}.json"
                    save_detailed_config(control_panel.config, filename)
                    st.success(f"Configuration saved as {filename}")
                except Exception as e:
                    st.error(f"Failed to save configuration: {str(e)}")
    
    # Load configuration
    st.write("**Load Configuration:**")
    config_files = [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('config_')]
    
    if config_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_config = st.selectbox(
                "Select Configuration File",
                config_files,
                key="selected_config"
            )
        
        with col2:
            if st.button("📂 Load", key="load_config"):
                try:
                    load_detailed_config(control_panel, selected_config)
                    st.success(f"Configuration loaded from {selected_config}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load configuration: {str(e)}")
        
        # Preview configuration
        if selected_config:
            with st.expander("Preview Configuration"):
                try:
                    with open(selected_config, 'r') as f:
                        config_data = json.load(f)
                    st.json(config_data)
                except Exception as e:
                    st.error(f"Failed to preview configuration: {str(e)}")
    else:
        st.info("No configuration files found")
    
    # Export/Import
    st.write("**Export/Import:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Current Config", key="export_config"):
            if control_panel.config:
                config_dict = config_to_dict(control_panel.config)
                st.download_button(
                    label="Download Config JSON",
                    data=json.dumps(config_dict, indent=2),
                    file_name="trading_config_export.json",
                    mime="application/json"
                )
    
    with col2:
        # Check if we just imported a config to show success message
        if st.session_state.get('config_imported', False):
            st.success("Configuration imported successfully!")
            st.session_state.config_imported = False
        
        uploaded_file = st.file_uploader(
            "Import Configuration",
            type="json",
            key="import_config"
        )
        if uploaded_file is not None:
            try:
                config_data = json.load(uploaded_file)
                control_panel.config = dict_to_config(config_data)
                st.session_state.config_imported = True
                # Force a refresh by clearing the file uploader state
                if 'import_config' in st.session_state:
                    del st.session_state['import_config']
            except Exception as e:
                st.error(f"Failed to import configuration: {str(e)}")

def load_preset_config(control_panel: ControlPanel, strategy_type: str):
    """Load preset configuration for a specific strategy"""
    from config import get_demo_single_cdm_config, TradingConfig, StrategyType
    
    # Create base config
    config = TradingConfig()
    
    if strategy_type == "cdm":
        config.active_strategies = [StrategyType.CDM]
        config.cdm_settings.enabled = True
        config.cdm_settings.capital_allocation = 1.0
        config.cdm_settings.max_orders = 5
        config.cdm_settings.order_distances = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.cdm_settings.order_sizes = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.cdm_settings.order_tps = [2.0, 2.0, 2.0, 2.0, 2.0]
        config.cdm_settings.trailing_stops = False
        
    elif strategy_type == "wdm":
        config.active_strategies = [StrategyType.WDM]
        config.wdm_settings.enabled = True
        config.wdm_settings.capital_allocation = 1.0
        config.wdm_settings.max_orders = 5
        config.wdm_settings.order_distances = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.wdm_settings.order_sizes = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.wdm_settings.order_sls = [2.0, 2.0, 2.0, 2.0, 2.0]
        
    elif strategy_type == "zrm":
        config.active_strategies = [StrategyType.ZRM]
        config.zrm_settings.enabled = True
        config.zrm_settings.capital_allocation = 1.0
        config.zrm_settings.max_orders = 5
        config.zrm_settings.zone_width_pct = 5.0
        config.zrm_settings.order_distances = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.zrm_settings.order_sizes = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.zrm_settings.order_tps = [1.0, 1.0, 1.0, 1.0, 1.0]
        config.zrm_settings.trailing_stops = False
        
    elif strategy_type == "izrm":
        config.active_strategies = [StrategyType.IZRM]
        config.izrm_settings.enabled = True
        config.izrm_settings.capital_allocation = 1.0
        config.izrm_settings.max_orders = 5
        config.izrm_settings.zone_width_pct = 5.0
        config.izrm_settings.order_distances = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.izrm_settings.order_sizes = [1.0, 1.5, 2.0, 2.5, 3.0]
        config.izrm_settings.order_sls = [2.0, 2.0, 2.0, 2.0, 2.0]
    
    control_panel.config = config

def config_to_dict(config: TradingConfig) -> Dict[str, Any]:
    """Convert TradingConfig to dictionary for serialization"""
    def settings_to_dict(settings):
        return {
            'enabled': settings.enabled,
            'capital_allocation': settings.capital_allocation,
            'initial_trade_type': settings.initial_trade_type,
            'symbol': settings.symbol,
            'price_trigger': settings.price_trigger,
            'max_orders': settings.max_orders,
            'hold_previous': settings.hold_previous,
            'order_distances': settings.order_distances,
            'order_sizes': settings.order_sizes
        }
    
    config_dict = {
        'account_type': config.account_type.value,
        'execution_mode': config.execution_mode.value,
        'active_strategies': [s.value for s in config.active_strategies],
        'tickers': config.tickers,
        'timeframe': config.timeframe,
        'duration': config.duration,
        'data_type': config.data_type,
        'position_size_type': config.position_size_type,
        'position_size_value': config.position_size_value,
        'cdm_settings': {
            **settings_to_dict(config.cdm_settings),
            'order_tps': config.cdm_settings.order_tps,
            'trailing_stops': config.cdm_settings.trailing_stops,
            'trailing_trigger_pct': getattr(config.cdm_settings, 'trailing_trigger_pct', [5.0] * 5),
            'trailing_distance_pct': getattr(config.cdm_settings, 'trailing_distance_pct', [1.0] * 5),
            'first_distance_trailing': config.cdm_settings.first_distance_trailing,
            'trailing_progress': config.cdm_settings.trailing_progress
        },
        'wdm_settings': {
            **settings_to_dict(config.wdm_settings),
            'order_sls': config.wdm_settings.order_sls
        },
        'zrm_settings': {
            **settings_to_dict(config.zrm_settings),
            'zone_center_price': config.zrm_settings.zone_center_price,
            'zone_width_pct': config.zrm_settings.zone_width_pct,
            'order_tps': config.zrm_settings.order_tps,
            'trailing_stops': config.zrm_settings.trailing_stops,
            'trailing_trigger_pct': getattr(config.zrm_settings, 'trailing_trigger_pct', [3.0] * 5),
            'trailing_distance_pct': getattr(config.zrm_settings, 'trailing_distance_pct', [0.5] * 5),
            'first_distance_trailing': config.zrm_settings.first_distance_trailing,
            'trailing_progress': config.zrm_settings.trailing_progress
        },
        'izrm_settings': {
            **settings_to_dict(config.izrm_settings),
            'zone_center_price': config.izrm_settings.zone_center_price,
            'zone_width_pct': config.izrm_settings.zone_width_pct,
            'order_sls': config.izrm_settings.order_sls
        },
        'shared_settings': {
            # Trading Control
            'continue_trading': config.shared_settings.continue_trading,
            'pre_after_hours': config.shared_settings.pre_after_hours,
            'repeat_on_close': config.shared_settings.repeat_on_close,
            'order_type': config.shared_settings.order_type,
            
            # Money Management
            'money_management': config.shared_settings.money_management,
            'growth_threshold': config.shared_settings.growth_threshold,
            'increase_value': config.shared_settings.increase_value,
            'progressive_reinvestment_step': config.shared_settings.progressive_reinvestment_step,
            
            # Position Sizing
            'global_position_size_unit': config.shared_settings.global_position_size_unit,
            'global_fixed_position_size': config.shared_settings.global_fixed_position_size,
            'global_percentage_of_portfolio': config.shared_settings.global_percentage_of_portfolio,
            # 'enable_dynamic_sizing': config.shared_settings.enable_dynamic_sizing,  # Removed - handled by strategy multipliers
            
            # Strategy Coordination
            'enable_strategy_coordination': config.shared_settings.enable_strategy_coordination,
            'global_strategy_alignment': config.shared_settings.global_strategy_alignment,
            'global_strategy_to_start_with': config.shared_settings.global_strategy_to_start_with,
            'max_concurrent_strategies': config.shared_settings.max_concurrent_strategies,
            
            # Risk Management
            'enable_daily_limits': config.shared_settings.enable_daily_limits,
            'global_daily_loss_limit': config.shared_settings.global_daily_loss_limit,
            'max_portfolio_drawdown_pct': config.shared_settings.max_portfolio_drawdown_pct,
            'enable_global_trailing_stops': config.shared_settings.enable_global_trailing_stops,
            'global_trailing_distance_pct': config.shared_settings.global_trailing_distance_pct,
            'global_trailing_trigger_pct': config.shared_settings.global_trailing_trigger_pct
        }
    }
    
    return config_dict

def dict_to_config(config_dict: Dict[str, Any]) -> TradingConfig:
    """Convert dictionary to TradingConfig object"""
    from config import TradingConfig, AccountType, ExecutionMode, StrategyType
    
    config = TradingConfig()
    
    # Basic settings
    config.account_type = AccountType(config_dict.get('account_type', 'demo'))
    config.execution_mode = ExecutionMode(config_dict.get('execution_mode', 'single'))
    config.active_strategies = [StrategyType(s) for s in config_dict.get('active_strategies', ['cdm'])]
    config.tickers = config_dict.get('tickers', ['AAPL'])
    config.timeframe = config_dict.get('timeframe', '1 min')
    config.duration = config_dict.get('duration', '30 D')
    config.data_type = config_dict.get('data_type', 'TRADES')
    config.position_size_type = config_dict.get('position_size_type', 'PERCENTAGE')
    config.position_size_value = config_dict.get('position_size_value', 5.0)
    
    # Strategy settings
    def update_settings(settings, settings_dict):
        if settings_dict:
            if 'enabled' in settings_dict:
                settings.enabled = settings_dict['enabled']
            if 'capital_allocation' in settings_dict:
                settings.capital_allocation = settings_dict['capital_allocation']
            if 'initial_trade_type' in settings_dict:
                settings.initial_trade_type = settings_dict['initial_trade_type']
            if 'symbol' in settings_dict:
                settings.symbol = settings_dict['symbol']
            if 'price_trigger' in settings_dict:
                settings.price_trigger = settings_dict['price_trigger']
            if 'max_orders' in settings_dict:
                settings.max_orders = settings_dict['max_orders']
            if 'hold_previous' in settings_dict:
                settings.hold_previous = settings_dict['hold_previous']
            if 'order_distances' in settings_dict:
                settings.order_distances = settings_dict['order_distances']
            if 'order_sizes' in settings_dict:
                settings.order_sizes = settings_dict['order_sizes']
    
    # CDM settings
    cdm_dict = config_dict.get('cdm_settings', {})
    update_settings(config.cdm_settings, cdm_dict)
    if cdm_dict:
        if 'order_tps' in cdm_dict:
            config.cdm_settings.order_tps = cdm_dict['order_tps']
        if 'trailing_stops' in cdm_dict:
            config.cdm_settings.trailing_stops = cdm_dict['trailing_stops']
        if 'trailing_trigger_pct' in cdm_dict:
            config.cdm_settings.trailing_trigger_pct = cdm_dict['trailing_trigger_pct']
        if 'trailing_distance_pct' in cdm_dict:
            config.cdm_settings.trailing_distance_pct = cdm_dict['trailing_distance_pct']
        if 'first_distance_trailing' in cdm_dict:
            config.cdm_settings.first_distance_trailing = cdm_dict['first_distance_trailing']
        if 'trailing_progress' in cdm_dict:
            config.cdm_settings.trailing_progress = cdm_dict['trailing_progress']
    
    # WDM settings
    wdm_dict = config_dict.get('wdm_settings', {})
    update_settings(config.wdm_settings, wdm_dict)
    if wdm_dict:
        if 'order_sls' in wdm_dict:
            config.wdm_settings.order_sls = wdm_dict['order_sls']
    
    # ZRM settings
    zrm_dict = config_dict.get('zrm_settings', {})
    update_settings(config.zrm_settings, zrm_dict)
    if zrm_dict:
        if 'zone_center_price' in zrm_dict:
            config.zrm_settings.zone_center_price = zrm_dict['zone_center_price']
        if 'zone_width_pct' in zrm_dict:
            config.zrm_settings.zone_width_pct = zrm_dict['zone_width_pct']
        if 'order_tps' in zrm_dict:
            config.zrm_settings.order_tps = zrm_dict['order_tps']
        if 'trailing_stops' in zrm_dict:
            config.zrm_settings.trailing_stops = zrm_dict['trailing_stops']
        if 'trailing_trigger_pct' in zrm_dict:
            config.zrm_settings.trailing_trigger_pct = zrm_dict['trailing_trigger_pct']
        if 'trailing_distance_pct' in zrm_dict:
            config.zrm_settings.trailing_distance_pct = zrm_dict['trailing_distance_pct']
        if 'first_distance_trailing' in zrm_dict:
            config.zrm_settings.first_distance_trailing = zrm_dict['first_distance_trailing']
        if 'trailing_progress' in zrm_dict:
            config.zrm_settings.trailing_progress = zrm_dict['trailing_progress']
    
    # IZRM settings
    izrm_dict = config_dict.get('izrm_settings', {})
    update_settings(config.izrm_settings, izrm_dict)
    if izrm_dict:
        if 'zone_center_price' in izrm_dict:
            config.izrm_settings.zone_center_price = izrm_dict['zone_center_price']
        if 'zone_width_pct' in izrm_dict:
            config.izrm_settings.zone_width_pct = izrm_dict['zone_width_pct']
        if 'order_sls' in izrm_dict:
            config.izrm_settings.order_sls = izrm_dict['order_sls']
    
    # Shared settings
    shared_dict = config_dict.get('shared_settings', {})
    if shared_dict:
        # Trading Control
        if 'continue_trading' in shared_dict:
            config.shared_settings.continue_trading = shared_dict['continue_trading']
        if 'pre_after_hours' in shared_dict:
            config.shared_settings.pre_after_hours = shared_dict['pre_after_hours']
        if 'repeat_on_close' in shared_dict:
            config.shared_settings.repeat_on_close = shared_dict['repeat_on_close']
        if 'order_type' in shared_dict:
            config.shared_settings.order_type = shared_dict['order_type']
        
        # Money Management
        if 'money_management' in shared_dict:
            config.shared_settings.money_management = shared_dict['money_management']
        if 'growth_threshold' in shared_dict:
            config.shared_settings.growth_threshold = shared_dict['growth_threshold']
        if 'increase_value' in shared_dict:
            config.shared_settings.increase_value = shared_dict['increase_value']
        if 'progressive_reinvestment_step' in shared_dict:
            config.shared_settings.progressive_reinvestment_step = shared_dict['progressive_reinvestment_step']
        
        # Position Sizing
        if 'global_position_size_unit' in shared_dict:
            config.shared_settings.global_position_size_unit = shared_dict['global_position_size_unit']
        if 'global_fixed_position_size' in shared_dict:
            config.shared_settings.global_fixed_position_size = shared_dict['global_fixed_position_size']
        if 'global_percentage_of_portfolio' in shared_dict:
            config.shared_settings.global_percentage_of_portfolio = shared_dict['global_percentage_of_portfolio']
        # if 'enable_dynamic_sizing' in shared_dict:
         #     config.shared_settings.enable_dynamic_sizing = shared_dict['enable_dynamic_sizing']  # Removed - handled by strategy multipliers
        
        # Strategy Coordination
        if 'enable_strategy_coordination' in shared_dict:
            config.shared_settings.enable_strategy_coordination = shared_dict['enable_strategy_coordination']
        if 'global_strategy_alignment' in shared_dict:
            config.shared_settings.global_strategy_alignment = shared_dict['global_strategy_alignment']
        if 'global_strategy_to_start_with' in shared_dict:
            config.shared_settings.global_strategy_to_start_with = shared_dict['global_strategy_to_start_with']
        if 'max_concurrent_strategies' in shared_dict:
            config.shared_settings.max_concurrent_strategies = shared_dict['max_concurrent_strategies']
        if 'global_max_concurrent_cycles' in shared_dict:
            config.shared_settings.global_max_concurrent_cycles = shared_dict['global_max_concurrent_cycles']
        
        # Risk Management
        if 'enable_daily_limits' in shared_dict:
            config.shared_settings.enable_daily_limits = shared_dict['enable_daily_limits']
        if 'global_daily_loss_limit' in shared_dict:
            config.shared_settings.global_daily_loss_limit = shared_dict['global_daily_loss_limit']
        if 'max_portfolio_drawdown_pct' in shared_dict:
            config.shared_settings.max_portfolio_drawdown_pct = shared_dict['max_portfolio_drawdown_pct']
        if 'enable_global_trailing_stops' in shared_dict:
            config.shared_settings.enable_global_trailing_stops = shared_dict['enable_global_trailing_stops']
        if 'global_trailing_distance_pct' in shared_dict:
            config.shared_settings.global_trailing_distance_pct = shared_dict['global_trailing_distance_pct']
        if 'global_trailing_trigger_pct' in shared_dict:
            config.shared_settings.global_trailing_trigger_pct = shared_dict['global_trailing_trigger_pct']
    
    # Synchronize active_strategies with individual strategy enabled flags
    # If a strategy is in active_strategies, ensure its enabled flag is True
    for strategy_type in config.active_strategies:
        settings = config.get_strategy_settings(strategy_type)
        settings.enabled = True
    
    # Apply shared settings to individual strategies
    config.apply_shared_settings_to_strategies()
    
    return config

def save_detailed_config(config: TradingConfig, filename: str):
    """Save detailed configuration to file"""
    config_dict = config_to_dict(config)
    
    # Ensure filename has config_ prefix
    if not filename.startswith('config_'):
        filename = f'config_{filename}'
    
    with open(filename, 'w') as f:
        json.dump(config_dict, f, indent=2)

def load_detailed_config(control_panel: ControlPanel, filename: str):
    """Load detailed configuration from file"""
    with open(filename, 'r') as f:
        config_dict = json.load(f)
    
    control_panel.config = dict_to_config(config_dict)

if __name__ == "__main__":
    render_config_manager()