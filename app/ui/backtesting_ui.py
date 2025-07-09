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
    
    # Initialize session state for stored backtests
    if 'stored_backtests' not in st.session_state:
        st.session_state.stored_backtests = {}
    
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
                        'end_date': end_date,
                        'timestamp': datetime.now()
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
            
            # Detailed Trades Table
            st.markdown("---")
            render_title_with_tooltip(
                "📋 Detailed Trades History", 
                "Complete list of all trades executed during the backtest with entry/exit details, P&L, and performance metrics",
                "header"
            )
            
            try:
                # Get trades data from backtest results
                bt_result = results['bt']
                trades_data = bt_result._results['_trades']
                
                if not trades_data.empty:
                    # Process and format trades data for display
                    trades_display = trades_data.copy()
                    
                    # Format datetime columns
                    if 'EntryTime' in trades_display.columns:
                        trades_display['Entry Date'] = pd.to_datetime(trades_display['EntryTime']).dt.strftime('%Y-%m-%d %H:%M')
                    if 'ExitTime' in trades_display.columns:
                        trades_display['Exit Date'] = pd.to_datetime(trades_display['ExitTime']).dt.strftime('%Y-%m-%d %H:%M')
                    
                    # Format price columns
                    if 'EntryPrice' in trades_display.columns:
                        trades_display['Entry Price'] = trades_display['EntryPrice'].round(4)
                    if 'ExitPrice' in trades_display.columns:
                        trades_display['Exit Price'] = trades_display['ExitPrice'].round(4)
                    
                    # Format P&L and percentage columns
                    if 'PnL' in trades_display.columns:
                        trades_display['P&L ($)'] = trades_display['PnL'].round(2)
                        trades_display['Result'] = trades_display['PnL'].apply(lambda x: '✅ Win' if x > 0 else '❌ Loss' if x < 0 else '➖ Break-even')
                    
                    if 'ReturnPct' in trades_display.columns:
                        trades_display['Return (%)'] = (trades_display['ReturnPct'] * 100).round(2)
                    
                    # Calculate trade duration if both entry and exit times are available
                    if 'EntryTime' in trades_display.columns and 'ExitTime' in trades_display.columns:
                        duration = pd.to_datetime(trades_display['ExitTime']) - pd.to_datetime(trades_display['EntryTime'])
                        trades_display['Duration'] = duration.apply(lambda x: f"{x.total_seconds() / 3600:.1f}h" if pd.notna(x) else 'N/A')
                    
                    # Add trade number
                    trades_display['Trade #'] = range(1, len(trades_display) + 1)
                    
                    # Select and reorder columns for display
                    display_columns = ['Trade #']
                    if 'Entry Date' in trades_display.columns:
                        display_columns.append('Entry Date')
                    if 'Exit Date' in trades_display.columns:
                        display_columns.append('Exit Date')
                    if 'Duration' in trades_display.columns:
                        display_columns.append('Duration')
                    if 'Size' in trades_display.columns:
                        display_columns.append('Size')
                    if 'Entry Price' in trades_display.columns:
                        display_columns.append('Entry Price')
                    if 'Exit Price' in trades_display.columns:
                        display_columns.append('Exit Price')
                    if 'P&L ($)' in trades_display.columns:
                        display_columns.append('P&L ($)')
                    if 'Return (%)' in trades_display.columns:
                        display_columns.append('Return (%)')
                    if 'Result' in trades_display.columns:
                        display_columns.append('Result')
                    
                    # Filter to only include columns that exist
                    available_columns = [col for col in display_columns if col in trades_display.columns]
                    
                    if available_columns:
                        trades_table = trades_display[available_columns]
                        
                        # Display summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            total_trades = len(trades_table)
                            st.metric("Total Trades", total_trades)
                        with col2:
                            if 'P&L ($)' in trades_table.columns:
                                winning_trades = len(trades_table[trades_table['P&L ($)'] > 0])
                                st.metric("Winning Trades", winning_trades)
                        with col3:
                            if 'P&L ($)' in trades_table.columns:
                                losing_trades = len(trades_table[trades_table['P&L ($)'] < 0])
                                st.metric("Losing Trades", losing_trades)
                        with col4:
                            if 'P&L ($)' in trades_table.columns and total_trades > 0:
                                win_rate = (winning_trades / total_trades * 100)
                                st.metric("Win Rate", f"{win_rate:.1f}%")
                        
                        # Display the trades table
                        st.markdown("**📊 All Trades:**")
                        st.dataframe(
                            trades_table,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'P&L ($)': st.column_config.NumberColumn(
                                    'P&L ($)',
                                    format="$%.2f"
                                ),
                                'Return (%)': st.column_config.NumberColumn(
                                    'Return (%)',
                                    format="%.2f%%"
                                ),
                                'Entry Price': st.column_config.NumberColumn(
                                    'Entry Price',
                                    format="$%.4f"
                                ),
                                'Exit Price': st.column_config.NumberColumn(
                                    'Exit Price',
                                    format="$%.4f"
                                )
                            }
                        )
                        
                        # Download trades data
                        if st.button("📥 Download Trades CSV", key="download_trades_csv"):
                            trades_csv = trades_table.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Trades Data",
                                data=trades_csv,
                                file_name=f"trades_history_{results['symbol']}_{results['start_date']}_{results['end_date']}.csv",
                                mime="text/csv",
                                key="download_trades_button"
                            )
                    else:
                        st.info("📊 No trade columns available for display.")
                else:
                    st.info("📊 No trades were executed during this backtest.")
                    
            except Exception as e:
                 st.error(f"Error displaying trades data: {str(e)}")
                 st.info("💡 Trades table unavailable - this may occur with certain strategy configurations.")
             
            # Detailed Cycles Table
            st.markdown("---")
            render_title_with_tooltip(
                "🔄 Detailed Cycles History", 
                "Complete analysis of all trading cycles including investment levels, recovery patterns, and performance metrics",
                "header"
            )
             
            try:
                # Get trades data and convert to cycles
                bt_result = results['bt']
                trades_data = bt_result._results['_trades']
                
                if not trades_data.empty:
                    # Convert trades to cycles (simplified approach - each trade = one cycle)
                    cycles_display_data = []
                    cycle_id = 1
                    
                    for _, trade in trades_data.iterrows():
                        if trade['Size'] > 0:  # Entry trade
                            # Calculate cycle metrics
                            investment = abs(trade['Size'] * trade['EntryPrice'])
                            pnl = trade['PnL'] if 'PnL' in trade else 0
                            
                            # Calculate duration
                            if 'EntryTime' in trade and 'ExitTime' in trade:
                                entry_time = pd.to_datetime(trade['EntryTime'])
                                exit_time = pd.to_datetime(trade['ExitTime'])
                                duration_hours = (exit_time - entry_time).total_seconds() / 3600
                                duration_str = f"{duration_hours:.1f}h"
                            else:
                                duration_str = "N/A"
                            
                            # Calculate ROI
                            roi_pct = (pnl / investment * 100) if investment > 0 else 0
                            
                            # Determine cycle result
                            if pnl > 0:
                                result = "✅ Profitable"
                                result_emoji = "✅"
                            elif pnl < 0:
                                result = "❌ Loss"
                                result_emoji = "❌"
                            else:
                                result = "➖ Break-even"
                                result_emoji = "➖"
                            
                            cycle_data = {
                                'Cycle #': cycle_id,
                                'Start Time': entry_time.strftime('%Y-%m-%d %H:%M') if 'EntryTime' in trade else 'N/A',
                                'End Time': exit_time.strftime('%Y-%m-%d %H:%M') if 'ExitTime' in trade else 'N/A',
                                'Duration': duration_str,
                                'Strategy': results.get('strategy', 'Backtest'),
                                'Symbol': results['symbol'],
                                'Investment ($)': investment,
                                'Max Investment ($)': investment,  # Simplified - same as investment for single trades
                                'Entry Price': trade['EntryPrice'] if 'EntryPrice' in trade else 0,
                                'Exit Price': trade['ExitPrice'] if 'ExitPrice' in trade else 0,
                                'Position Size': abs(trade['Size']) if 'Size' in trade else 0,
                                'Realized P&L ($)': pnl,
                                'ROI (%)': roi_pct,
                                'Result': result,
                                'Status': '✅ Completed'
                            }
                            cycles_display_data.append(cycle_data)
                            cycle_id += 1
                    
                    if cycles_display_data:
                        cycles_df = pd.DataFrame(cycles_display_data)
                        
                        # Display cycle summary metrics
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            total_cycles = len(cycles_df)
                            st.metric("Total Cycles", total_cycles)
                        
                        with col2:
                            profitable_cycles = len(cycles_df[cycles_df['Realized P&L ($)'] > 0])
                            st.metric("Profitable Cycles", profitable_cycles)
                        
                        with col3:
                            losing_cycles = len(cycles_df[cycles_df['Realized P&L ($)'] < 0])
                            st.metric("Losing Cycles", losing_cycles)
                        
                        with col4:
                            if total_cycles > 0:
                                cycle_win_rate = (profitable_cycles / total_cycles * 100)
                                st.metric("Cycle Win Rate", f"{cycle_win_rate:.1f}%")
                        
                        with col5:
                            avg_cycle_pnl = cycles_df['Realized P&L ($)'].mean()
                            st.metric("Avg P&L per Cycle", f"${avg_cycle_pnl:.2f}")
                        
                        # Additional cycle metrics
                        col6, col7, col8, col9 = st.columns(4)
                        
                        with col6:
                            total_investment = cycles_df['Investment ($)'].sum()
                            st.metric("Total Investment", f"${total_investment:,.2f}")
                        
                        with col7:
                            total_pnl = cycles_df['Realized P&L ($)'].sum()
                            st.metric("Total P&L", f"${total_pnl:.2f}")
                        
                        with col8:
                            avg_duration = cycles_df['Duration'].apply(lambda x: float(x.replace('h', '')) if 'h' in str(x) else 0).mean()
                            st.metric("Avg Duration", f"{avg_duration:.1f}h")
                        
                        with col9:
                            overall_roi = (total_pnl / total_investment * 100) if total_investment > 0 else 0
                            st.metric("Overall ROI", f"{overall_roi:.2f}%")
                        
                        # Display the cycles table
                        st.markdown("**🔄 All Cycles:**")
                        st.dataframe(
                            cycles_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'Investment ($)': st.column_config.NumberColumn(
                                    'Investment ($)',
                                    format="$%.2f"
                                ),
                                'Max Investment ($)': st.column_config.NumberColumn(
                                    'Max Investment ($)',
                                    format="$%.2f"
                                ),
                                'Realized P&L ($)': st.column_config.NumberColumn(
                                    'Realized P&L ($)',
                                    format="$%.2f"
                                ),
                                'ROI (%)': st.column_config.NumberColumn(
                                    'ROI (%)',
                                    format="%.2f%%"
                                ),
                                'Entry Price': st.column_config.NumberColumn(
                                    'Entry Price',
                                    format="$%.4f"
                                ),
                                'Exit Price': st.column_config.NumberColumn(
                                    'Exit Price',
                                    format="$%.4f"
                                ),
                                'Position Size': st.column_config.NumberColumn(
                                    'Position Size',
                                    format="%.4f"
                                )
                            }
                        )
                        
                        # Download cycles data
                        if st.button("📥 Download Cycles CSV", key="download_cycles_csv"):
                            cycles_csv = cycles_df.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Cycles Data",
                                data=cycles_csv,
                                file_name=f"cycles_history_{results['symbol']}_{results['start_date']}_{results['end_date']}.csv",
                                mime="text/csv",
                                key="download_cycles_button"
                            )
                        
                        # Cycle Performance Analysis
                        st.markdown("**📊 Cycle Performance Analysis:**")
                        
                        # Performance distribution chart
                        col_chart1, col_chart2 = st.columns(2)
                        
                        with col_chart1:
                            # P&L Distribution
                            import plotly.express as px
                            fig_pnl = px.histogram(
                                cycles_df,
                                x='Realized P&L ($)',
                                nbins=15,
                                title="Cycle P&L Distribution",
                                labels={'x': 'P&L ($)', 'y': 'Number of Cycles'}
                            )
                            fig_pnl.update_layout(showlegend=False, height=400)
                            st.plotly_chart(fig_pnl, use_container_width=True)
                        
                        with col_chart2:
                            # ROI Distribution
                            fig_roi = px.histogram(
                                cycles_df,
                                x='ROI (%)',
                                nbins=15,
                                title="Cycle ROI Distribution",
                                labels={'x': 'ROI (%)', 'y': 'Number of Cycles'}
                            )
                            fig_roi.update_layout(showlegend=False, height=400)
                            st.plotly_chart(fig_roi, use_container_width=True)
                        
                        # Duration vs P&L scatter plot
                        if 'Duration' in cycles_df.columns:
                            duration_numeric = cycles_df['Duration'].apply(lambda x: float(x.replace('h', '')) if 'h' in str(x) else 0)
                            fig_scatter = px.scatter(
                                x=duration_numeric,
                                y=cycles_df['Realized P&L ($)'],
                                title="Cycle Duration vs P&L",
                                labels={'x': 'Duration (hours)', 'y': 'P&L ($)'},
                                color=cycles_df['Realized P&L ($)'],
                                color_continuous_scale='RdYlGn'
                            )
                            fig_scatter.update_layout(height=400)
                            st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    else:
                        st.info("📊 No cycles data available for display.")
                else:
                    st.info("📊 No trades were executed during this backtest - no cycles to analyze.")
                    
            except Exception as e:
                st.error(f"Error displaying cycles data: {str(e)}")
                st.info("💡 Cycles table unavailable - this may occur with certain strategy configurations.")
             
             # Save Backtest Section - Always visible when results are available
            st.markdown("---")
            st.markdown("**💾 Save Backtest for Comparison**")
            
            # Initialize save expander state if not exists
            if 'save_expander_open' not in st.session_state:
                st.session_state.save_expander_open = True
            
            with st.expander("💾 Save This Backtest", expanded=st.session_state.save_expander_open):
                col_save1, col_save2 = st.columns([3, 1])
                
                with col_save1:
                    # Generate default name based on current backtest
                    symbol = results.get('symbol', 'UNKNOWN')
                    start_date = results.get('start_date', 'UNKNOWN')
                    end_date = results.get('end_date', 'UNKNOWN')
                    
                    # Format dates if they are datetime objects
                    if hasattr(start_date, 'strftime'):
                        start_str = start_date.strftime('%Y%m%d')
                    else:
                        start_str = str(start_date).replace('-', '')
                    
                    if hasattr(end_date, 'strftime'):
                        end_str = end_date.strftime('%Y%m%d')
                    else:
                        end_str = str(end_date).replace('-', '')
                    
                    default_name = f"{symbol}_{start_str}_{end_str}"
                    
                    # Initialize backtest name in session state if not exists
                    if 'current_backtest_name' not in st.session_state:
                        st.session_state.current_backtest_name = default_name
                    
                    backtest_name = st.text_input(
                        "Backtest Name:",
                        value=st.session_state.current_backtest_name,
                        help="Enter a unique name for this backtest to save it for comparison",
                        key="save_backtest_name_input"
                    )
                    
                    # Update session state when name changes
                    if backtest_name != st.session_state.current_backtest_name:
                        st.session_state.current_backtest_name = backtest_name
                
                with col_save2:
                    if st.button("💾 Save Backtest", use_container_width=True, key="save_backtest_btn"):
                        if backtest_name.strip():
                            if backtest_name in st.session_state.stored_backtests:
                                st.warning(f"⚠️ Backtest '{backtest_name}' already exists. Choose a different name.")
                            else:
                                # Store the backtest
                                st.session_state.stored_backtests[backtest_name] = st.session_state.backtest_results.copy()
                                st.success(f"✅ Backtest '{backtest_name}' saved successfully!")
                                st.info(f"📊 Total saved backtests: {len(st.session_state.stored_backtests)}")
                                # Reset the name for next backtest
                                st.session_state.current_backtest_name = default_name
                        else:
                            st.error("❌ Please enter a valid backtest name.")
            
            # Add Cycle Analysis Section
            render_cycle_analysis_section(results)
    
    # Add Backtest Comparison Section
    render_backtest_comparison_section()

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

def render_backtest_comparison_section():
    """Render backtest comparison section"""
    st.markdown("---")
    render_title_with_tooltip(
        "⚖️ Backtest Comparison", 
        "Compare multiple saved backtests side-by-side to analyze performance differences and identify optimal strategies",
        "header"
    )
    
    # Always show import/export functionality
    with st.expander("📁 Import/Export & Manage Backtests", expanded=True):
        # Import section
        st.markdown("**📥 Import Backtest Results**")
        col_import1, col_import2 = st.columns([3, 1])
        
        with col_import1:
            uploaded_file = st.file_uploader(
                "Upload backtest JSON file:",
                type=['json'],
                help="Upload a previously exported backtest result file",
                key="backtest_upload"
            )
        
        with col_import2:
            if uploaded_file is not None:
                if st.button("📥 Import", use_container_width=True, key="import_backtest_btn"):
                    try:
                        # Read and parse the uploaded file
                        file_content = uploaded_file.read()
                        backtest_data = json.loads(file_content.decode('utf-8'))
                        
                        # Validate the data structure
                        required_keys = ['symbol', 'strategies', 'timeframe', 'start_date', 'end_date', 'metrics', 'timestamp']
                        if all(key in backtest_data for key in required_keys):
                            # Generate a unique name if needed
                            base_name = uploaded_file.name.replace('.json', '')
                            import_name = base_name
                            counter = 1
                            while import_name in st.session_state.stored_backtests:
                                import_name = f"{base_name}_{counter}"
                                counter += 1
                            
                            # Convert date strings back to datetime objects if needed
                            if isinstance(backtest_data['start_date'], str):
                                backtest_data['start_date'] = datetime.fromisoformat(backtest_data['start_date'])
                            if isinstance(backtest_data['end_date'], str):
                                backtest_data['end_date'] = datetime.fromisoformat(backtest_data['end_date'])
                            if isinstance(backtest_data['timestamp'], str):
                                backtest_data['timestamp'] = datetime.fromisoformat(backtest_data['timestamp'])
                            
                            # Store the imported backtest
                            st.session_state.stored_backtests[import_name] = backtest_data
                            st.success(f"✅ Successfully imported backtest as '{import_name}'!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid backtest file format. Missing required fields.")
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON file format.")
                    except Exception as e:
                        st.error(f"❌ Error importing backtest: {str(e)}")
        
        st.markdown("---")
        
        # Export section
        if st.session_state.stored_backtests:
            st.markdown("**📤 Export Backtest Results**")
            col_export1, col_export2 = st.columns([3, 1])
            
            with col_export1:
                backtest_to_export = st.selectbox(
                    "Select backtest to export:",
                    list(st.session_state.stored_backtests.keys()),
                    key="export_backtest_select"
                )
            
            with col_export2:
                if st.button("📤 Export", use_container_width=True, key="export_backtest_btn"):
                    try:
                        # Get the backtest data
                        export_data = st.session_state.stored_backtests[backtest_to_export].copy()
                        
                        # Convert datetime objects to strings for JSON serialization
                        if hasattr(export_data['start_date'], 'isoformat'):
                            export_data['start_date'] = export_data['start_date'].isoformat()
                        if hasattr(export_data['end_date'], 'isoformat'):
                            export_data['end_date'] = export_data['end_date'].isoformat()
                        if hasattr(export_data['timestamp'], 'isoformat'):
                            export_data['timestamp'] = export_data['timestamp'].isoformat()
                        
                        # Convert strategies enum to string if needed
                        if 'strategies' in export_data:
                            export_data['strategies'] = [str(s) for s in export_data['strategies']]
                        
                        # Create JSON string
                        json_str = json.dumps(export_data, indent=2, default=str)
                        
                        # Create download button
                        st.download_button(
                            label=f"💾 Download {backtest_to_export}.json",
                            data=json_str,
                            file_name=f"{backtest_to_export}.json",
                            mime="application/json",
                            key="download_backtest_json"
                        )
                        
                        st.success(f"✅ Export ready for '{backtest_to_export}'!")
                    except Exception as e:
                        st.error(f"❌ Error exporting backtest: {str(e)}")
            
            st.markdown("---")
        
        # Management section
    with st.expander("🗂️ Manage Saved Backtests", expanded=False):
        if st.session_state.stored_backtests:
            st.markdown("**Saved Backtests:**")
            
            # Display saved backtests in a table
            backtest_data = []
            for name, data in st.session_state.stored_backtests.items():
                backtest_data.append({
                    'Name': name,
                    'Symbol': data['symbol'],
                    'Strategies': ', '.join([s.value for s in data['strategies']]),
                    'Timeframe': data['timeframe'],
                    'Period': f"{data['start_date'].strftime('%Y-%m-%d')} to {data['end_date'].strftime('%Y-%m-%d')}",
                    'Return': f"{data['metrics']['Return [%]']:.2f}%",
                    'Saved': data['timestamp'].strftime('%Y-%m-%d %H:%M')
                })
            
            backtest_df = pd.DataFrame(backtest_data)
            st.dataframe(backtest_df, use_container_width=True)
            
            # Delete backtest option
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                backtest_to_delete = st.selectbox(
                    "Select backtest to delete:",
                    list(st.session_state.stored_backtests.keys()),
                    key="delete_backtest_select"
                )
            with col_del2:
                if st.button("🗑️ Delete", key="delete_backtest_btn"):
                    if backtest_to_delete in st.session_state.stored_backtests:
                        del st.session_state.stored_backtests[backtest_to_delete]
                        st.success(f"✅ Deleted backtest '{backtest_to_delete}'")
                        st.rerun()
            
            # Clear all backtests
            if st.button("🗑️ Clear All Backtests", type="secondary"):
                st.session_state.stored_backtests = {}
                st.success("✅ All backtests cleared!")
                st.rerun()
    
    # Display current status
    st.markdown(f"📊 **Available Backtests:** {len(st.session_state.stored_backtests)}")
    
    # Show helpful message if no backtests available
    if not st.session_state.stored_backtests:
        st.info("💡 No saved backtests available for comparison. You can:")
        st.markdown("""
        **Options to get started:**
        1. **Import existing backtests** using the Import section above
        2. **Run new backtests** using the configuration in the Backtesting section
        3. **Save backtests** with descriptive names for comparison
        """)
        return
    
    # Comparison section
    if len(st.session_state.stored_backtests) < 2:
        st.warning("⚠️ Need at least 2 saved backtests for comparison. Import more backtests or run additional backtests.")
        return
    
    st.markdown("### 📊 Select Backtests to Compare")
    
    # Backtest selection
    col_select1, col_select2 = st.columns(2)
    
    backtest_names = list(st.session_state.stored_backtests.keys())
    
    with col_select1:
        backtest1_name = st.selectbox(
            "First Backtest:",
            backtest_names,
            key="comparison_backtest1"
        )
    
    with col_select2:
        backtest2_name = st.selectbox(
            "Second Backtest:",
            backtest_names,
            index=1 if len(backtest_names) > 1 else 0,
            key="comparison_backtest2"
        )
    
    if backtest1_name == backtest2_name:
        st.warning("⚠️ Please select two different backtests for comparison.")
        return
    
    # Get selected backtests
    backtest1 = st.session_state.stored_backtests[backtest1_name]
    backtest2 = st.session_state.stored_backtests[backtest2_name]
    
    # Comparison tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Detailed Metrics", "📋 Side-by-Side", "📊 Visual Comparison"])
    
    with tab1:
        render_backtest_overview_comparison(backtest1, backtest2, backtest1_name, backtest2_name)
    
    with tab2:
        render_detailed_metrics_comparison(backtest1, backtest2, backtest1_name, backtest2_name)
    
    with tab3:
        render_side_by_side_comparison(backtest1, backtest2, backtest1_name, backtest2_name)
    
    with tab4:
        render_visual_comparison(backtest1, backtest2, backtest1_name, backtest2_name)

def render_backtest_overview_comparison(backtest1, backtest2, name1, name2):
    """Render overview comparison of two backtests"""
    st.markdown("### 🏆 Performance Winner Analysis")
    
    # Key metrics comparison
    metrics1 = backtest1['metrics']
    metrics2 = backtest2['metrics']
    
    # Determine winners
    winners = {}
    winners['return'] = name1 if metrics1['Return [%]'] > metrics2['Return [%]'] else name2
    winners['sharpe'] = name1 if (metrics1.get('Sharpe Ratio', 0) or 0) > (metrics2.get('Sharpe Ratio', 0) or 0) else name2
    winners['drawdown'] = name1 if metrics1['Max. Drawdown [%]'] < metrics2['Max. Drawdown [%]'] else name2  # Less drawdown is better
    winners['trades'] = name1 if (metrics1.get('# Trades', 0) or 0) > (metrics2.get('# Trades', 0) or 0) else name2
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        return_diff = metrics1['Return [%]'] - metrics2['Return [%]']
        st.metric(
            "Total Return Winner",
            winners['return'],
            delta=f"{abs(return_diff):.2f}% difference"
        )
    
    with col2:
        sharpe1 = metrics1.get('Sharpe Ratio', 0) or 0
        sharpe2 = metrics2.get('Sharpe Ratio', 0) or 0
        sharpe_diff = sharpe1 - sharpe2
        st.metric(
            "Sharpe Ratio Winner",
            winners['sharpe'],
            delta=f"{abs(sharpe_diff):.3f} difference"
        )
    
    with col3:
        dd_diff = metrics2['Max. Drawdown [%]'] - metrics1['Max. Drawdown [%]']  # Reversed for better display
        st.metric(
            "Lower Drawdown",
            winners['drawdown'],
            delta=f"{abs(dd_diff):.2f}% less drawdown"
        )
    
    with col4:
        trades1 = metrics1.get('# Trades', 0) or 0
        trades2 = metrics2.get('# Trades', 0) or 0
        trades_diff = trades1 - trades2
        st.metric(
            "More Active",
            winners['trades'],
            delta=f"{abs(trades_diff):.0f} more trades"
        )
    
    # Overall winner
    st.markdown("### 🎯 Overall Assessment")
    
    score1 = 0
    score2 = 0
    
    if winners['return'] == name1: score1 += 1
    else: score2 += 1
    
    if winners['sharpe'] == name1: score1 += 1
    else: score2 += 1
    
    if winners['drawdown'] == name1: score1 += 1
    else: score2 += 1
    
    if score1 > score2:
        st.success(f"🏆 **Overall Winner: {name1}** (Score: {score1}/{score1+score2})")
    elif score2 > score1:
        st.success(f"🏆 **Overall Winner: {name2}** (Score: {score2}/{score1+score2})")
    else:
        st.info(f"🤝 **Tie** (Score: {score1}-{score2})")
    
    # Key insights
    st.markdown("### 💡 Key Insights")
    
    insights = []
    
    if abs(return_diff) > 5:
        insights.append(f"📈 Significant return difference: {abs(return_diff):.1f}%")
    
    if abs(sharpe_diff) > 0.5:
        insights.append(f"📊 Notable risk-adjusted performance difference (Sharpe: {abs(sharpe_diff):.2f})")
    
    if abs(dd_diff) > 3:
        insights.append(f"⚠️ Significant drawdown difference: {abs(dd_diff):.1f}%")
    
    period1 = (backtest1['end_date'] - backtest1['start_date']).days
    period2 = (backtest2['end_date'] - backtest2['start_date']).days
    if abs(period1 - period2) > 30:
        insights.append(f"📅 Different testing periods: {abs(period1 - period2)} days difference")
    
    if backtest1['symbol'] != backtest2['symbol']:
        insights.append(f"🎯 Different symbols: {backtest1['symbol']} vs {backtest2['symbol']}")
    
    if insights:
        for insight in insights:
            st.info(insight)
    else:
        st.success("✅ Both backtests show similar performance characteristics")

def render_detailed_metrics_comparison(backtest1, backtest2, name1, name2):
    """Render detailed metrics comparison"""
    st.markdown("### 📊 Comprehensive Metrics Comparison")
    
    metrics1 = backtest1['metrics']
    metrics2 = backtest2['metrics']
    
    # Create comparison dataframe
    comparison_data = {
        'Metric': [
            'Total Return (%)', 'Annual Return (%)', 'Buy & Hold Return (%)',
            'Max Drawdown (%)', 'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio',
            'Win Rate (%)', 'Profit Factor', 'Total Trades', 'Best Trade (%)',
            'Worst Trade (%)', 'Average Trade (%)', 'Exposure Time (%)',
            'Final Equity ($)', 'Peak Equity ($)'
        ],
        name1: [
            f"{metrics1.get('Return [%]', 0):.2f}",
            f"{metrics1.get('Return (Ann.) [%]', 0) or 0:.2f}",
            f"{metrics1.get('Buy & Hold Return [%]', 0):.2f}",
            f"{metrics1.get('Max. Drawdown [%]', 0):.2f}",
            f"{metrics1.get('Sharpe Ratio', 0) or 0:.3f}",
            f"{metrics1.get('Sortino Ratio', 0) or 0:.3f}",
            f"{metrics1.get('Calmar Ratio', 0) or 0:.3f}",
            f"{metrics1.get('Win Rate [%]', 0) or 0:.1f}",
            f"{metrics1.get('Profit Factor', 0) or 0:.2f}",
            f"{int(metrics1.get('# Trades', 0) or 0)}",
            f"{metrics1.get('Best Trade [%]', 0) or 0:.2f}",
            f"{metrics1.get('Worst Trade [%]', 0) or 0:.2f}",
            f"{metrics1.get('Avg. Trade [%]', 0) or 0:.2f}",
            f"{metrics1.get('Exposure Time [%]', 0):.1f}",
            f"{metrics1.get('Equity Final [$]', 0):,.2f}",
            f"{metrics1.get('Equity Peak [$]', 0):,.2f}"
        ],
        name2: [
            f"{metrics2.get('Return [%]', 0):.2f}",
            f"{metrics2.get('Return (Ann.) [%]', 0) or 0:.2f}",
            f"{metrics2.get('Buy & Hold Return [%]', 0):.2f}",
            f"{metrics2.get('Max. Drawdown [%]', 0):.2f}",
            f"{metrics2.get('Sharpe Ratio', 0) or 0:.3f}",
            f"{metrics2.get('Sortino Ratio', 0) or 0:.3f}",
            f"{metrics2.get('Calmar Ratio', 0) or 0:.3f}",
            f"{metrics2.get('Win Rate [%]', 0) or 0:.1f}",
            f"{metrics2.get('Profit Factor', 0) or 0:.2f}",
            f"{int(metrics2.get('# Trades', 0) or 0)}",
            f"{metrics2.get('Best Trade [%]', 0) or 0:.2f}",
            f"{metrics2.get('Worst Trade [%]', 0) or 0:.2f}",
            f"{metrics2.get('Avg. Trade [%]', 0) or 0:.2f}",
            f"{metrics2.get('Exposure Time [%]', 0):.1f}",
            f"{metrics2.get('Equity Final [$]', 0):,.2f}",
            f"{metrics2.get('Equity Peak [$]', 0):,.2f}"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Download comparison
    if st.button("📥 Download Comparison CSV"):
        csv_data = comparison_df.to_csv(index=False)
        st.download_button(
            label="Download Comparison Data",
            data=csv_data,
            file_name=f"backtest_comparison_{name1}_vs_{name2}.csv",
            mime="text/csv"
        )

def render_side_by_side_comparison(backtest1, backtest2, name1, name2):
    """Render side-by-side configuration and setup comparison"""
    st.markdown("### ⚙️ Configuration Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### 📊 {name1}")
        st.markdown(f"**Symbol:** {backtest1['symbol']}")
        st.markdown(f"**Strategies:** {', '.join([s.value for s in backtest1['strategies']])}")
        st.markdown(f"**Timeframe:** {backtest1['timeframe']}")
        st.markdown(f"**Period:** {backtest1['start_date'].strftime('%Y-%m-%d')} to {backtest1['end_date'].strftime('%Y-%m-%d')}")
        st.markdown(f"**Duration:** {(backtest1['end_date'] - backtest1['start_date']).days} days")
        st.markdown(f"**Saved:** {backtest1['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        
        # Key metrics
        st.markdown("**Key Results:**")
        metrics1 = backtest1['metrics']
        st.success(f"Return: {metrics1['Return [%]']:.2f}%")
        st.info(f"Sharpe: {metrics1.get('Sharpe Ratio', 0) or 0:.3f}")
        st.warning(f"Max DD: {metrics1['Max. Drawdown [%]']:.2f}%")
    
    with col2:
        st.markdown(f"#### 📊 {name2}")
        st.markdown(f"**Symbol:** {backtest2['symbol']}")
        st.markdown(f"**Strategies:** {', '.join([s.value for s in backtest2['strategies']])}")
        st.markdown(f"**Timeframe:** {backtest2['timeframe']}")
        st.markdown(f"**Period:** {backtest2['start_date'].strftime('%Y-%m-%d')} to {backtest2['end_date'].strftime('%Y-%m-%d')}")
        st.markdown(f"**Duration:** {(backtest2['end_date'] - backtest2['start_date']).days} days")
        st.markdown(f"**Saved:** {backtest2['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        
        # Key metrics
        st.markdown("**Key Results:**")
        metrics2 = backtest2['metrics']
        st.success(f"Return: {metrics2['Return [%]']:.2f}%")
        st.info(f"Sharpe: {metrics2.get('Sharpe Ratio', 0) or 0:.3f}")
        st.warning(f"Max DD: {metrics2['Max. Drawdown [%]']:.2f}%")
    
    # Differences analysis
    st.markdown("### 🔍 Key Differences")
    
    differences = []
    
    if backtest1['symbol'] != backtest2['symbol']:
        differences.append(f"📈 **Symbol:** {backtest1['symbol']} vs {backtest2['symbol']}")
    
    if set([s.value for s in backtest1['strategies']]) != set([s.value for s in backtest2['strategies']]):
        strategies1 = set([s.value for s in backtest1['strategies']])
        strategies2 = set([s.value for s in backtest2['strategies']])
        differences.append(f"🎯 **Strategies:** {strategies1} vs {strategies2}")
    
    if backtest1['timeframe'] != backtest2['timeframe']:
        differences.append(f"⏰ **Timeframe:** {backtest1['timeframe']} vs {backtest2['timeframe']}")
    
    period_diff = abs((backtest1['end_date'] - backtest1['start_date']).days - (backtest2['end_date'] - backtest2['start_date']).days)
    if period_diff > 7:
        differences.append(f"📅 **Period Length:** {period_diff} days difference")
    
    if differences:
        for diff in differences:
            st.info(diff)
    else:
        st.success("✅ Both backtests use identical configurations")

def render_visual_comparison(backtest1, backtest2, name1, name2):
    """Render visual comparison charts"""
    st.markdown("### 📊 Visual Performance Comparison")
    
    metrics1 = backtest1['metrics']
    metrics2 = backtest2['metrics']
    
    # Create comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Return comparison bar chart
        fig_returns = go.Figure(data=[
            go.Bar(name=name1, x=['Total Return', 'Annual Return'], 
                   y=[metrics1['Return [%]'], metrics1.get('Return (Ann.) [%]', 0) or 0]),
            go.Bar(name=name2, x=['Total Return', 'Annual Return'], 
                   y=[metrics2['Return [%]'], metrics2.get('Return (Ann.) [%]', 0) or 0])
        ])
        fig_returns.update_layout(title="Return Comparison (%)", barmode='group')
        st.plotly_chart(fig_returns, use_container_width=True)
    
    with col2:
        # Risk metrics comparison
        fig_risk = go.Figure(data=[
            go.Bar(name=name1, x=['Max Drawdown', 'Sharpe Ratio'], 
                   y=[metrics1['Max. Drawdown [%]'], (metrics1.get('Sharpe Ratio', 0) or 0) * 10]),  # Scale Sharpe for visibility
            go.Bar(name=name2, x=['Max Drawdown', 'Sharpe Ratio'], 
                   y=[metrics2['Max. Drawdown [%]'], (metrics2.get('Sharpe Ratio', 0) or 0) * 10])
        ])
        fig_risk.update_layout(title="Risk Metrics (Sharpe x10 for scale)", barmode='group')
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Radar chart comparison
    st.markdown("### 🎯 Multi-Metric Radar Comparison")
    
    # Normalize metrics for radar chart (0-100 scale)
    def normalize_metric(value, min_val, max_val):
        if max_val == min_val:
            return 50
        return ((value - min_val) / (max_val - min_val)) * 100
    
    # Get metrics for radar
    return1 = metrics1['Return [%]']
    return2 = metrics2['Return [%]']
    sharpe1 = metrics1.get('Sharpe Ratio', 0) or 0
    sharpe2 = metrics2.get('Sharpe Ratio', 0) or 0
    dd1 = 100 - metrics1['Max. Drawdown [%]']  # Invert so higher is better
    dd2 = 100 - metrics2['Max. Drawdown [%]']
    trades1 = metrics1.get('# Trades', 0) or 0
    trades2 = metrics2.get('# Trades', 0) or 0
    winrate1 = metrics1.get('Win Rate [%]', 0) or 0
    winrate2 = metrics2.get('Win Rate [%]', 0) or 0
    
    # Normalize
    min_return, max_return = min(return1, return2), max(return1, return2)
    min_sharpe, max_sharpe = min(sharpe1, sharpe2), max(sharpe1, sharpe2)
    min_dd, max_dd = min(dd1, dd2), max(dd1, dd2)
    min_trades, max_trades = min(trades1, trades2), max(trades1, trades2)
    min_winrate, max_winrate = min(winrate1, winrate2), max(winrate1, winrate2)
    
    categories = ['Return', 'Sharpe Ratio', 'Low Drawdown', 'Trade Count', 'Win Rate']
    
    values1 = [
        normalize_metric(return1, min_return, max_return),
        normalize_metric(sharpe1, min_sharpe, max_sharpe),
        normalize_metric(dd1, min_dd, max_dd),
        normalize_metric(trades1, min_trades, max_trades),
        normalize_metric(winrate1, min_winrate, max_winrate)
    ]
    
    values2 = [
        normalize_metric(return2, min_return, max_return),
        normalize_metric(sharpe2, min_sharpe, max_sharpe),
        normalize_metric(dd2, min_dd, max_dd),
        normalize_metric(trades2, min_trades, max_trades),
        normalize_metric(winrate2, min_winrate, max_winrate)
    ]
    
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=values1 + [values1[0]],  # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        name=name1,
        line_color='blue'
    ))
    
    fig_radar.add_trace(go.Scatterpolar(
        r=values2 + [values2[0]],  # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        name=name2,
        line_color='red'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Performance Radar Comparison (Normalized 0-100)",
        showlegend=True
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Summary insights
    st.markdown("### 💡 Visual Analysis Insights")
    
    if abs(return1 - return2) > 5:
        better_return = name1 if return1 > return2 else name2
        st.info(f"📈 {better_return} shows significantly better returns")
    
    if abs(sharpe1 - sharpe2) > 0.3:
        better_sharpe = name1 if sharpe1 > sharpe2 else name2
        st.info(f"📊 {better_sharpe} demonstrates superior risk-adjusted returns")
    
    if abs(dd1 - dd2) > 5:
        better_dd = name1 if dd1 > dd2 else name2
        st.info(f"🛡️ {better_dd} shows better drawdown control")

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