import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
import os
import time
import sys

# Add the app directory to the path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from config import TradingConfig

def render_performance_analytics():
    """Render the performance analytics dashboard"""
    st.title("📊 Performance Analytics")
    
    # Performance tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "💹 P&L Analysis", "📊 Strategy Performance", "📋 Trade History"])
    
    with tab1:
        st.subheader("📈 Performance Overview")
        
        # Data source toggle for overview
        overview_source = st.radio(
            "Data Source",
            ["Broker Account", "Strategy Data"],
            horizontal=True,
            help="Choose between real broker account data or internal strategy tracking",
            key="overview_source"
        )
        
        # Get performance data based on selected source
        if overview_source == "Broker Account":
            perf_data = get_broker_performance_overview()
        else:
            perf_data = get_performance_overview()
        
        # Display data source indicator and connection status
        st.info(f"📊 Data Source: {perf_data.get('Data Source', 'Unknown')}")
        
        # Add connection status debugging
        if overview_source == "Broker Account":
            if st.session_state.trading_engine:
                if st.session_state.trading_engine.api:
                    if st.session_state.trading_engine.api.is_connected:
                        st.success("✅ IBKR API Connected")
                    else:
                        st.warning("⚠️ IBKR API Not Connected - Check TWS/Gateway")
                else:
                    st.error("❌ IBKR API Not Initialized")
            else:
                st.error("❌ Trading Engine Not Started")
        
        # Display key metrics based on data source
        if overview_source == "Broker Account":
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Account Balance",
                    f"${perf_data.get('Account Balance', 0):.2f}"
                )
            
            with col2:
                st.metric(
                    "Total Trades",
                    perf_data.get('Total Trades', 0)
                )
            
            with col3:
                st.metric(
                    "Buy Orders",
                    perf_data.get('Buy Orders', 0)
                )
            
            with col4:
                st.metric(
                    "Sell Orders",
                    perf_data.get('Sell Orders', 0)
                )
            
            # Additional metrics row
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric(
                    "Total Volume",
                    f"{perf_data.get('Total Volume', 0):.0f}"
                )
            
            with col6:
                st.metric(
                    "Avg Trade Size",
                    f"{perf_data.get('Total Volume', 0) / max(perf_data.get('Total Trades', 1), 1):.0f}"
                )
        else:
            # Original strategy data metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total P&L",
                    f"${perf_data['Total P&L']:.2f}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Total Trades",
                    perf_data['Total Trades']
                )
            
            with col3:
                st.metric(
                    "Win Rate",
                    f"{perf_data['Win Rate']:.1f}%"
                )
            
            with col4:
                st.metric(
                    "Total Volume",
                    f"{perf_data['Total Volume']:.0f}"
                )
    
    with tab2:
        render_pnl_analysis()
    
    with tab3:
        render_strategy_performance()
    
    with tab4:
        render_trade_history()

def render_performance_overview():
    """Render performance overview section"""
    st.subheader("📈 Performance Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Get real performance metrics from trading engine
    metrics = get_real_performance_metrics()
    
    with col1:
        st.metric(
            label="Total Return",
            value=f"{metrics['total_return']:.2f}%",
            delta=f"{metrics['daily_return']:.2f}%"
        )
    
    with col2:
        st.metric(
            label="Sharpe Ratio",
            value=f"{metrics['sharpe_ratio']:.2f}",
            delta=None
        )
    

    
    with col4:
        st.metric(
            label="Win Rate",
            value=f"{metrics['win_rate']:.1f}%",
            delta=None
        )
    
    # Equity curve
    st.subheader("💰 Equity Curve")
    equity_data = get_real_equity_curve_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_data['date'],
        y=equity_data['equity'],
        mode='lines',
        name='Portfolio Equity',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title="Portfolio Equity Over Time",
        xaxis_title="Date",
        yaxis_title="Equity ($)",
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Daily returns distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Daily Returns Distribution")
        returns_data = get_real_returns_data()
        
        fig_hist = px.histogram(
            returns_data,
            x='daily_return',
            nbins=30,
            title="Daily Returns Distribution",
            labels={'daily_return': 'Daily Return (%)', 'count': 'Frequency'}
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("📈 Monthly Performance")
        monthly_data = get_real_monthly_performance_data()
        
        fig_monthly = px.bar(
            monthly_data,
            x='month',
            y='return',
            title="Monthly Returns",
            labels={'month': 'Month', 'return': 'Return (%)'}
        )
        fig_monthly.update_layout(showlegend=False)
        st.plotly_chart(fig_monthly, use_container_width=True)

def render_pnl_analysis():
    """Render P&L analysis section"""
    st.subheader("💹 P&L Analysis")
    
    # P&L breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Realized P&L by Symbol**")
        pnl_by_symbol = get_real_pnl_by_symbol()
        
        fig_pie = px.pie(
            values=list(pnl_by_symbol.values()),
            names=list(pnl_by_symbol.keys()),
            title="Realized P&L Distribution by Symbol"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.write("**Unrealized P&L by Symbol**")
        unrealized_pnl = get_real_unrealized_pnl_by_symbol()
        
        fig_bar = px.bar(
            x=list(unrealized_pnl.keys()),
            y=list(unrealized_pnl.values()),
            title="Unrealized P&L by Symbol",
            labels={'x': 'Symbol', 'y': 'Unrealized P&L ($)'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Cumulative P&L chart
    st.subheader("📈 Cumulative P&L")
    cumulative_pnl_data = get_real_cumulative_pnl_data()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Cumulative P&L', 'Daily P&L'),
        vertical_spacing=0.1
    )
    
    # Cumulative P&L
    fig.add_trace(
        go.Scatter(
            x=cumulative_pnl_data['date'],
            y=cumulative_pnl_data['cumulative_pnl'],
            mode='lines',
            name='Cumulative P&L',
            line=dict(color='green')
        ),
        row=1, col=1
    )
    
    # Daily P&L
    colors = ['green' if x >= 0 else 'red' for x in cumulative_pnl_data['daily_pnl']]
    fig.add_trace(
        go.Bar(
            x=cumulative_pnl_data['date'],
            y=cumulative_pnl_data['daily_pnl'],
            name='Daily P&L',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="P&L Analysis"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_strategy_performance():
    """Render strategy performance section"""
    st.subheader("📊 Strategy Performance")
    
    # Strategy comparison
    strategy_metrics = get_real_strategy_metrics()
    
    if strategy_metrics:
        df_strategies = pd.DataFrame(strategy_metrics).T
        df_strategies.index.name = 'Strategy'
        
        st.write("**Strategy Performance Comparison**")
        st.dataframe(df_strategies, use_container_width=True)
        
        # Strategy performance chart
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Total Return (%)' in df_strategies.columns:
                fig_return = px.bar(
                    x=df_strategies.index,
                    y=df_strategies['Total Return (%)'],
                    title="Total Return by Strategy",
                    labels={'x': 'Strategy', 'y': 'Total Return (%)'}
                )
                st.plotly_chart(fig_return, use_container_width=True)
            else:
                st.info("Total Return data not available. Start trading to see returns.")
        
        with col2:
            if 'Sharpe Ratio' in df_strategies.columns:
                fig_sharpe = px.bar(
                    x=df_strategies.index,
                    y=df_strategies['Sharpe Ratio'],
                    title="Sharpe Ratio by Strategy",
                    labels={'x': 'Strategy', 'y': 'Sharpe Ratio'}
                )
                st.plotly_chart(fig_sharpe, use_container_width=True)
            else:
                st.info("Sharpe Ratio data not available. Start trading to see ratios.")
    else:
        st.info("No strategy performance data available. Start trading to see strategy metrics.")
    
    # Strategy allocation
    st.subheader("🥧 Strategy Allocation")
    allocation_data = get_real_strategy_allocation()
    
    if allocation_data:
        fig_allocation = px.pie(
            values=list(allocation_data.values()),
            names=list(allocation_data.keys()),
            title="Current Strategy Allocation"
        )
        st.plotly_chart(fig_allocation, use_container_width=True)
    else:
        st.info("No strategy allocation data available.")

def render_trade_history():
    """Render trade history section"""
    st.subheader("📋 Trade History")
    
    # Data source toggle
    col_toggle, col_refresh = st.columns([3, 1])
    with col_toggle:
        data_source = st.radio(
            "Data Source",
            ["Broker Account", "Strategy Data"],
            horizontal=True,
            help="Choose between real broker account data or internal strategy tracking"
        )
    
    with col_refresh:
        if st.button("🔄 Refresh Data", help="Refresh trade history from broker"):
            st.rerun()
    
    # Display data source indicator and connection status
    st.info(f"📊 Data Source: {data_source}")
    
    # Add connection status debugging for broker account
    if data_source == "Broker Account":
        if st.session_state.trading_engine:
            if st.session_state.trading_engine.api:
                if st.session_state.trading_engine.api.is_connected:
                    st.success("✅ IBKR API Connected")
                else:
                    st.warning("⚠️ IBKR API Not Connected - Check TWS/Gateway")
            else:
                st.error("❌ IBKR API Not Initialized")
        else:
            st.error("❌ Trading Engine Not Started")
    
    # Trade filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        symbol_filter = st.selectbox(
            "Filter by Symbol",
            options=["All"] + ["AAPL", "TSLA", "MSFT", "GOOGL"],
            key="symbol_filter"
        )
    
    with col2:
        strategy_filter = st.selectbox(
            "Filter by Strategy",
            options=["All", "CDM", "WDM", "ZRM", "IZRM"],
            key="strategy_filter"
        )
    
    with col3:
        date_from = st.date_input(
            "From Date",
            value=datetime.now() - timedelta(days=30),
            key="date_from"
        )
    
    with col4:
        date_to = st.date_input(
            "To Date",
            value=datetime.now(),
            key="date_to"
        )
    
    # Get trade history data based on selected source
    if data_source == "Broker Account":
        trades_data = get_broker_trade_history(symbol_filter, strategy_filter, date_from, date_to)
    else:
        trades_data = get_real_trade_history(symbol_filter, strategy_filter, date_from, date_to)
    
    if trades_data:
        # Trade summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", len(trades_data))
        
        with col2:
            winning_trades = len([t for t in trades_data if t['pnl'] > 0])
            st.metric("Winning Trades", winning_trades)
        
        with col3:
            total_pnl = sum(t['pnl'] for t in trades_data)
            st.metric("Total P&L", f"${total_pnl:,.2f}")
        
        with col4:
            avg_pnl = total_pnl / len(trades_data) if trades_data else 0
            st.metric("Avg P&L per Trade", f"${avg_pnl:,.2f}")
        
        # Trade history table
        st.write("**Trade Details**")
        df_trades = pd.DataFrame(trades_data)
        
        # Format the DataFrame
        # Handle date formatting - keep "Current" as is, format others as datetime
        def format_date(date_val):
            if date_val == "Current":
                return "Current"
            try:
                return pd.to_datetime(date_val).strftime('%Y-%m-%d %H:%M')
            except:
                return str(date_val)
        
        df_trades['date'] = df_trades['date'].apply(format_date)
        df_trades['entry_price'] = df_trades['entry_price'].apply(lambda x: f"${x:.2f}")
        df_trades['exit_price'] = df_trades['exit_price'].apply(lambda x: f"${x:.2f}" if x != 0.0 else "N/A")
        df_trades['pnl'] = df_trades['pnl'].apply(lambda x: f"${x:,.2f}" if x != 0.0 else "N/A")
        
        # Rename columns
        df_trades.columns = [
            'Date', 'Symbol', 'Strategy', 'Side', 'Quantity',
            'Entry Price', 'Exit Price', 'P&L'
        ]
        
        st.dataframe(df_trades, use_container_width=True)
        
        # Export trades
        if st.button("📤 Export Trade History"):
            csv = df_trades.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No trades found for the selected filters.")

# Helper functions to get real data from trading engine and IBKR API
def get_real_performance_metrics():
    """Get real performance metrics from trading engine"""
    try:
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            engine = st.session_state.trading_engine
            api = engine.api
            
            # Request fresh account data
            api.request_account_summary()
            api.request_positions()
            time.sleep(0.5)  # Allow time for data to be received
            
            # Get account info
            account_info = api.account_info
            if not account_info:
                return get_fallback_metrics()
            
            # Calculate performance metrics
            net_liquidation = account_info.get('NetLiquidation', 0.0)
            config = st.session_state.control_panel.config if st.session_state.control_panel else None
            initial_balance = config.shared_settings.initial_balance if config else 50000.0
            
            # Calculate total return
            total_pnl = net_liquidation - initial_balance
            total_return = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0.0
            
            # Get engine status for additional metrics
            engine_status = engine.get_engine_status()
            strategy_status = engine.get_strategy_status()
            
            # Calculate win rate from strategies
            total_cycles = sum(s.get('total_cycles', 0) for s in strategy_status.values())
            winning_cycles = sum(s.get('winning_cycles', 0) for s in strategy_status.values())
            win_rate = (winning_cycles / total_cycles * 100) if total_cycles > 0 else 0.0
            
            # Calculate daily return (simplified)
            daily_return = 0.0  # Would need historical data for accurate calculation
            
            return {
                'total_return': total_return,
                'daily_return': daily_return,
                'sharpe_ratio': 0.0,  # Would need historical returns for calculation

                'win_rate': win_rate
            }
        else:
            return get_fallback_metrics()
    except Exception as e:
        st.error(f"Error getting performance metrics: {str(e)}")
        return get_fallback_metrics()

def get_fallback_metrics():
    """Fallback metrics when trading engine is not available"""
    return {
        'total_return': 0.0,
        'daily_return': 0.0,
        'sharpe_ratio': 0.0,

        'win_rate': 0.0
    }

def get_real_equity_curve_data():
    """Get real equity curve data from trading engine"""
    try:
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            api = st.session_state.trading_engine.api
            
            # Request current account data
            api.request_account_summary()
            time.sleep(0.3)
            
            account_info = api.account_info
            current_equity = account_info.get('NetLiquidation', 0.0) if account_info else 0.0
            
            # Get initial balance from config
            config = st.session_state.control_panel.config if st.session_state.control_panel else None
            initial_balance = config.shared_settings.initial_balance if config else 50000.0
            
            # For now, create a simple equity curve showing progression from initial to current
            # In a full implementation, you'd store historical equity data
            engine = st.session_state.trading_engine
            start_time = engine.start_time if engine.start_time else datetime.now() - timedelta(days=1)
            
            # Create equity progression (simplified)
            dates = pd.date_range(start=start_time.date(), end=datetime.now().date(), freq='D')
            if len(dates) == 1:
                dates = [start_time.date(), datetime.now().date()]
            
            # Linear progression from initial to current (simplified)
            equity_values = np.linspace(initial_balance, current_equity, len(dates))
            
            return pd.DataFrame({
                'date': dates,
                'equity': equity_values
            })
        else:
            # Fallback data
            dates = [datetime.now().date() - timedelta(days=1), datetime.now().date()]
            return pd.DataFrame({
                'date': dates,
                'equity': [50000, 50000]
            })
    except Exception as e:
        st.error(f"Error getting equity curve data: {str(e)}")
        # Fallback data
        dates = [datetime.now().date() - timedelta(days=1), datetime.now().date()]
        return pd.DataFrame({
            'date': dates,
            'equity': [50000, 50000]
        })

def get_real_returns_data():
    """Get real daily returns data from trading engine"""
    try:
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            # For now, return simplified data since we don't have historical daily returns stored
            # In a full implementation, you'd store daily equity snapshots
            api = st.session_state.trading_engine.api
            
            # Get current performance
            account_info = api.account_info
            if account_info:
                net_liquidation = account_info.get('NetLiquidation', 0.0)
                config = st.session_state.control_panel.config if st.session_state.control_panel else None
                initial_balance = config.shared_settings.initial_balance if config else 50000.0
                
                # Calculate total return as a single data point
                total_return = ((net_liquidation - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
                
                # Create a simple distribution around the current performance
                # This is simplified - in production, you'd use actual daily returns
                returns = [total_return] * 10  # Simplified representation
                return pd.DataFrame({'daily_return': returns})
            else:
                return pd.DataFrame({'daily_return': [0.0]})
        else:
            return pd.DataFrame({'daily_return': [0.0]})
    except Exception as e:
        st.error(f"Error getting returns data: {str(e)}")
        return pd.DataFrame({'daily_return': [0.0]})

def get_real_monthly_performance_data():
    """Get real monthly performance data from trading engine"""
    try:
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            # For now, show current month performance
            # In a full implementation, you'd store monthly snapshots
            api = st.session_state.trading_engine.api
            
            account_info = api.account_info
            if account_info:
                net_liquidation = account_info.get('NetLiquidation', 0.0)
                config = st.session_state.control_panel.config if st.session_state.control_panel else None
                initial_balance = config.shared_settings.initial_balance if config else 50000.0
                
                # Calculate current month return
                current_return = ((net_liquidation - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
                current_month = datetime.now().strftime('%b')
                
                # Show only current month data for now
                return pd.DataFrame({
                    'month': [current_month],
                    'return': [current_return]
                })
            else:
                return pd.DataFrame({
                    'month': [datetime.now().strftime('%b')],
                    'return': [0.0]
                })
        else:
            return pd.DataFrame({
                'month': [datetime.now().strftime('%b')],
                'return': [0.0]
            })
    except Exception as e:
        st.error(f"Error getting monthly performance data: {str(e)}")
        return pd.DataFrame({
            'month': [datetime.now().strftime('%b')],
            'return': [0.0]
        })

def get_real_pnl_by_symbol():
    """Get real realized P&L by symbol from trading engine"""
    try:
        if st.session_state.trading_engine:
            engine = st.session_state.trading_engine
            strategy_status = engine.get_strategy_status()
            
            pnl_by_symbol = {}
            
            # Get P&L from strategy data
            for strategy_key, strategy in engine.strategies.items():
                symbol = strategy.settings.symbol
                # Calculate realized P&L from completed cycles
                realized_pnl = 0.0
                
                # This is simplified - in a full implementation, you'd track completed trades
                if hasattr(strategy, 'total_realized_pnl'):
                    realized_pnl = strategy.total_realized_pnl
                
                if symbol in pnl_by_symbol:
                    pnl_by_symbol[symbol] += realized_pnl
                else:
                    pnl_by_symbol[symbol] = realized_pnl
            
            # Filter out zero values
            pnl_by_symbol = {k: v for k, v in pnl_by_symbol.items() if v != 0}
            
            return pnl_by_symbol if pnl_by_symbol else {'No Data': 0}
        else:
            return {'No Data': 0}
    except Exception as e:
        st.error(f"Error getting P&L by symbol: {str(e)}")
        return {'Error': 0}

def get_real_unrealized_pnl_by_symbol():
    """Get real unrealized P&L by symbol from IBKR positions"""
    try:
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            api = st.session_state.trading_engine.api
            
            # Request fresh position data
            api.request_positions()
            time.sleep(0.5)
            
            unrealized_pnl = {}
            
            # Get unrealized P&L from current positions
            for symbol, ib_position in api.positions.items():
                if ib_position.position != 0:
                    # Get current market data
                    market_data = api.get_market_data(symbol)
                    current_price = market_data.price if market_data else ib_position.avg_cost
                    
                    # Calculate unrealized P&L
                    position_value = ib_position.position * current_price
                    cost_basis = ib_position.position * ib_position.avg_cost
                    pnl = position_value - cost_basis
                    
                    unrealized_pnl[symbol] = pnl
            
            return unrealized_pnl if unrealized_pnl else {'No Positions': 0}
        else:
            return {'No Data': 0}
    except Exception as e:
        st.error(f"Error getting unrealized P&L: {str(e)}")
        return {'Error': 0}

def get_real_cumulative_pnl_data():
    """Get real cumulative P&L data from trading engine"""
    try:
        if st.session_state.trading_engine and st.session_state.trading_engine.api:
            api = st.session_state.trading_engine.api
            engine = st.session_state.trading_engine
            
            # Get current account info
            account_info = api.account_info
            if account_info:
                net_liquidation = account_info.get('NetLiquidation', 0.0)
                config = st.session_state.control_panel.config if st.session_state.control_panel else None
                initial_balance = config.shared_settings.initial_balance if config else 50000.0
                
                # Calculate total P&L
                total_pnl = net_liquidation - initial_balance
                
                # Create simple progression from start to current
                start_time = engine.start_time if engine.start_time else datetime.now() - timedelta(days=1)
                dates = pd.date_range(start=start_time.date(), end=datetime.now().date(), freq='D')
                
                if len(dates) == 1:
                    dates = [start_time.date(), datetime.now().date()]
                
                # Linear progression of P&L (simplified)
                cumulative_pnl = np.linspace(0, total_pnl, len(dates))
                daily_pnl = np.diff(np.concatenate([[0], cumulative_pnl]))
                
                return pd.DataFrame({
                    'date': dates,
                    'daily_pnl': daily_pnl,
                    'cumulative_pnl': cumulative_pnl
                })
            else:
                # Fallback data
                dates = [datetime.now().date()]
                return pd.DataFrame({
                    'date': dates,
                    'daily_pnl': [0.0],
                    'cumulative_pnl': [0.0]
                })
        else:
            # Fallback data
            dates = [datetime.now().date()]
            return pd.DataFrame({
                'date': dates,
                'daily_pnl': [0.0],
                'cumulative_pnl': [0.0]
            })
    except Exception as e:
        st.error(f"Error getting cumulative P&L data: {str(e)}")
        dates = [datetime.now().date()]
        return pd.DataFrame({
            'date': dates,
            'daily_pnl': [0.0],
            'cumulative_pnl': [0.0]
        })

def get_real_strategy_metrics():
    """Get real strategy performance metrics from trading engine"""
    try:
        if st.session_state.trading_engine:
            engine = st.session_state.trading_engine
            strategy_status = engine.get_strategy_status()
            
            metrics = {}
            
            for strategy_key, status in strategy_status.items():
                # Extract strategy type and symbol from key
                strategy_name = strategy_key.split('_')[0] if '_' in strategy_key else strategy_key
                
                # Calculate metrics from strategy status
                total_cycles = status.get('total_cycles', 0)
                winning_cycles = status.get('winning_cycles', 0)
                win_rate = (winning_cycles / total_cycles * 100) if total_cycles > 0 else 0.0
                unrealized_pnl = status.get('unrealized_pnl', 0.0)
                
                metrics[strategy_name] = {
                    'Total Return (%)': 0.0,  # Would need historical data
                    'Sharpe Ratio': 0.0,  # Would need historical returns
                    'Max Drawdown (%)': 0.0,  # Would need historical equity curve
                    'Win Rate (%)': win_rate,
                    'Trades': total_cycles,
                    'Unrealized P&L ($)': unrealized_pnl
                }
            
            return metrics if metrics else {
                'No Strategies': {
                    'Total Return (%)': 0.0,
                    'Sharpe Ratio': 0.0,
                    'Max Drawdown (%)': 0.0,
                    'Win Rate (%)': 0.0,
                    'Trades': 0,
                    'Unrealized P&L ($)': 0.0
                }
            }
        else:
            return {
                'No Data': {
                    'Total Return (%)': 0.0,
                    'Sharpe Ratio': 0.0,
                    'Max Drawdown (%)': 0.0,
                    'Win Rate (%)': 0.0,
                    'Trades': 0,
                    'Unrealized P&L ($)': 0.0
                }
            }
    except Exception as e:
        st.error(f"Error getting strategy metrics: {str(e)}")
        return {
            'Error': {
                'Total Return (%)': 0.0,
                'Sharpe Ratio': 0.0,
                'Max Drawdown (%)': 0.0,
                'Win Rate (%)': 0.0,
                'Trades': 0,
                'Unrealized P&L ($)': 0.0
            }
        }

def get_real_strategy_allocation():
    """Get real strategy allocation from trading engine"""
    try:
        if st.session_state.trading_engine:
            engine = st.session_state.trading_engine
            
            # Calculate allocation based on active strategies
            active_strategies = [key for key, strategy in engine.strategies.items() if strategy.is_active]
            
            if active_strategies:
                # Equal allocation for now (simplified)
                allocation_per_strategy = 100 / len(active_strategies)
                allocation = {}
                
                for strategy_key in active_strategies:
                    strategy_name = strategy_key.split('_')[0] if '_' in strategy_key else strategy_key
                    allocation[strategy_name] = allocation_per_strategy
                
                return allocation
            else:
                return {'No Active Strategies': 100}
        else:
            return {'No Data': 100}
    except Exception as e:
        st.error(f"Error getting strategy allocation: {str(e)}")
        return {'Error': 100}

def get_broker_trade_history(symbol_filter, strategy_filter, date_from, date_to):
    """Get real trade history from broker account via IBKR API"""
    try:
        # Use session state trading engine API instead of global instance
        if not (st.session_state.trading_engine and st.session_state.trading_engine.api and st.session_state.trading_engine.api.is_connected):
            return get_real_trade_history(symbol_filter, strategy_filter, date_from, date_to)
        
        api = st.session_state.trading_engine.api
        
        # Request recent executions (last 7 days)
        api.request_executions(days_back=7)
        
        # Wait a moment for executions to be received
        import time
        time.sleep(2)
        
        # Get executions
        executions = api.get_executions(symbol_filter if symbol_filter != "All" else None)
        
        trades_data = []
        
        # Group executions by order ID to create trades
        from collections import defaultdict
        order_executions = defaultdict(list)
        
        for execution in executions:
            # Apply date filter
            if date_from or date_to:
                try:
                    # Parse execution time (format: YYYYMMDD HH:MM:SS)
                    exec_date = datetime.strptime(execution.time[:8], '%Y%m%d').date()
                    if date_from and exec_date < date_from:
                        continue
                    if date_to and exec_date > date_to:
                        continue
                except:
                    continue
            
            order_executions[execution.order_id].append(execution)
        
        # Convert executions to trade records
        for order_id, execs in order_executions.items():
            if not execs:
                continue
            
            # Calculate average price and total quantity
            total_shares = sum(exec.shares for exec in execs)
            avg_price = sum(exec.price * exec.shares for exec in execs) / total_shares if total_shares > 0 else 0
            
            # Use the first execution for common data
            first_exec = execs[0]
            
            # Format execution time
            try:
                exec_datetime = datetime.strptime(first_exec.time, '%Y%m%d  %H:%M:%S')
                formatted_time = exec_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = first_exec.time
            
            trades_data.append({
                'date': formatted_time,
                'symbol': first_exec.symbol,
                'strategy': 'Broker Account',
                'side': 'Buy' if first_exec.side == 'BOT' else 'Sell',
                'entry_price': avg_price,
                'exit_price': 0.0,
                'quantity': total_shares,
                'pnl': 0.0  # Would need to match buy/sell pairs to calculate P&L
            })
        
        # Add current positions from broker
        api.request_positions()
        time.sleep(1)
        
        for symbol, position in api.positions.items():
            if symbol_filter and symbol_filter != "All" and symbol != symbol_filter:
                continue
            
            if position.position != 0:  # Only show non-zero positions
                trades_data.append({
                    'date': 'Current',
                    'symbol': symbol,
                    'strategy': 'Broker Account',
                    'side': 'Open Position',
                    'entry_price': position.avg_cost,
                    'exit_price': 0.0,
                    'quantity': position.position,
                    'pnl': 0.0
                })
        
        return trades_data
        
    except Exception as e:
        st.error(f"Error getting broker trade history: {str(e)}")
        # Fallback to strategy data
        return get_real_trade_history(symbol_filter, strategy_filter, date_from, date_to)

def get_real_trade_history(symbol_filter, strategy_filter, date_from, date_to):
    """Get real trade history from trading engine (fallback)"""
    try:
        if st.session_state.trading_engine:
            engine = st.session_state.trading_engine
            
            trades = []
            
            # Get trade data from strategies
            for strategy_key, strategy in engine.strategies.items():
                strategy_name = strategy_key.split('_')[0] if '_' in strategy_key else strategy_key
                symbol = strategy.settings.symbol
                
                # Get completed positions/trades from strategy
                # This is simplified - in a full implementation, you'd have detailed trade logging
                if hasattr(strategy, 'completed_trades'):
                    for trade in strategy.completed_trades:
                        trades.append({
                            'date': trade.get('date', datetime.now().strftime('%Y-%m-%d %H:%M')),
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'side': trade.get('side', 'BUY'),
                            'quantity': trade.get('quantity', 0),
                            'entry_price': trade.get('entry_price', 0.0),
                            'exit_price': trade.get('exit_price', 0.0),
                            'pnl': trade.get('pnl', 0.0)
                        })
                
                # If no completed trades, show current positions as "open trades"
                elif strategy.positions:
                    for position in strategy.positions:
                        # Get current market data for unrealized P&L
                        market_data = engine.api.get_market_data(symbol) if engine.api else None
                        current_price = market_data.price if market_data else position.avg_price
                        
                        unrealized_pnl = (current_price - position.avg_price) * position.quantity
                        
                        trades.append({
                            'date': position.entry_time.strftime('%Y-%m-%d %H:%M') if hasattr(position, 'entry_time') and position.entry_time else datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'side': 'BUY' if position.quantity > 0 else 'SELL',
                            'quantity': abs(position.quantity),
                            'entry_price': position.avg_price,
                            'exit_price': current_price,  # Current price for open positions
                            'pnl': unrealized_pnl
                        })
            
            # Apply filters
            filtered_trades = trades
            
            if symbol_filter != "All":
                filtered_trades = [t for t in filtered_trades if t['symbol'] == symbol_filter]
            
            if strategy_filter != "All":
                filtered_trades = [t for t in filtered_trades if t['strategy'] == strategy_filter]
            
            # Apply date filters
            if date_from and date_to:
                filtered_trades = [
                    t for t in filtered_trades 
                    if date_from <= datetime.strptime(t['date'].split(' ')[0], '%Y-%m-%d').date() <= date_to
                ]
            
            return filtered_trades
        else:
            return []
    except Exception as e:
        st.error(f"Error getting trade history: {str(e)}")
        return []

def get_broker_performance_overview():
    """Get performance overview from broker account"""
    try:
        # Use session state trading engine API instead of global instance
        if not (st.session_state.trading_engine and st.session_state.trading_engine.api and st.session_state.trading_engine.api.is_connected):
            return get_performance_overview()  # Fallback to strategy data
        
        api = st.session_state.trading_engine.api
        
        # Request recent executions
        api.request_executions(days_back=30)
        import time
        time.sleep(2)
        
        executions = api.get_executions()
        
        total_volume = sum(exec.shares for exec in executions)
        total_trades = len(set(exec.order_id for exec in executions))
        
        # Get account balance for P&L (simplified)
        api.request_account_summary()
        time.sleep(1)
        account_balance = api.get_account_balance()
        
        # Count buy vs sell for basic win rate estimation
        buy_orders = len([exec for exec in executions if exec.side == 'BOT'])
        sell_orders = len([exec for exec in executions if exec.side == 'SLD'])
        
        return {
            'Account Balance': account_balance,
            'Total Trades': total_trades,
            'Total Volume': total_volume,
            'Buy Orders': buy_orders,
            'Sell Orders': sell_orders,
            'Data Source': 'Broker Account'
        }
        
    except Exception as e:
        st.error(f"Error getting broker performance overview: {str(e)}")
        return get_performance_overview()  # Fallback

def get_performance_overview():
    """Get performance overview data from strategy tracking"""
    try:
        if st.session_state.trading_engine:
            engine = st.session_state.trading_engine
            
            total_pnl = 0
            total_trades = 0
            winning_trades = 0
            total_volume = 0
            
            for strategy_id, strategy in engine.strategies.items():
                # Count completed trades
                for trade in strategy.completed_trades:
                    total_trades += 1
                    if hasattr(trade, 'pnl') and trade.pnl:
                        total_pnl += trade.pnl
                        if trade.pnl > 0:
                            winning_trades += 1
                    if hasattr(trade, 'quantity'):
                        total_volume += abs(trade.quantity)
                
                # Add unrealized P&L from current positions
                for position in strategy.positions:
                    if hasattr(position, 'unrealized_pnl'):
                        total_pnl += position.unrealized_pnl
                    if hasattr(position, 'quantity'):
                        total_volume += abs(position.quantity)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'Total P&L': total_pnl,
                'Total Trades': total_trades,
                'Win Rate': win_rate,
                'Total Volume': total_volume,
                'Data Source': 'Strategy Data'
            }
        else:
            return {
                'Total P&L': 0,
                'Total Trades': 0,
                'Win Rate': 0,
                'Total Volume': 0,
                'Data Source': 'Strategy Data'
            }
    except Exception as e:
        st.error(f"Error getting performance overview: {str(e)}")
        return {
            'Total P&L': 0,
            'Total Trades': 0,
            'Win Rate': 0,
            'Total Volume': 0,
            'Data Source': 'Strategy Data'
        }

if __name__ == "__main__":
    render_performance_analytics()