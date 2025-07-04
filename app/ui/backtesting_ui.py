import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os
import warnings
import json

# Suppress specific warnings from backtesting library and bokeh
warnings.filterwarnings('ignore', message='Superimposed OHLC plot matches the original plot. Skipping.')
warnings.filterwarnings('ignore', message='no explicit representation of timezones available for np.datetime64')
warnings.filterwarnings('ignore', category=UserWarning, module='bokeh')
warnings.filterwarnings('ignore', category=UserWarning, module='backtesting')

# Add the app directory to the path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from config import TradingConfig, StrategyType
from backtesting_system import BacktestingAdapter
from config_manager import dict_to_config, config_to_dict
from cycle_analysis import CycleAnalysisReport, Cycle, CycleStatus

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

def render_backtesting_interface(config: TradingConfig):
    """Render the backtesting interface"""
    render_title_with_tooltip(
        "📈 Backtesting System", 
        "Test your trading strategies with historical data to evaluate performance and optimize parameters",
        "header"
    )
    st.markdown("Test your trading strategies with historical data")
    
    # Initialize session state for selected strategies
    if 'backtest_selected_strategies' not in st.session_state:
        st.session_state.backtest_selected_strategies = []
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_title_with_tooltip(
            "📊 Backtest Configuration", 
            "Configure strategies, parameters, and data settings for your backtest",
            "subheader"
        )
        
        # Strategy Selection
        st.markdown("**Strategy Selection**")
        available_strategies = list(StrategyType)
        strategy_options = {strategy.value: strategy for strategy in available_strategies}
        
        selected_strategy_names = st.multiselect(
            "Select Strategies to Test",
            options=list(strategy_options.keys()),
            default=st.session_state.backtest_selected_strategies,
            help="Choose one or more strategies to include in the backtest",
            key="strategy_multiselect"
        )
        
        # Update session state
        st.session_state.backtest_selected_strategies = selected_strategy_names
        selected_strategies = [strategy_options[name] for name in selected_strategy_names]
        
        # Configuration Upload Section
        st.markdown("**📁 Load Saved Configuration**")
        
        # Quick load from saved configurations
        config_files = [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('config_')]
        if config_files:
            st.markdown("**Quick Load from Saved Configurations:**")
            col_quick1, col_quick2 = st.columns([3, 1])
            
            with col_quick1:
                selected_saved_config = st.selectbox(
                    "Select a saved configuration",
                    config_files,
                    key="quick_load_config",
                    help="Choose from previously saved configuration files"
                )
            
            with col_quick2:
                if st.button("🚀 Quick Load", key="quick_load_button"):
                    try:
                        with open(selected_saved_config, 'r') as f:
                            config_data = json.load(f)
                        uploaded_trading_config = dict_to_config(config_data)
                        
                        # Update ALL configuration fields from loaded config
                        config.account_type = uploaded_trading_config.account_type
                        config.execution_mode = uploaded_trading_config.execution_mode
                        config.active_strategies = uploaded_trading_config.active_strategies
                        config.tickers = uploaded_trading_config.tickers
                        config.timeframe = uploaded_trading_config.timeframe
                        config.duration = uploaded_trading_config.duration
                        config.data_type = uploaded_trading_config.data_type
                        config.position_size_type = uploaded_trading_config.position_size_type
                        config.position_size_value = uploaded_trading_config.position_size_value
                        
                        # Update strategy settings objects completely
                        config.cdm_settings = uploaded_trading_config.cdm_settings
                        config.wdm_settings = uploaded_trading_config.wdm_settings
                        config.zrm_settings = uploaded_trading_config.zrm_settings
                        config.izrm_settings = uploaded_trading_config.izrm_settings
                        
                        # Update shared settings (CRITICAL for global_max_concurrent_cycles)
                        config.shared_settings = uploaded_trading_config.shared_settings
                        
                        # Update session state for selected strategies
                        loaded_strategy_names = [strategy.value for strategy in uploaded_trading_config.active_strategies]
                        st.session_state.backtest_selected_strategies = loaded_strategy_names
                        
                        # Update the session state config object
                        st.session_state.backtest_config = config
                        
                        # Force clear any cached strategy settings
                        if 'strategy_settings_cache' in st.session_state:
                            del st.session_state.strategy_settings_cache
                        
                        st.success(f"✅ Configuration '{selected_saved_config}' loaded! Active strategies: {', '.join(loaded_strategy_names)}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to load configuration: {str(e)}")
        
        with st.expander("Upload Configuration File", expanded=False):
            st.info("💡 Upload a saved configuration file to automatically set up strategies and parameters for backtesting.")
            
            col_upload1, col_upload2 = st.columns([2, 1])
            
            with col_upload1:
                uploaded_config = st.file_uploader(
                    "Choose configuration file",
                    type="json",
                    key="backtest_config_upload",
                    help="Upload a .json configuration file saved from the Configuration Manager"
                )
            
            with col_upload2:
                if uploaded_config is not None:
                    if st.button("🔄 Apply Config", key="apply_uploaded_config"):
                        try:
                            config_data = json.load(uploaded_config)
                            uploaded_trading_config = dict_to_config(config_data)
                            
                            # Update ALL configuration fields from uploaded config
                            config.account_type = uploaded_trading_config.account_type
                            config.execution_mode = uploaded_trading_config.execution_mode
                            config.active_strategies = uploaded_trading_config.active_strategies
                            config.tickers = uploaded_trading_config.tickers
                            config.timeframe = uploaded_trading_config.timeframe
                            config.duration = uploaded_trading_config.duration
                            config.data_type = uploaded_trading_config.data_type
                            config.position_size_type = uploaded_trading_config.position_size_type
                            config.position_size_value = uploaded_trading_config.position_size_value
                            
                            # Update strategy settings objects completely
                            config.cdm_settings = uploaded_trading_config.cdm_settings
                            config.wdm_settings = uploaded_trading_config.wdm_settings
                            config.zrm_settings = uploaded_trading_config.zrm_settings
                            config.izrm_settings = uploaded_trading_config.izrm_settings
                            
                            # Update shared settings (CRITICAL for global_max_concurrent_cycles)
                            config.shared_settings = uploaded_trading_config.shared_settings
                            
                            # Update session state for selected strategies
                            loaded_strategy_names = [strategy.value for strategy in uploaded_trading_config.active_strategies]
                            st.session_state.backtest_selected_strategies = loaded_strategy_names
                            
                            # Update the session state config object
                            st.session_state.backtest_config = config
                            
                            # Force clear any cached strategy settings
                            if 'strategy_settings_cache' in st.session_state:
                                del st.session_state.strategy_settings_cache
                            
                            st.success(f"✅ Configuration loaded! Active strategies: {', '.join(loaded_strategy_names)}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Failed to load configuration: {str(e)}")
            
            # Show loaded configuration preview
            if uploaded_config is not None:
                with st.expander("📋 Configuration Preview", expanded=False):
                    try:
                        config_data = json.load(uploaded_config)
                        st.json(config_data)
                    except Exception as e:
                        st.error(f"Failed to preview configuration: {str(e)}")
        
        if not selected_strategies:
            st.warning("Please select at least one strategy to proceed or upload a configuration file.")
            return
        
        # Display selected strategy settings
        st.markdown("**Active Strategy Configuration**")
        
        # Show current configuration summary
        if selected_strategies:
            config_summary_col1, config_summary_col2 = st.columns(2)
            
            with config_summary_col1:
                st.info(f"📊 **Active Strategies:** {', '.join([s.value for s in selected_strategies])}")
            
            with config_summary_col2:
                total_allocation = sum([config.get_strategy_settings(s).capital_allocation for s in selected_strategies])
                st.info(f"💰 **Total Capital Allocation:** {total_allocation:.2f}")
        
        # Detailed strategy settings
        for strategy in selected_strategies:
            with st.expander(f"{strategy.value} Settings", expanded=False):
                settings = config.get_strategy_settings(strategy)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Capital Allocation", f"{settings.capital_allocation:.2f}")
                    st.metric("Max Orders", settings.max_orders)
                    st.metric("Enabled", "✅" if settings.enabled else "❌")
                with col_b:
                    st.metric("Order Distances", str(settings.order_distances))
                    st.metric("Order Sizes", str(settings.order_sizes))
                    if hasattr(settings, 'order_tps'):
                        st.metric("Take Profits", str(settings.order_tps))
                    elif hasattr(settings, 'order_sls'):
                        st.metric("Stop Losses", str(settings.order_sls))
        
        # Symbol Input
        st.markdown("**Market Data**")
        symbol = st.text_input(
            "Ticker Symbol",
            value="AAPL",
            help="Enter the stock symbol (e.g., AAPL, MSFT, GOOGL)"
        ).upper()
        
        # Timeframe Selection (moved before date selection to adjust date limits)
        timeframe_options = {
            "1 Minute": "1m",
            "5 Minutes": "5m",
            "15 Minutes": "15m",
            "30 Minutes": "30m",
            "1 Hour": "1h",
            "2 Hours": "2h",
            "4 Hours": "4h",
            "1 Day": "1d",
            "1 Week": "1wk",
            "1 Month": "1mo"
        }
        
        timeframe_display = st.selectbox(
            "Timeframe",
            options=list(timeframe_options.keys()),
            index=4,  # Default to 1 Hour
            help="Select the timeframe for the backtest data"
        )
        timeframe = timeframe_options[timeframe_display]
        
        # Determine date limits based on timeframe
        # yfinance has limitations: intraday data (1m, 5m, 15m, 30m, 1h, 2h, 4h) is only available for the last 730 days
        intraday_timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h"]
        
        if timeframe in intraday_timeframes:
            # For intraday data, limit to last 700 days (safe margin within 730 day limit)
            max_days_back = 700
            default_days_back = 90  # Default to 3 months for intraday
            date_help = f"⚠️ Intraday data is limited to the last {max_days_back} days by yfinance"
        else:
            # For daily and longer timeframes, allow longer periods
            max_days_back = 3650  # ~10 years
            default_days_back = 365  # Default to 1 year
            date_help = "Select the date range for backtesting"
        
        # Calculate date limits
        max_start_date = datetime.now().date() - timedelta(days=max_days_back)
        default_start_date = datetime.now().date() - timedelta(days=default_days_back)
        
        # Date Range Selection
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input(
                "Start Date",
                value=default_start_date,
                min_value=max_start_date,
                max_value=datetime.now().date(),
                help=date_help
            )
        
        with col_date2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                min_value=start_date,
                max_value=datetime.now().date(),
                help="End date for the backtest"
            )
        
        # Initial Cash
        initial_cash = st.number_input(
            "Initial Cash ($)",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=1000.0,
            help="Starting capital for the backtest"
        )
        
        # Validation
        if start_date >= end_date:
            st.error("Start date must be before end date.")
            return
        
        # Additional validation for yfinance limitations
        days_back = (datetime.now().date() - start_date).days
        if timeframe in intraday_timeframes and days_back > 730:
            st.error(f"⚠️ Intraday data ({timeframe_display}) is only available for the last 730 days. Your start date is {days_back} days ago. Please select a more recent start date.")
            return
        
        # Show warning if approaching the limit
        if timeframe in intraday_timeframes and days_back > 600:
            st.warning(f"⚠️ You're requesting data from {days_back} days ago. Intraday data may be limited. If you encounter errors, try a more recent date range.")
        
        # Run Backtest Button
        run_backtest = st.button(
            "🚀 Run Backtest",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        st.subheader("📋 Backtest Results")
        
        if run_backtest:
            if not selected_strategies:
                st.error("Please select at least one strategy.")
                return
            
            try:
                with st.spinner(f"Running backtest for {symbol} from {start_date} to {end_date}..."):
                    # Create backtesting adapter
                    adapter = BacktestingAdapter(config, selected_strategies)
                    
                    # Run backtest
                    bt, metrics, cycle_report = adapter.run_backtest(
                        symbol=symbol,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        interval=timeframe,
                        initial_cash=initial_cash
                    )
                    
                    # Store results in session state
                    st.session_state.backtest_results = {
                        'bt': bt,
                        'metrics': metrics,
                        'cycle_report': cycle_report,
                        'symbol': symbol,
                        'strategies': selected_strategies,
                        'timeframe': timeframe_display,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    
                    st.success("✅ Backtest completed successfully!")
            
            except Exception as e:
                st.error(f"❌ Error running backtest: {str(e)}")
                return
        
        # Display results if available
        if 'backtest_results' in st.session_state:
            results = st.session_state.backtest_results
            metrics = results['metrics']
            
            # Summary metrics
            st.markdown("**📊 Performance Summary**")
            
            # Key metrics in columns
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric(
                    "Total Return",
                    f"{metrics['Return [%]']:.2f}%",
                    delta=f"{metrics['Return [%]'] - metrics['Buy & Hold Return [%]']:.2f}% vs B&H"
                )
                st.metric(
                    "Sharpe Ratio",
                    f"{metrics['Sharpe Ratio']:.3f}" if metrics['Sharpe Ratio'] is not None else "N/A"
                )
            
            with metric_col2:
                st.metric(
                    "Win Rate",
                    f"{metrics['Win Rate [%]']:.1f}%" if metrics['Win Rate [%]'] is not None else "N/A"
                )
                st.metric(
                    "Max Drawdown",
                    f"{metrics['Max. Drawdown [%]']:.2f}%"
                )
            
            with metric_col3:
                st.metric(
                    "Total Trades",
                    f"{int(metrics['# Trades'])}" if metrics['# Trades'] is not None else "0"
                )
                st.metric(
                    "Profit Factor",
                    f"{metrics['Profit Factor']:.2f}" if metrics['Profit Factor'] is not None else "N/A"
                )
            
            # Detailed metrics table
            st.markdown("**📈 Detailed Metrics**")
            
            # Create metrics dataframe for better display
            metrics_df = pd.DataFrame([
                {"Metric": "Start Date", "Value": str(metrics['Start'])},
                {"Metric": "End Date", "Value": str(metrics['End'])},
                {"Metric": "Duration", "Value": str(metrics['Duration'])},
                {"Metric": "Exposure Time", "Value": f"{metrics['Exposure Time [%]']:.1f}%"},
                {"Metric": "Final Equity", "Value": f"${metrics['Equity Final [$]']:,.2f}"},
                {"Metric": "Peak Equity", "Value": f"${metrics['Equity Peak [$]']:,.2f}"},
                {"Metric": "Annual Return", "Value": f"{metrics['Return (Ann.) [%]']:.2f}%" if metrics['Return (Ann.) [%]'] is not None else "N/A"},
                {"Metric": "Annual Volatility", "Value": f"{metrics['Volatility (Ann.) [%]']:.2f}%" if metrics['Volatility (Ann.) [%]'] is not None else "N/A"},
                {"Metric": "Sortino Ratio", "Value": f"{metrics['Sortino Ratio']:.3f}" if metrics['Sortino Ratio'] is not None else "N/A"},
                {"Metric": "Calmar Ratio", "Value": f"{metrics['Calmar Ratio']:.3f}" if metrics['Calmar Ratio'] is not None else "N/A"},
                {"Metric": "Best Trade", "Value": f"{metrics['Best Trade [%]']:.2f}%" if metrics['Best Trade [%]'] is not None else "N/A"},
                {"Metric": "Worst Trade", "Value": f"{metrics['Worst Trade [%]']:.2f}%" if metrics['Worst Trade [%]'] is not None else "N/A"},
                {"Metric": "Average Trade", "Value": f"{metrics['Avg. Trade [%]']:.2f}%" if metrics['Avg. Trade [%]'] is not None else "N/A"},
                {"Metric": "Expectancy", "Value": f"{metrics['Expectancy [%]']:.2f}%" if metrics['Expectancy [%]'] is not None else "N/A"},
            ])
            
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Plot button
            if st.button("📊 Show Backtest Chart", use_container_width=True):
                try:
                    with st.spinner("Generating chart..."):
                        # Try to generate the native backtesting.py chart with trade markers
                        try:
                            # Try to set bokeh output for better compatibility
                            try:
                                import backtesting
                                if hasattr(backtesting, 'set_bokeh_output'):
                                    backtesting.set_bokeh_output(notebook=False)
                            except:
                                pass  # Continue without bokeh settings if not available
                            
                            # Generate the native backtesting.py plot with trade markers
                            # This will show candlesticks, equity curve, and trade entry/exit points
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                plot_fig = results['bt'].plot(
                                    resample=False,  # Avoid upsampling issues
                                    show_legend=True,
                                    plot_width=None,  # Let it auto-size
                                    plot_equity=True,
                                    plot_return=False,
                                    plot_pl=True,
                                    plot_volume=False,
                                    plot_drawdown=False,
                                    superimpose=False  # Disable superimpose to avoid upsampling issues
                                )
                            
                            # Display success message
                            st.success("✅ Interactive backtesting chart generated successfully!")
                            st.info("📊 The chart shows:")
                            st.markdown("""
                            - **Candlestick price data** with OHLC values
                            - **Portfolio equity curve** (blue line)
                            - **Buy & Hold benchmark** (orange dashed line)
                            - **Trade entry points** (green triangles pointing up)
                            - **Trade exit points** (red triangles pointing down)
                            - **Interactive zoom and pan** capabilities
                            """)
                            
                            # Note about the chart
                            st.warning("📝 **Note:** The interactive chart opens in a separate browser window/tab. If it doesn't appear automatically, check your browser's popup blocker.")
                            
                        except Exception as plot_error:
                            # Enhanced fallback: Create comprehensive plotly chart with trade markers
                            st.warning(f"Native plot failed ({str(plot_error)}). Generating enhanced chart with trade markers...")
                            
                            try:
                                # Get data from backtest results
                                bt_result = results['bt']
                                equity_data = bt_result._results['_equity_curve']
                                trades_data = bt_result._results['_trades']
                                price_data = results['data']
                                
                                # Create comprehensive plotly chart
                                import plotly.graph_objects as go
                                from plotly.subplots import make_subplots
                                
                                # Create subplots: price chart on top, equity curve below
                                fig = make_subplots(
                                    rows=2, cols=1,
                                    shared_xaxes=True,
                                    vertical_spacing=0.1,
                                    subplot_titles=('Price Chart with Trades', 'Portfolio Equity'),
                                    row_heights=[0.7, 0.3]
                                )
                                 
                                # Add candlestick chart
                                fig.add_trace(
                                    go.Candlestick(
                                        x=price_data.index,
                                        open=price_data['Open'],
                                        high=price_data['High'],
                                        low=price_data['Low'],
                                        close=price_data['Close'],
                                        name='Price',
                                        showlegend=False
                                    ),
                                    row=1, col=1
                                )
                                 
                                # Add trade markers if trades exist
                                if not trades_data.empty:
                                    # Entry points (buy trades)
                                    entry_trades = trades_data[trades_data['Size'] > 0]
                                    if not entry_trades.empty:
                                        fig.add_trace(
                                            go.Scatter(
                                                x=entry_trades['EntryTime'],
                                                y=entry_trades['EntryPrice'],
                                                mode='markers',
                                                marker=dict(
                                                    symbol='triangle-up',
                                                    size=12,
                                                    color='green',
                                                    line=dict(width=2, color='darkgreen')
                                                ),
                                                name='Buy Entry',
                                                hovertemplate='<b>Buy Entry</b><br>' +
                                                            'Date: %{x}<br>' +
                                                            'Price: $%{y:.2f}<br>' +
                                                            '<extra></extra>'
                                            ),
                                            row=1, col=1
                                        )
                                    
                                    # Exit points (sell trades)
                                    exit_trades = trades_data[trades_data['Size'] < 0]
                                    if not exit_trades.empty:
                                        fig.add_trace(
                                            go.Scatter(
                                                x=exit_trades['ExitTime'],
                                                y=exit_trades['ExitPrice'],
                                                mode='markers',
                                                marker=dict(
                                                    symbol='triangle-down',
                                                    size=12,
                                                    color='red',
                                                    line=dict(width=2, color='darkred')
                                                ),
                                                name='Sell Exit',
                                                hovertemplate='<b>Sell Exit</b><br>' +
                                                            'Date: %{x}<br>' +
                                                            'Price: $%{y:.2f}<br>' +
                                                            'P&L: $%{customdata:.2f}<br>' +
                                                            '<extra></extra>',
                                                customdata=exit_trades['PnL']
                                            ),
                                            row=1, col=1
                                        )
                                 
                                # Add equity curve
                                fig.add_trace(
                                    go.Scatter(
                                        x=equity_data.index,
                                        y=equity_data['Equity'],
                                        mode='lines',
                                        name='Portfolio Equity',
                                        line=dict(color='blue', width=2),
                                        hovertemplate='<b>Portfolio Value</b><br>' +
                                                    'Date: %{x}<br>' +
                                                    'Value: $%{y:,.2f}<br>' +
                                                    '<extra></extra>'
                                    ),
                                    row=2, col=1
                                )
                                
                                # Add buy & hold comparison if available
                                if 'Buy&Hold' in equity_data.columns:
                                    fig.add_trace(
                                        go.Scatter(
                                            x=equity_data.index,
                                            y=equity_data['Buy&Hold'],
                                            mode='lines',
                                            name='Buy & Hold',
                                            line=dict(color='orange', width=2, dash='dash'),
                                            hovertemplate='<b>Buy & Hold</b><br>' +
                                                        'Date: %{x}<br>' +
                                                        'Value: $%{y:,.2f}<br>' +
                                                        '<extra></extra>'
                                        ),
                                        row=2, col=1
                                    )
                                
                                # Update layout
                                fig.update_layout(
                                    title=f"📊 Comprehensive Backtest Analysis - {results['symbol']}",
                                    xaxis_title="Date",
                                    yaxis_title="Price ($)",
                                    xaxis2_title="Date",
                                    yaxis2_title="Portfolio Value ($)",
                                    hovermode='x unified',
                                    showlegend=True,
                                    height=800,
                                    template='plotly_white'
                                )
                                
                                # Remove range slider for cleaner look
                                fig.update_layout(xaxis_rangeslider_visible=False)
                                
                                # Display the enhanced chart
                                st.plotly_chart(fig, use_container_width=True)
                                st.success("✅ Enhanced chart with trade markers generated successfully!")
                                
                                # Display trade summary
                                if not trades_data.empty:
                                    st.markdown("**🎯 Trade Summary**")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Total Trades", len(trades_data))
                                    with col2:
                                        winning_trades = len(trades_data[trades_data['PnL'] > 0])
                                        st.metric("Winning Trades", winning_trades)
                                    with col3:
                                        losing_trades = len(trades_data[trades_data['PnL'] < 0])
                                        st.metric("Losing Trades", losing_trades)
                                    with col4:
                                        win_rate = (winning_trades / len(trades_data) * 100) if len(trades_data) > 0 else 0
                                        st.metric("Win Rate", f"{win_rate:.1f}%")
                              
                            except Exception as fallback_error:
                                st.error(f"Error generating enhanced chart: {str(fallback_error)}")
                                st.info("💡 Try using a different timeframe or date range if the chart generation continues to fail.")
                                
                                # Show basic metrics table as final fallback
                                st.markdown("**📊 Basic Results (Chart unavailable)**")
                                if 'metrics' in results:
                                    metrics_dict = results['metrics']
                                    basic_metrics = {
                                        'Total Return': f"{metrics_dict.get('Return [%]', 0):.2f}%",
                                        'Max Drawdown': f"{metrics_dict.get('Max. Drawdown [%]', 0):.2f}%",
                                        'Sharpe Ratio': f"{metrics_dict.get('Sharpe Ratio', 0):.2f}",
                                        'Total Trades': f"{metrics_dict.get('# Trades', 0)}"
                                    }
                                    
                                    cols = st.columns(len(basic_metrics))
                                    for i, (key, value) in enumerate(basic_metrics.items()):
                                        with cols[i]:
                                            st.metric(key, value)
                                              
                        except Exception as e:
                            st.error(f"Error generating chart: {str(e)}")
                            st.info("💡 Try using a different timeframe or date range if the chart generation continues to fail.")
                
                except Exception as outer_e:
                    st.error(f"Error in chart generation: {str(outer_e)}")
                
            # Download results
            if st.button("💾 Download Results", use_container_width=True):
                try:
                    # Create downloadable CSV
                    csv_data = metrics_df.to_csv(index=False)
                    st.download_button(
                        label="Download Metrics CSV",
                        data=csv_data,
                        file_name=f"backtest_results_{results['symbol']}_{results['start_date']}_{results['end_date']}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error preparing download: {str(e)}")
            
            # Add Cycle Analysis Section
            render_cycle_analysis_section(results)
        
        else:
            st.info("👆 Configure your backtest parameters and click 'Run Backtest' to see results.")
            
            # Show example
            st.markdown("**💡 Example Configuration:**")
            st.markdown("""
            - **Strategies**: CDM (Counter Direction Martingale)
            - **Symbol**: AAPL
            - **Period**: Last 6 months
            - **Timeframe**: 1 Hour
            - **Initial Cash**: $100,000
            """)

def render_cycle_analysis_section(results):
    """Render cycle analysis section from backtest results"""
    st.markdown("---")
    render_title_with_tooltip(
        "🔄 Cycle Analysis", 
        "Detailed analysis of trading cycles extracted from backtest results including performance metrics and distributions",
        "header"
    )
    st.markdown("Detailed analysis of trading cycles from backtest results")
    
    try:
        # Get trades data from backtest results
        bt_result = results['bt']
        trades_data = bt_result._results['_trades']
        
        if trades_data.empty:
            st.warning("No trades found in backtest results for cycle analysis.")
            return
        
        # Convert trades to cycles (simplified approach)
        cycles = []
        cycle_id = 1
        
        # Group trades into cycles (each complete trade = one cycle)
        for _, trade in trades_data.iterrows():
            if trade['Size'] > 0:  # Entry trade
                cycle = Cycle(
                    cycle_id=f"BT_CYCLE_{cycle_id}",
                    strategy_type=results.get('strategy', 'BACKTEST'),
                    symbol=results['symbol'],
                    start_time=trade['EntryTime'],
                    end_time=trade['ExitTime'] if 'ExitTime' in trade else trade['EntryTime'],
                    status=CycleStatus.COMPLETED,
                    total_investment=abs(trade['Size'] * trade['EntryPrice']),
                    max_investment=abs(trade['Size'] * trade['EntryPrice']),
                    realized_pnl=trade['PnL']
                )
                cycles.append(cycle)
                cycle_id += 1
        
        if not cycles:
            st.warning("No complete cycles found for analysis.")
            return
        
        # Create cycle analysis report
        cycle_report = CycleAnalysisReport()
        cycle_report.cycles = cycles
        
        # Import cycle analysis UI functions
        from cycle_analysis_ui import render_cycle_overview, render_performance_analysis, render_cycle_comparison
        
        # Create tabs for different analysis views
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Performance", "⚖️ Comparison"])
        
        with tab1:
            render_cycle_overview(cycle_report.export_to_dataframe(), cycle_report)
        
        with tab2:
            render_performance_analysis(cycle_report.export_to_dataframe(), results['symbol'])
        
        with tab3:
            render_cycle_comparison(cycle_report.export_to_dataframe())
        
        # Additional backtest-specific analysis
        render_title_with_tooltip(
            "🎯 Backtest-Specific Insights", 
            "Key metrics and insights specific to the backtest including cycle duration, win rates, and average profitability",
            "markdown"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_cycle_duration = sum([(c.end_time - c.start_time).total_seconds() / 3600 for c in cycles]) / len(cycles)
            st.metric("Avg Cycle Duration", f"{avg_cycle_duration:.1f} hours")
        
        with col2:
            total_cycles = len(cycles)
            winning_cycles = len([c for c in cycles if c.realized_pnl > 0])
            cycle_win_rate = (winning_cycles / total_cycles * 100) if total_cycles > 0 else 0
            st.metric("Cycle Win Rate", f"{cycle_win_rate:.1f}%")
        
        with col3:
            avg_pnl_per_cycle = sum([c.realized_pnl for c in cycles]) / len(cycles)
            st.metric("Avg PnL per Cycle", f"${avg_pnl_per_cycle:.2f}")
        
        # Cycle performance distribution
        render_title_with_tooltip(
            "📊 Cycle Performance Distribution", 
            "Histogram showing the distribution of profit and loss across all trading cycles",
            "markdown"
        )
        
        cycle_pnls = [c.realized_pnl for c in cycles]
        
        import plotly.express as px
        fig_hist = px.histogram(
            x=cycle_pnls,
            nbins=20,
            title="Distribution of Cycle P&L",
            labels={'x': 'Cycle P&L ($)', 'y': 'Frequency'}
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Export cycle data
        render_title_with_tooltip(
            "💾 Export Cycle Data", 
            "Download detailed cycle analysis data as CSV for further analysis or record keeping",
            "markdown"
        )
        if st.button("📥 Download Cycle Analysis CSV"):
            cycle_df = cycle_report.export_to_dataframe()
            csv_data = cycle_df.to_csv(index=False)
            st.download_button(
                label="Download Cycle Data",
                data=csv_data,
                file_name=f"cycle_analysis_{results['symbol']}_{results['start_date']}_{results['end_date']}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error generating cycle analysis: {str(e)}")
        st.info("💡 Cycle analysis requires completed trades with entry/exit data.")

def main():
    """Main function for standalone testing"""
    st.set_page_config(
        page_title="Backtesting System",
        page_icon="📈",
        layout="wide"
    )
    
    # Load config (you might need to adjust this path)
    try:
        config = TradingConfig()
        render_backtesting_interface(config)
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")

if __name__ == "__main__":
    main()