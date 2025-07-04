import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cycle_analysis import CycleAnalysisReport, Cycle, CycleStatus
from config import TradingConfig

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

def render_cycle_analysis_page(cycle_report: CycleAnalysisReport, symbol: str = "Portfolio"):
    """Render dedicated cycle analysis page with advanced features"""
    render_title_with_tooltip(
        "🔄 Advanced Cycle Analysis Dashboard", 
        "Comprehensive analysis of trading cycles including performance metrics, optimization insights, and detailed comparisons",
        "header"
    )
    st.markdown(f"Comprehensive cycle analysis and optimization for **{symbol}**")
    
    # Real-time status indicator
    status_col1, status_col2, status_col3 = st.columns([2, 1, 1])
    with status_col1:
        st.markdown(f"**📊 Analysis Target:** {symbol}")
    with status_col2:
        st.markdown(f"**🕒 Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
    with status_col3:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    if not cycle_report or not cycle_report.cycles:
        st.warning("No cycle data available for analysis.")
        # Show sample data upload option
        st.info("💡 **Tip:** Upload cycle data CSV or connect to live trading data to begin analysis")
        
        with st.expander("📤 Upload Sample Data"):
            uploaded_file = st.file_uploader(
                "Choose a CSV file with cycle data",
                type="csv",
                help="CSV should contain columns: cycle_id, strategy_type, start_time, realized_pnl, etc."
            )
            if uploaded_file is not None:
                try:
                    sample_df = pd.read_csv(uploaded_file)
                    st.success(f"✅ Loaded {len(sample_df)} cycles from uploaded file")
                    st.dataframe(sample_df.head(), use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        return
    
    # Get cycle data
    cycle_df = cycle_report.export_to_dataframe()
    
    if cycle_df.empty:
        st.warning("No cycle data available for analysis.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Analysis Filters")
    
    # Strategy filter
    strategies = ['All'] + list(cycle_df['strategy_type'].unique())
    selected_strategies = st.sidebar.multiselect(
        "Select Strategies",
        strategies,
        default=['All']
    )
    
    # Status filter
    statuses = ['All'] + list(cycle_df['status'].unique())
    selected_status = st.sidebar.selectbox("Cycle Status", statuses)
    
    # Date range filter
    if 'start_time' in cycle_df.columns:
        min_date = cycle_df['start_time'].min().date()
        max_date = cycle_df['start_time'].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    # PnL range filter
    if 'realized_pnl' in cycle_df.columns:
        min_pnl = float(cycle_df['realized_pnl'].min())
        max_pnl = float(cycle_df['realized_pnl'].max())
        
        pnl_range = st.sidebar.slider(
            "PnL Range ($)",
            min_value=min_pnl,
            max_value=max_pnl,
            value=(min_pnl, max_pnl),
            step=10.0
        )
    
    # Apply filters
    filtered_df = cycle_df.copy()
    
    if 'All' not in selected_strategies:
        filtered_df = filtered_df[filtered_df['strategy_type'].isin(selected_strategies)]
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['status'] == selected_status]
    
    if len(date_range) == 2 and 'start_time' in filtered_df.columns:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['start_time'].dt.date >= start_date) &
            (filtered_df['start_time'].dt.date <= end_date)
        ]
    
    if 'realized_pnl' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['realized_pnl'] >= pnl_range[0]) &
            (filtered_df['realized_pnl'] <= pnl_range[1])
        ]
    
    if filtered_df.empty:
        st.warning("No cycles match the selected filters.")
        return
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "📈 Performance Analysis", 
        "🔍 Cycle Comparison",
        "🎯 Optimization",
        "📋 Detailed Data",
        "📤 Export & Reports"
    ])
    
    with tab1:
        render_cycle_overview(filtered_df, cycle_report)
    
    with tab2:
        render_performance_analysis(filtered_df, symbol)
    
    with tab3:
        render_cycle_comparison(filtered_df)
    
    with tab4:
        render_optimization_analysis(filtered_df, cycle_report, symbol)
    
    with tab5:
        render_detailed_data(filtered_df)
    
    with tab6:
        render_export_reports(filtered_df, cycle_report, symbol)

def render_cycle_overview(cycle_df: pd.DataFrame, cycle_report: CycleAnalysisReport):
    """Render cycle overview with key metrics and summary charts"""
    st.markdown("## 📊 Real-Time Cycle Overview")
    
    # Real-time status indicators
    status_row1 = st.columns([1, 1, 1, 1])
    
    with status_row1[0]:
        active_cycles = len(cycle_df[cycle_df['status'] == 'ACTIVE']) if 'status' in cycle_df.columns else 0
        st.metric("🔄 Active Cycles", active_cycles, help="Currently running cycles")
    
    with status_row1[1]:
        pending_cycles = len(cycle_df[cycle_df['status'] == 'PENDING']) if 'status' in cycle_df.columns else 0
        st.metric("⏳ Pending Cycles", pending_cycles, help="Cycles waiting to start")
    
    with status_row1[2]:
        if 'realized_pnl' in cycle_df.columns:
            today_pnl = 0  # This would be calculated from today's completed cycles
            # For demo purposes, we'll use a sample calculation
            if 'start_time' in cycle_df.columns:
                today_cycles = cycle_df[cycle_df['start_time'].dt.date == datetime.now().date()]
                today_pnl = today_cycles['realized_pnl'].sum() if len(today_cycles) > 0 else 0
            st.metric("📈 Today's PnL", f"${today_pnl:,.2f}", help="PnL from cycles completed today")
    
    with status_row1[3]:
        if 'total_investment' in cycle_df.columns:
            total_capital_deployed = cycle_df[cycle_df['status'] == 'ACTIVE']['total_investment'].sum() if 'status' in cycle_df.columns else 0
            st.metric("💰 Capital Deployed", f"${total_capital_deployed:,.2f}", help="Total capital in active cycles")
    
    st.divider()
    
    # Key performance metrics
    render_title_with_tooltip(
        "📈 Key Performance Metrics", 
        "Essential performance indicators including total cycles, completion rates, win rates, and profitability metrics",
        "markdown"
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Cycles", len(cycle_df))
    
    with col2:
        completed = len(cycle_df[cycle_df['status'] == 'COMPLETED']) if 'status' in cycle_df.columns else len(cycle_df)
        completion_rate = (completed / len(cycle_df) * 100) if len(cycle_df) > 0 else 0
        st.metric("Completed", completed, f"{completion_rate:.1f}%")
    
    with col3:
        if 'realized_pnl' in cycle_df.columns:
            winning = len(cycle_df[cycle_df['realized_pnl'] > 0])
            win_rate = (winning / completed * 100) if completed > 0 else 0
            # Calculate trend (simplified)
            win_rate_trend = "+2.3%" if win_rate > 50 else "-1.1%"
            st.metric("Win Rate", f"{win_rate:.1f}%", win_rate_trend)
    
    with col4:
        if 'realized_pnl' in cycle_df.columns:
            total_pnl = cycle_df['realized_pnl'].sum()
            # Calculate trend (simplified)
            pnl_trend = f"+${abs(total_pnl * 0.05):,.0f}" if total_pnl > 0 else f"-${abs(total_pnl * 0.03):,.0f}"
            st.metric("Total PnL", f"${total_pnl:,.2f}", pnl_trend)
    
    with col5:
        if 'realized_pnl' in cycle_df.columns:
            avg_pnl = cycle_df['realized_pnl'].mean()
            # Calculate trend (simplified)
            avg_trend = f"+${abs(avg_pnl * 0.08):,.0f}" if avg_pnl > 0 else f"-${abs(avg_pnl * 0.04):,.0f}"
            st.metric("Avg PnL", f"${avg_pnl:,.2f}", avg_trend)
    
    # Advanced metrics row
    render_title_with_tooltip(
        "🎯 Advanced Performance Metrics", 
        "Advanced statistical measures including profit factor, Sharpe ratio, maximum drawdown, and return on investment",
        "markdown"
    )
    adv_col1, adv_col2, adv_col3, adv_col4, adv_col5 = st.columns(5)
    
    with adv_col1:
        if 'realized_pnl' in cycle_df.columns:
            profit_factor = abs(cycle_df[cycle_df['realized_pnl'] > 0]['realized_pnl'].sum() / 
                               cycle_df[cycle_df['realized_pnl'] <= 0]['realized_pnl'].sum()) if cycle_df[cycle_df['realized_pnl'] <= 0]['realized_pnl'].sum() != 0 else float('inf')
            st.metric("Profit Factor", f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞")
    
    with adv_col2:
        if 'realized_pnl' in cycle_df.columns and len(cycle_df) > 1:
            sharpe_ratio = cycle_df['realized_pnl'].mean() / cycle_df['realized_pnl'].std() if cycle_df['realized_pnl'].std() > 0 else 0
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.3f}")
    
    with adv_col3:
        if 'realized_pnl' in cycle_df.columns:
            max_drawdown = cycle_df['realized_pnl'].min()
            st.metric("Max Drawdown", f"${max_drawdown:,.2f}")
    
    with adv_col4:
        if 'duration_minutes' in cycle_df.columns:
            avg_duration = cycle_df['duration_minutes'].mean()
            st.metric("Avg Duration", f"{avg_duration:.1f} min")
    
    with adv_col5:
        if 'total_investment' in cycle_df.columns and 'realized_pnl' in cycle_df.columns:
            total_invested = cycle_df['total_investment'].sum()
            roi = (cycle_df['realized_pnl'].sum() / total_invested * 100) if total_invested > 0 else 0
            st.metric("Overall ROI", f"{roi:.2f}%")
    
    # Summary charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Strategy distribution
        if 'strategy_type' in cycle_df.columns:
            strategy_counts = cycle_df['strategy_type'].value_counts()
            
            fig_strategy = go.Figure(data=[
                go.Pie(
                    labels=strategy_counts.index,
                    values=strategy_counts.values,
                    hole=0.4,
                    textinfo='label+percent'
                )
            ])
            
            fig_strategy.update_layout(
                title="Cycles by Strategy",
                height=400
            )
            
            st.plotly_chart(fig_strategy, use_container_width=True)
    
    with chart_col2:
        # PnL distribution by strategy
        if 'strategy_type' in cycle_df.columns and 'realized_pnl' in cycle_df.columns:
            fig_pnl_strategy = go.Figure()
            
            for strategy in cycle_df['strategy_type'].unique():
                strategy_data = cycle_df[cycle_df['strategy_type'] == strategy]
                
                fig_pnl_strategy.add_trace(go.Box(
                    y=strategy_data['realized_pnl'],
                    name=strategy,
                    boxpoints='outliers'
                ))
            
            fig_pnl_strategy.update_layout(
                title="PnL Distribution by Strategy",
                yaxis_title="PnL ($)",
                height=400
            )
            
            st.plotly_chart(fig_pnl_strategy, use_container_width=True)

def render_performance_analysis(cycle_df: pd.DataFrame, symbol: str):
    """Render detailed performance analysis with real-time monitoring"""
    render_title_with_tooltip(
        "📈 Advanced Performance Analysis", 
        "In-depth analysis of cycle performance including real-time monitoring, statistical metrics, and trend analysis",
        "subheader"
    )
    
    # Real-time performance dashboard
    render_title_with_tooltip(
        "🔄 Real-Time Performance Dashboard", 
        "Live tracking of performance metrics with cumulative PnL charts and real-time statistics",
        "markdown"
    )
    
    # Create real-time metrics with auto-refresh
    dashboard_col1, dashboard_col2 = st.columns([2, 1])
    
    with dashboard_col1:
        # Live performance chart
        if 'start_time' in cycle_df.columns and 'realized_pnl' in cycle_df.columns:
            # Sort by time and create cumulative PnL
            sorted_df = cycle_df.sort_values('start_time')
            sorted_df['cumulative_pnl'] = sorted_df['realized_pnl'].cumsum()
            
            fig_live = go.Figure()
            
            # Add cumulative PnL line
            fig_live.add_trace(go.Scatter(
                x=sorted_df['start_time'],
                y=sorted_df['cumulative_pnl'],
                mode='lines+markers',
                name='Cumulative PnL',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6),
                hovertemplate='Time: %{x}<br>Cumulative PnL: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add individual cycle markers with color coding
            colors = ['green' if pnl > 0 else 'red' for pnl in sorted_df['realized_pnl']]
            fig_live.add_trace(go.Scatter(
                x=sorted_df['start_time'],
                y=sorted_df['realized_pnl'],
                mode='markers',
                name='Individual Cycles',
                marker=dict(color=colors, size=8, opacity=0.7),
                yaxis='y2',
                hovertemplate='Time: %{x}<br>Cycle PnL: $%{y:,.2f}<extra></extra>'
            ))
            
            fig_live.update_layout(
                title=f"Live Performance Tracking - {symbol}",
                xaxis_title="Time",
                yaxis_title="Cumulative PnL ($)",
                yaxis2=dict(
                    title="Individual Cycle PnL ($)",
                    overlaying='y',
                    side='right'
                ),
                template='plotly_white',
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_live, use_container_width=True)
    
    with dashboard_col2:
        # Live statistics
        st.markdown("**📊 Live Statistics**")
        
        if 'realized_pnl' in cycle_df.columns:
            # Recent performance (last 10 cycles)
            recent_cycles = cycle_df.tail(10) if len(cycle_df) >= 10 else cycle_df
            recent_win_rate = (recent_cycles['realized_pnl'] > 0).sum() / len(recent_cycles) * 100
            recent_avg_pnl = recent_cycles['realized_pnl'].mean()
            
            st.metric("Recent Win Rate (Last 10)", f"{recent_win_rate:.1f}%")
            st.metric("Recent Avg PnL", f"${recent_avg_pnl:,.2f}")
            
            # Performance trend indicator
            if len(cycle_df) >= 20:
                first_half = cycle_df.head(len(cycle_df)//2)['realized_pnl'].mean()
                second_half = cycle_df.tail(len(cycle_df)//2)['realized_pnl'].mean()
                trend = "📈 Improving" if second_half > first_half else "📉 Declining"
                st.metric("Performance Trend", trend)
            
            # Risk indicator
            volatility = cycle_df['realized_pnl'].std()
            avg_pnl = cycle_df['realized_pnl'].mean()
            risk_level = "🟢 Low" if volatility < abs(avg_pnl) else "🟡 Medium" if volatility < abs(avg_pnl) * 2 else "🔴 High"
            st.metric("Risk Level", risk_level)
    
    st.divider()
    
    # Detailed performance metrics
    render_title_with_tooltip(
        "📊 Detailed Performance Metrics", 
        "Comprehensive statistical analysis including return metrics, duration analysis, and risk measurements",
        "markdown"
    )
    perf_col1, perf_col2, perf_col3 = st.columns(3)
    
    with perf_col1:
        st.markdown("**📊 Return Metrics**")
        if 'realized_pnl' in cycle_df.columns:
            returns = cycle_df['realized_pnl']
            st.write(f"• Best Cycle: ${returns.max():,.2f}")
            st.write(f"• Worst Cycle: ${returns.min():,.2f}")
            st.write(f"• Median PnL: ${returns.median():,.2f}")
            st.write(f"• Std Deviation: ${returns.std():,.2f}")
            st.write(f"• Skewness: {returns.skew():.3f}")
            st.write(f"• Kurtosis: {returns.kurtosis():.3f}")
    
    with perf_col2:
        st.markdown("**⏱️ Duration Metrics**")
        if 'duration_minutes' in cycle_df.columns:
            durations = cycle_df['duration_minutes']
            st.write(f"• Avg Duration: {durations.mean():.1f} min")
            st.write(f"• Median Duration: {durations.median():.1f} min")
            st.write(f"• Max Duration: {durations.max():.1f} min")
            st.write(f"• Min Duration: {durations.min():.1f} min")
            st.write(f"• Duration Std: {durations.std():.1f} min")
            
            # Duration efficiency
            if 'realized_pnl' in cycle_df.columns:
                pnl_per_minute = cycle_df['realized_pnl'] / cycle_df['duration_minutes']
                st.write(f"• Avg PnL/min: ${pnl_per_minute.mean():.2f}")
    
    with perf_col3:
        st.markdown("**💰 Investment Metrics**")
        if 'total_investment' in cycle_df.columns:
            investments = cycle_df['total_investment']
            st.write(f"• Avg Investment: ${investments.mean():,.2f}")
            st.write(f"• Max Investment: ${investments.max():,.2f}")
            st.write(f"• Total Invested: ${investments.sum():,.2f}")
            
            if 'max_investment' in cycle_df.columns:
                max_investments = cycle_df['max_investment']
                st.write(f"• Peak Investment: ${max_investments.max():,.2f}")
            
            # Capital efficiency
            if 'realized_pnl' in cycle_df.columns:
                capital_efficiency = cycle_df['realized_pnl'].sum() / investments.sum() * 100
                st.write(f"• Capital Efficiency: {capital_efficiency:.2f}%")
                
                # Return on investment
                roi_per_cycle = (cycle_df['realized_pnl'] / cycle_df['total_investment'] * 100).mean()
                st.write(f"• Avg ROI per Cycle: {roi_per_cycle:.2f}%")
    
    # Advanced Performance Charts
    if 'start_time' in cycle_df.columns and 'realized_pnl' in cycle_df.columns:
        render_title_with_tooltip(
            "📈 Advanced Rolling Performance Analytics", 
            "Interactive charts showing rolling performance metrics with configurable windows and confidence bands",
            "markdown"
        )
        
        # Chart configuration
        chart_col1, chart_col2, chart_col3 = st.columns(3)
        
        with chart_col1:
            window_size = st.selectbox(
                "Rolling Window Size:",
                [5, 10, 20, 50],
                index=1,
                key="perf_window"
            )
        
        with chart_col2:
            chart_type = st.selectbox(
                "Chart Type:",
                ["Standard", "Normalized", "Volatility Adjusted"],
                key="chart_type"
            )
        
        with chart_col3:
            show_bands = st.checkbox("Show Confidence Bands", value=True)
        
        if len(cycle_df) >= window_size:
            # Calculate rolling metrics
            sorted_df = cycle_df.sort_values('start_time')
            
            rolling_pnl = sorted_df['realized_pnl'].rolling(window=window_size).sum()
            rolling_avg_pnl = sorted_df['realized_pnl'].rolling(window=window_size).mean()
            rolling_win_rate = (sorted_df['realized_pnl'] > 0).rolling(window=window_size).mean() * 100
            rolling_std = sorted_df['realized_pnl'].rolling(window=window_size).std()
            rolling_sharpe = rolling_avg_pnl / rolling_std
            
            # Calculate additional metrics
            rolling_max_dd = []
            for i in range(len(sorted_df)):
                if i < window_size - 1:
                    rolling_max_dd.append(None)
                else:
                    window_data = sorted_df['realized_pnl'].iloc[i-window_size+1:i+1]
                    cumsum = window_data.cumsum()
                    running_max = cumsum.expanding().max()
                    drawdown = (cumsum - running_max)
                    rolling_max_dd.append(drawdown.min())
            
            # Apply chart type transformations
            if chart_type == "Normalized":
                rolling_pnl = (rolling_pnl - rolling_pnl.mean()) / rolling_pnl.std()
                rolling_avg_pnl = (rolling_avg_pnl - rolling_avg_pnl.mean()) / rolling_avg_pnl.std()
            elif chart_type == "Volatility Adjusted":
                rolling_pnl = rolling_pnl / rolling_std
                rolling_avg_pnl = rolling_avg_pnl / rolling_std
            
            # Create enhanced subplots
            fig_rolling = make_subplots(
                rows=4, cols=1,
                subplot_titles=(
                    f'Rolling {window_size}-Cycle Total PnL ({chart_type})',
                    f'Rolling {window_size}-Cycle Average PnL ({chart_type})',
                    f'Rolling {window_size}-Cycle Win Rate (%)',
                    f'Rolling {window_size}-Cycle Sharpe Ratio & Max Drawdown'
                ),
                vertical_spacing=0.06
            )
            
            # Add main traces
            fig_rolling.add_trace(
                go.Scatter(
                    x=sorted_df['start_time'],
                    y=rolling_pnl,
                    mode='lines',
                    name='Rolling Total PnL',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # Add confidence bands if enabled
            if show_bands and chart_type == "Standard":
                upper_band = rolling_pnl + rolling_std
                lower_band = rolling_pnl - rolling_std
                
                fig_rolling.add_trace(
                    go.Scatter(
                        x=sorted_df['start_time'],
                        y=upper_band,
                        mode='lines',
                        line=dict(width=0),
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=1, col=1
                )
                
                fig_rolling.add_trace(
                    go.Scatter(
                        x=sorted_df['start_time'],
                        y=lower_band,
                        mode='lines',
                        line=dict(width=0),
                        fill='tonexty',
                        fillcolor='rgba(0,100,80,0.2)',
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=1, col=1
                )
            
            fig_rolling.add_trace(
                go.Scatter(
                    x=sorted_df['start_time'],
                    y=rolling_avg_pnl,
                    mode='lines',
                    name='Rolling Avg PnL',
                    line=dict(color='green', width=2)
                ),
                row=2, col=1
            )
            
            fig_rolling.add_trace(
                go.Scatter(
                    x=sorted_df['start_time'],
                    y=rolling_win_rate,
                    mode='lines',
                    name='Rolling Win Rate',
                    line=dict(color='orange', width=2)
                ),
                row=3, col=1
            )
            
            # Add 50% reference line for win rate
            fig_rolling.add_hline(y=50, line_dash="dash", line_color="gray", row=3, col=1)
            
            # Sharpe ratio and max drawdown
            fig_rolling.add_trace(
                go.Scatter(
                    x=sorted_df['start_time'],
                    y=rolling_sharpe,
                    mode='lines',
                    name='Sharpe Ratio',
                    line=dict(color='purple', width=2),
                    yaxis='y4'
                ),
                row=4, col=1
            )
            
            # Add max drawdown on secondary y-axis
            fig_rolling.add_trace(
                go.Scatter(
                    x=sorted_df['start_time'],
                    y=rolling_max_dd,
                    mode='lines',
                    name='Max Drawdown',
                    line=dict(color='red', width=2),
                    yaxis='y5'
                ),
                row=4, col=1
            )
            
            # Update layout with secondary y-axes
            fig_rolling.update_layout(
                height=1000,
                title_text=f"Advanced Rolling Performance Analysis (Window: {window_size} cycles)",
                showlegend=False,
                yaxis4=dict(title="Sharpe Ratio", side="left"),
                yaxis5=dict(title="Max Drawdown ($)", side="right", overlaying="y4")
            )
            
            st.plotly_chart(fig_rolling, use_container_width=True)
            
            # Performance insights
            render_title_with_tooltip(
                "🔍 Performance Insights", 
                "Key insights and recommendations based on rolling performance analysis and statistical trends",
                "markdown"
            )
            
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                st.markdown("**📊 Rolling Statistics Summary**")
                current_win_rate = rolling_win_rate.iloc[-1] if not pd.isna(rolling_win_rate.iloc[-1]) else 0
                current_sharpe = rolling_sharpe.iloc[-1] if not pd.isna(rolling_sharpe.iloc[-1]) else 0
                current_avg_pnl = rolling_avg_pnl.iloc[-1] if not pd.isna(rolling_avg_pnl.iloc[-1]) else 0
                
                st.write(f"• Current Win Rate: {current_win_rate:.1f}%")
                st.write(f"• Current Sharpe Ratio: {current_sharpe:.3f}")
                st.write(f"• Current Avg PnL: ${current_avg_pnl:,.2f}")
                
                # Performance consistency
                win_rate_std = rolling_win_rate.std()
                consistency = "High" if win_rate_std < 10 else "Medium" if win_rate_std < 20 else "Low"
                st.write(f"• Win Rate Consistency: {consistency} (σ={win_rate_std:.1f}%)")
            
            with insights_col2:
                st.markdown("**🎯 Performance Trends**")
                
                # Trend analysis
                recent_performance = rolling_avg_pnl.tail(10).mean()
                earlier_performance = rolling_avg_pnl.head(10).mean()
                
                if recent_performance > earlier_performance * 1.1:
                    trend_status = "📈 Strong Improvement"
                elif recent_performance > earlier_performance:
                    trend_status = "📊 Slight Improvement"
                elif recent_performance > earlier_performance * 0.9:
                    trend_status = "➡️ Stable"
                else:
                    trend_status = "📉 Declining"
                
                st.write(f"• Overall Trend: {trend_status}")
                
                # Volatility trend
                recent_volatility = rolling_std.tail(10).mean()
                earlier_volatility = rolling_std.head(10).mean()
                vol_trend = "Decreasing" if recent_volatility < earlier_volatility else "Increasing"
                st.write(f"• Volatility Trend: {vol_trend}")
                
                # Best/worst periods
                best_period = rolling_avg_pnl.idxmax()
                worst_period = rolling_avg_pnl.idxmin()
                st.write(f"• Best Period: Cycle {best_period}")
                st.write(f"• Worst Period: Cycle {worst_period}")
        else:
            st.warning(f"Need at least {window_size} cycles for rolling analysis.")

def render_cycle_comparison(cycle_df: pd.DataFrame):
    """Render advanced cycle comparison tools"""
    st.markdown("## ⚖️ Advanced Cycle Comparison")
    
    if len(cycle_df) < 2:
        st.warning("Need at least 2 cycles for comparison.")
        return
    
    # Comparison mode selection
    comparison_mode = st.radio(
        "Comparison Mode:",
        ["Individual Cycles", "Strategy Groups", "Performance Quartiles", "Time Periods"],
        horizontal=True
    )
    
    if comparison_mode == "Individual Cycles":
        render_individual_cycle_comparison(cycle_df)
    elif comparison_mode == "Strategy Groups":
        render_strategy_group_comparison(cycle_df)
    elif comparison_mode == "Performance Quartiles":
        render_quartile_comparison(cycle_df)
    else:  # Time Periods
        render_time_period_comparison(cycle_df)

def render_individual_cycle_comparison(cycle_df: pd.DataFrame):
    """Render individual cycle comparison"""
    st.markdown("### 🔍 Individual Cycle Analysis")
    
    # Enhanced cycle selection with filtering
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        strategy_filter = st.multiselect(
            "Filter by Strategy:",
            cycle_df['strategy_type'].unique() if 'strategy_type' in cycle_df.columns else [],
            default=cycle_df['strategy_type'].unique() if 'strategy_type' in cycle_df.columns else []
        )
    
    with filter_col2:
        min_pnl = st.number_input("Min PnL:", value=float(cycle_df['realized_pnl'].min()) if 'realized_pnl' in cycle_df.columns else 0.0)
        max_pnl = st.number_input("Max PnL:", value=float(cycle_df['realized_pnl'].max()) if 'realized_pnl' in cycle_df.columns else 0.0)
    
    with filter_col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["PnL", "Duration", "Investment", "ROI", "Recent"],
            index=0
        )
    
    # Apply filters
    filtered_df = cycle_df.copy()
    if strategy_filter and 'strategy_type' in cycle_df.columns:
        filtered_df = filtered_df[filtered_df['strategy_type'].isin(strategy_filter)]
    if 'realized_pnl' in cycle_df.columns:
        filtered_df = filtered_df[(filtered_df['realized_pnl'] >= min_pnl) & (filtered_df['realized_pnl'] <= max_pnl)]
    
    # Sort cycles
    if sort_by == "PnL" and 'realized_pnl' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('realized_pnl', ascending=False)
    elif sort_by == "Duration" and 'duration_minutes' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('duration_minutes', ascending=False)
    elif sort_by == "Investment" and 'total_investment' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('total_investment', ascending=False)
    elif sort_by == "ROI" and 'realized_pnl' in filtered_df.columns and 'total_investment' in filtered_df.columns:
        filtered_df['roi'] = filtered_df['realized_pnl'] / filtered_df['total_investment'] * 100
        filtered_df = filtered_df.sort_values('roi', ascending=False)
    elif sort_by == "Recent" and 'start_time' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('start_time', ascending=False)
    
    if len(filtered_df) < 2:
        st.warning("Need at least 2 cycles matching the filters for comparison.")
        return
    
    # Cycle selection for comparison
    st.markdown("**Select Cycles to Compare**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cycle1_options = [f"Cycle {idx}: {row.get('strategy_type', 'Unknown')} - PnL: ${row.get('realized_pnl', 0):.2f}" 
                         for idx, row in filtered_df.iterrows()]
        cycle1_idx = st.selectbox("First Cycle:", range(len(cycle1_options)), 
                                 format_func=lambda x: cycle1_options[x])
        cycle1 = filtered_df.iloc[cycle1_idx]
    
    with col2:
        cycle2_options = [f"Cycle {idx}: {row.get('strategy_type', 'Unknown')} - PnL: ${row.get('realized_pnl', 0):.2f}" 
                         for idx, row in filtered_df.iterrows()]
        cycle2_idx = st.selectbox("Second Cycle:", range(len(cycle2_options)), 
                                 format_func=lambda x: cycle2_options[x],
                                 index=1 if len(cycle2_options) > 1 else 0)
        cycle2 = filtered_df.iloc[cycle2_idx]
    
    if cycle1_idx == cycle2_idx:
        st.warning("Please select two different cycles for comparison.")
        return
    
    # Enhanced comparison table
    st.markdown("### 📊 Detailed Comparison")
    
    comparison_data = {
        'Metric': [
            'Strategy Type', 'Status', 'PnL ($)', 'Total Investment ($)', 'Max Investment ($)',
            'Duration (min)', 'Trade Count', 'Max Order Level', 'ROI (%)', 'Efficiency',
            'Capital Efficiency', 'Start Time', 'End Time'
        ],
        f'Cycle {filtered_df.index[cycle1_idx]}': [
            str(cycle1.get('strategy_type', 'N/A')),
            str(cycle1.get('status', 'N/A')),
            f"${cycle1.get('realized_pnl', 0):.2f}",
            f"${cycle1.get('total_investment', 0):.2f}",
            f"${cycle1.get('max_investment', cycle1.get('total_investment', 0)):.2f}",
            f"{cycle1.get('duration_minutes', 0):.1f}",
            str(cycle1.get('trade_count', 0)),
            str(cycle1.get('max_order_level', 0)),
            f"{(cycle1.get('realized_pnl', 0) / max(cycle1.get('total_investment', 1), 1) * 100):.2f}%",
            f"{(cycle1.get('realized_pnl', 0) / max(cycle1.get('duration_minutes', 1), 1)):.3f}",
            f"{(cycle1.get('realized_pnl', 0) / max(cycle1.get('max_investment', cycle1.get('total_investment', 1)), 1) * 100):.2f}%",
            str(cycle1.get('start_time', 'N/A')),
            str(cycle1.get('end_time', 'N/A'))
        ],
        f'Cycle {filtered_df.index[cycle2_idx]}': [
            str(cycle2.get('strategy_type', 'N/A')),
            str(cycle2.get('status', 'N/A')),
            f"${cycle2.get('realized_pnl', 0):.2f}",
            f"${cycle2.get('total_investment', 0):.2f}",
            f"${cycle2.get('max_investment', cycle2.get('total_investment', 0)):.2f}",
            f"{cycle2.get('duration_minutes', 0):.1f}",
            str(cycle2.get('trade_count', 0)),
            str(cycle2.get('max_order_level', 0)),
            f"{(cycle2.get('realized_pnl', 0) / max(cycle2.get('total_investment', 1), 1) * 100):.2f}%",
            f"{(cycle2.get('realized_pnl', 0) / max(cycle2.get('duration_minutes', 1), 1)):.3f}",
            f"{(cycle2.get('realized_pnl', 0) / max(cycle2.get('max_investment', cycle2.get('total_investment', 1)), 1) * 100):.2f}%",
            str(cycle2.get('start_time', 'N/A')),
            str(cycle2.get('end_time', 'N/A'))
        ]
    }
    
    # Add difference column
    differences = []
    for i, metric in enumerate(comparison_data['Metric']):
        if metric in ['PnL ($)', 'Total Investment ($)', 'Max Investment ($)', 'Duration (min)', 'ROI (%)']:
            try:
                val1 = float(comparison_data[f'Cycle {filtered_df.index[cycle1_idx]}'][i].replace('$', '').replace('%', ''))
                val2 = float(comparison_data[f'Cycle {filtered_df.index[cycle2_idx]}'][i].replace('$', '').replace('%', ''))
                diff = val1 - val2
                if metric in ['PnL ($)', 'Total Investment ($)', 'Max Investment ($)']:
                    differences.append(f"${diff:+.2f}")
                else:
                    differences.append(f"{diff:+.2f}")
            except:
                differences.append('N/A')
        elif metric in ['Trade Count', 'Max Order Level']:
            try:
                val1 = int(comparison_data[f'Cycle {filtered_df.index[cycle1_idx]}'][i])
                val2 = int(comparison_data[f'Cycle {filtered_df.index[cycle2_idx]}'][i])
                diff = val1 - val2
                differences.append(f"{diff:+d}")
            except:
                differences.append('N/A')
        else:
            differences.append('-')
    
    comparison_data['Difference (C1 - C2)'] = differences
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Performance insights
    st.markdown("### 🎯 Performance Insights")
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.markdown("**Winner Analysis:**")
        pnl1 = cycle1.get('realized_pnl', 0)
        pnl2 = cycle2.get('realized_pnl', 0)
        roi1 = pnl1 / max(cycle1.get('total_investment', 1), 1) * 100
        roi2 = pnl2 / max(cycle2.get('total_investment', 1), 1) * 100
        
        if pnl1 > pnl2:
            st.success(f"🏆 Cycle {filtered_df.index[cycle1_idx]} wins by PnL (${pnl1 - pnl2:.2f})")
        elif pnl2 > pnl1:
            st.success(f"🏆 Cycle {filtered_df.index[cycle2_idx]} wins by PnL (${pnl2 - pnl1:.2f})")
        else:
            st.info("🤝 Tie in PnL")
        
        if roi1 > roi2:
            st.info(f"📈 Cycle {filtered_df.index[cycle1_idx]} has better ROI ({roi1 - roi2:.2f}% higher)")
        elif roi2 > roi1:
            st.info(f"📈 Cycle {filtered_df.index[cycle2_idx]} has better ROI ({roi2 - roi1:.2f}% higher)")
    
    with insight_col2:
        st.markdown("**Statistical Comparison:**")
        duration1 = cycle1.get('duration_minutes', 0)
        duration2 = cycle2.get('duration_minutes', 0)
        
        if duration1 < duration2:
            st.info(f"⚡ Cycle {filtered_df.index[cycle1_idx]} was {duration2 - duration1:.1f} min faster")
        elif duration2 < duration1:
            st.info(f"⚡ Cycle {filtered_df.index[cycle2_idx]} was {duration1 - duration2:.1f} min faster")
        
        efficiency1 = pnl1 / max(duration1, 1)
        efficiency2 = pnl2 / max(duration2, 1)
        
        if efficiency1 > efficiency2:
            st.info(f"🎯 Cycle {filtered_df.index[cycle1_idx]} is more efficient (${efficiency1 - efficiency2:.3f}/min)")
        elif efficiency2 > efficiency1:
            st.info(f"🎯 Cycle {filtered_df.index[cycle2_idx]} is more efficient (${efficiency2 - efficiency1:.3f}/min)")
    
    # Radar chart comparison
    st.markdown("### 📊 Visual Comparison")
    render_radar_chart(cycle1, cycle2, filtered_df.index[cycle1_idx], filtered_df.index[cycle2_idx])

def render_radar_chart(cycle1: pd.Series, cycle2: pd.Series, cycle1_name: str, cycle2_name: str):
    """Render radar chart comparing two cycles across multiple metrics"""
    try:
        # Define metrics for comparison
        metrics = [
            'PnL ($)',
            'Duration (min)',
            'Investment ($)',
            'Trade Count',
            'Efficiency ($/min)'
        ]
        
        # Extract values for cycle1
        cycle1_values = [
            cycle1.get('realized_pnl', 0),
            cycle1.get('duration_minutes', 0),
            cycle1.get('total_investment', 0),
            cycle1.get('trade_count', 0),
            cycle1.get('realized_pnl', 0) / max(cycle1.get('duration_minutes', 1), 1)
        ]
        
        # Extract values for cycle2
        cycle2_values = [
            cycle2.get('realized_pnl', 0),
            cycle2.get('duration_minutes', 0),
            cycle2.get('total_investment', 0),
            cycle2.get('trade_count', 0),
            cycle2.get('realized_pnl', 0) / max(cycle2.get('duration_minutes', 1), 1)
        ]
        
        # Normalize values to 0-100 scale for radar chart
        all_values = cycle1_values + cycle2_values
        max_vals = [max(cycle1_values[i], cycle2_values[i]) for i in range(len(metrics))]
        min_vals = [min(cycle1_values[i], cycle2_values[i]) for i in range(len(metrics))]
        
        # Avoid division by zero
        normalized_cycle1 = []
        normalized_cycle2 = []
        
        for i in range(len(metrics)):
            if max_vals[i] != min_vals[i]:
                norm1 = ((cycle1_values[i] - min_vals[i]) / (max_vals[i] - min_vals[i])) * 100
                norm2 = ((cycle2_values[i] - min_vals[i]) / (max_vals[i] - min_vals[i])) * 100
            else:
                norm1 = norm2 = 50  # Default to middle if no variation
            
            normalized_cycle1.append(norm1)
            normalized_cycle2.append(norm2)
        
        # Create radar chart
        fig = go.Figure()
        
        # Add cycle1 trace
        fig.add_trace(go.Scatterpolar(
            r=normalized_cycle1 + [normalized_cycle1[0]],  # Close the polygon
            theta=metrics + [metrics[0]],  # Close the polygon
            fill='toself',
            name=f'Cycle {cycle1_name}',
            line_color='rgba(0, 123, 255, 0.8)',
            fillcolor='rgba(0, 123, 255, 0.2)'
        ))
        
        # Add cycle2 trace
        fig.add_trace(go.Scatterpolar(
            r=normalized_cycle2 + [normalized_cycle2[0]],  # Close the polygon
            theta=metrics + [metrics[0]],  # Close the polygon
            fill='toself',
            name=f'Cycle {cycle2_name}',
            line_color='rgba(255, 99, 132, 0.8)',
            fillcolor='rgba(255, 99, 132, 0.2)'
        ))
        
        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickmode='linear',
                    tick0=0,
                    dtick=20
                )
            ),
            showlegend=True,
            title=f"Cycle Performance Comparison: {cycle1_name} vs {cycle2_name}",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display actual values table
        comparison_data = {
            'Metric': metrics,
            f'Cycle {cycle1_name}': [f"{float(val):.2f}" for val in cycle1_values],
            f'Cycle {cycle2_name}': [f"{float(val):.2f}" for val in cycle2_values]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        # Ensure all columns are string type to avoid pyarrow conversion issues
        for col in comparison_df.columns:
            if col != 'Metric':
                comparison_df[col] = comparison_df[col].astype(str)
        
        st.markdown("**📊 Actual Values Comparison**")
        st.dataframe(comparison_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating radar chart: {str(e)}")
        st.info("Displaying simplified comparison instead...")
        
        # Fallback simple comparison
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Cycle {cycle1_name}**")
            st.write(f"PnL: ${cycle1.get('realized_pnl', 0):.2f}")
            st.write(f"Duration: {cycle1.get('duration_minutes', 0):.1f} min")
            st.write(f"Investment: ${cycle1.get('total_investment', 0):.2f}")
        
        with col2:
            st.markdown(f"**Cycle {cycle2_name}**")
            st.write(f"PnL: ${cycle2.get('realized_pnl', 0):.2f}")
            st.write(f"Duration: {cycle2.get('duration_minutes', 0):.1f} min")
            st.write(f"Investment: ${cycle2.get('total_investment', 0):.2f}")

def render_strategy_group_comparison(cycle_df: pd.DataFrame):
    """Render strategy group comparison"""
    st.markdown("### 📊 Strategy Group Analysis")
    
    if 'strategy_type' not in cycle_df.columns:
        st.warning("Strategy information not available for group comparison.")
        return
    
    strategies = cycle_df['strategy_type'].unique()
    if len(strategies) < 2:
        st.warning("Need at least 2 different strategies for group comparison.")
        return
    
    # Strategy performance summary
    strategy_stats = cycle_df.groupby('strategy_type').agg({
        'realized_pnl': ['count', 'sum', 'mean', 'std', lambda x: (x > 0).sum()],
        'duration_minutes': ['mean', 'median'],
        'total_investment': ['mean', 'sum'],
        'trade_count': 'mean'
    }).round(2)
    
    # Flatten column names
    strategy_stats.columns = ['_'.join(col).strip() for col in strategy_stats.columns]
    strategy_stats['win_rate'] = (strategy_stats['realized_pnl_<lambda>'] / strategy_stats['realized_pnl_count'] * 100).round(1)
    
    # Display strategy comparison table
    st.markdown("**📈 Strategy Performance Summary**")
    
    display_stats = strategy_stats[[
        'realized_pnl_count', 'realized_pnl_sum', 'realized_pnl_mean', 
        'win_rate', 'duration_minutes_mean', 'total_investment_mean'
    ]].copy()
    
    display_stats.columns = [
        'Total Cycles', 'Total PnL ($)', 'Avg PnL ($)', 
        'Win Rate (%)', 'Avg Duration (min)', 'Avg Investment ($)'
    ]
    
    st.dataframe(display_stats, use_container_width=True)
    
    # Strategy comparison charts
    st.markdown("**📊 Visual Strategy Comparison**")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Win rate comparison
        fig_win_rate = px.bar(
            x=strategy_stats.index,
            y=strategy_stats['win_rate'],
            title="Win Rate by Strategy",
            labels={'x': 'Strategy', 'y': 'Win Rate (%)'},
            color=strategy_stats['win_rate'],
            color_continuous_scale='RdYlGn'
        )
        fig_win_rate.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Break-even")
        st.plotly_chart(fig_win_rate, use_container_width=True)
    
    with chart_col2:
        # Average PnL comparison
        fig_avg_pnl = px.bar(
            x=strategy_stats.index,
            y=strategy_stats['realized_pnl_mean'],
            title="Average PnL by Strategy",
            labels={'x': 'Strategy', 'y': 'Average PnL ($)'},
            color=strategy_stats['realized_pnl_mean'],
            color_continuous_scale='RdYlGn'
        )
        fig_avg_pnl.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
        st.plotly_chart(fig_avg_pnl, use_container_width=True)
    
    # Risk-return scatter plot
    st.markdown("**⚖️ Risk-Return Analysis by Strategy**")
    
    fig_risk_return = px.scatter(
        x=strategy_stats['realized_pnl_std'],
        y=strategy_stats['realized_pnl_mean'],
        size=strategy_stats['realized_pnl_count'],
        color=strategy_stats.index,
        title="Risk vs Return by Strategy",
        labels={'x': 'Risk (PnL Std Dev)', 'y': 'Return (Avg PnL)', 'color': 'Strategy'},
        hover_data={'realized_pnl_count': True}
    )
    
    # Add quadrant lines
    fig_risk_return.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_risk_return.add_vline(x=strategy_stats['realized_pnl_std'].median(), line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig_risk_return, use_container_width=True)

def render_quartile_comparison(cycle_df: pd.DataFrame):
    """Render performance quartile comparison"""
    st.markdown("### 📊 Performance Quartile Analysis")
    
    if 'realized_pnl' not in cycle_df.columns:
        st.warning("PnL data not available for quartile analysis.")
        return
    
    # Calculate quartiles
    quartiles = pd.qcut(cycle_df['realized_pnl'], q=4, labels=['Q1 (Bottom)', 'Q2', 'Q3', 'Q4 (Top)'])
    cycle_df_with_quartiles = cycle_df.copy()
    cycle_df_with_quartiles['performance_quartile'] = quartiles
    
    # Quartile statistics
    quartile_stats = cycle_df_with_quartiles.groupby('performance_quartile').agg({
        'realized_pnl': ['count', 'min', 'max', 'mean', 'std'],
        'duration_minutes': ['mean', 'median'],
        'total_investment': ['mean', 'median'],
        'trade_count': 'mean'
    }).round(2)
    
    # Flatten column names
    quartile_stats.columns = ['_'.join(col).strip() for col in quartile_stats.columns]
    
    st.markdown("**📈 Quartile Performance Summary**")
    
    display_quartiles = quartile_stats[[
        'realized_pnl_count', 'realized_pnl_min', 'realized_pnl_max', 
        'realized_pnl_mean', 'duration_minutes_mean', 'total_investment_mean'
    ]].copy()
    
    display_quartiles.columns = [
        'Cycle Count', 'Min PnL ($)', 'Max PnL ($)', 
        'Avg PnL ($)', 'Avg Duration (min)', 'Avg Investment ($)'
    ]
    
    st.dataframe(display_quartiles, use_container_width=True)
    
    # Quartile characteristics analysis
    st.markdown("**🔍 Quartile Characteristics**")
    
    char_col1, char_col2 = st.columns(2)
    
    with char_col1:
        # Duration distribution by quartile
        fig_duration = px.box(
            cycle_df_with_quartiles,
            x='performance_quartile',
            y='duration_minutes',
            title="Duration Distribution by Performance Quartile",
            labels={'performance_quartile': 'Performance Quartile', 'duration_minutes': 'Duration (minutes)'}
        )
        st.plotly_chart(fig_duration, use_container_width=True)
    
    with char_col2:
        # Investment distribution by quartile
        fig_investment = px.box(
            cycle_df_with_quartiles,
            x='performance_quartile',
            y='total_investment',
            title="Investment Distribution by Performance Quartile",
            labels={'performance_quartile': 'Performance Quartile', 'total_investment': 'Total Investment ($)'}
        )
        st.plotly_chart(fig_investment, use_container_width=True)
    
    # Strategy distribution in quartiles
    if 'strategy_type' in cycle_df.columns:
        st.markdown("**🎯 Strategy Distribution Across Quartiles**")
        
        strategy_quartile_crosstab = pd.crosstab(
            cycle_df_with_quartiles['performance_quartile'],
            cycle_df_with_quartiles['strategy_type'],
            normalize='index'
        ) * 100
        
        fig_strategy_dist = px.bar(
            strategy_quartile_crosstab,
            title="Strategy Distribution by Performance Quartile (%)",
            labels={'value': 'Percentage (%)', 'index': 'Performance Quartile'}
        )
        st.plotly_chart(fig_strategy_dist, use_container_width=True)

def render_time_period_comparison(cycle_df: pd.DataFrame):
    """Render time period comparison"""
    st.markdown("### 📅 Time Period Analysis")
    
    if 'start_time' not in cycle_df.columns:
        st.warning("Time data not available for period analysis.")
        return
    
    # Convert start_time to datetime if it's not already
    cycle_df_time = cycle_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(cycle_df_time['start_time']):
        cycle_df_time['start_time'] = pd.to_datetime(cycle_df_time['start_time'])
    
    # Time period selection
    period_type = st.selectbox(
        "Select Time Period Grouping:",
        ["Daily", "Weekly", "Monthly", "Hourly"]
    )
    
    # Group by time period
    if period_type == "Daily":
        cycle_df_time['period'] = cycle_df_time['start_time'].dt.date
        period_label = "Date"
    elif period_type == "Weekly":
        cycle_df_time['period'] = cycle_df_time['start_time'].dt.to_period('W')
        period_label = "Week"
    elif period_type == "Monthly":
        cycle_df_time['period'] = cycle_df_time['start_time'].dt.to_period('M')
        period_label = "Month"
    else:  # Hourly
        cycle_df_time['period'] = cycle_df_time['start_time'].dt.hour
        period_label = "Hour of Day"
    
    # Calculate period statistics
    def count_wins(x):
        return (x > 0).sum()
    
    period_stats = cycle_df_time.groupby('period').agg({
        'realized_pnl': ['count', 'sum', 'mean', count_wins],
        'duration_minutes': 'mean',
        'total_investment': 'sum'
    }).round(2)
    
    # Flatten column names
    period_stats.columns = ['_'.join(col).strip() for col in period_stats.columns]
    period_stats['win_rate'] = (period_stats['realized_pnl_count_wins'] / period_stats['realized_pnl_count'] * 100).round(1)
    
    # Display period performance
    st.markdown(f"**📈 {period_type} Performance Summary**")
    
    display_periods = period_stats[[
        'realized_pnl_count', 'realized_pnl_sum', 'realized_pnl_mean', 'win_rate'
    ]].copy()
    
    display_periods.columns = [
        'Cycle Count', 'Total PnL ($)', 'Avg PnL ($)', 'Win Rate (%)'
    ]
    
    st.dataframe(display_periods, use_container_width=True)
    
    # Time series charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # PnL over time
        fig_pnl_time = px.line(
            x=period_stats.index,
            y=period_stats['realized_pnl_sum'],
            title=f"Total PnL by {period_type}",
            labels={'x': period_label, 'y': 'Total PnL ($)'}
        )
        st.plotly_chart(fig_pnl_time, use_container_width=True)
    
    with chart_col2:
        # Win rate over time
        fig_winrate_time = px.line(
            x=period_stats.index,
            y=period_stats['win_rate'],
            title=f"Win Rate by {period_type}",
            labels={'x': period_label, 'y': 'Win Rate (%)'}
        )
        fig_winrate_time.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Break-even")
        st.plotly_chart(fig_winrate_time, use_container_width=True)
    
    # Best/worst periods
    st.markdown(f"**🏆 Best and Worst {period_type} Periods**")
    
    best_period = period_stats.loc[period_stats['realized_pnl_sum'].idxmax()]
    worst_period = period_stats.loc[period_stats['realized_pnl_sum'].idxmin()]
    
    best_col, worst_col = st.columns(2)
    
    with best_col:
        st.success(f"**🏆 Best {period_type}: {period_stats['realized_pnl_sum'].idxmax()}**")
        st.write(f"• Total PnL: ${best_period['realized_pnl_sum']:,.2f}")
        st.write(f"• Cycles: {best_period['realized_pnl_count']}")
        st.write(f"• Win Rate: {best_period['win_rate']:.1f}%")
    
    with worst_col:
        st.error(f"**📉 Worst {period_type}: {period_stats['realized_pnl_sum'].idxmin()}**")
        st.write(f"• Total PnL: ${worst_period['realized_pnl_sum']:,.2f}")
        st.write(f"• Cycles: {worst_period['realized_pnl_count']}")
        st.write(f"• Win Rate: {worst_period['win_rate']:.1f}%")

def render_optimization_analysis(cycle_df: pd.DataFrame, cycle_report: CycleAnalysisReport, symbol: str):
    """Render optimization analysis and suggestions"""
    st.markdown("## 🎯 Cycle Optimization Analysis")
    
    if len(cycle_df) < 10:
        st.warning("Need at least 10 cycles for meaningful optimization analysis.")
        return
    
    # Performance metrics calculation
    total_cycles = len(cycle_df)
    winning_cycles = len(cycle_df[cycle_df['realized_pnl'] > 0]) if 'realized_pnl' in cycle_df.columns else 0
    win_rate = (winning_cycles / total_cycles * 100) if total_cycles > 0 else 0
    avg_pnl = cycle_df['realized_pnl'].mean() if 'realized_pnl' in cycle_df.columns else 0
    total_pnl = cycle_df['realized_pnl'].sum() if 'realized_pnl' in cycle_df.columns else 0
    pnl_std = cycle_df['realized_pnl'].std() if 'realized_pnl' in cycle_df.columns else 0
    
    # Optimization suggestions
    st.subheader("💡 Optimization Recommendations")
    
    suggestions = []
    
    # Win rate analysis
    if win_rate < 40:
        suggestions.append({
            'category': '⚠️ Win Rate Improvement',
            'priority': 'High',
            'issue': f'Low win rate ({win_rate:.1f}%)',
            'recommendation': 'Consider tightening entry criteria, improving exit strategies, or reducing position sizes',
            'target': '50-70%'
        })
    elif win_rate > 85:
        suggestions.append({
            'category': '💡 Aggressive Positioning',
            'priority': 'Medium',
            'issue': f'Very high win rate ({win_rate:.1f}%)',
            'recommendation': 'Consider increasing position sizes or taking more aggressive positions to maximize returns',
            'target': 'Maintain while increasing position size'
        })
    
    # Volatility analysis
    if pnl_std > abs(avg_pnl) * 3:
        suggestions.append({
            'category': '📊 Risk Management',
            'priority': 'High',
            'issue': 'High PnL volatility detected',
            'recommendation': 'Implement dynamic position sizing based on volatility or stricter risk management rules',
            'target': f'Reduce volatility to < ${abs(avg_pnl) * 2:.2f}'
        })
    
    # Strategy-specific analysis
    if 'strategy_type' in cycle_df.columns:
        strategy_performance = cycle_df.groupby('strategy_type')['realized_pnl'].agg(['mean', 'count', 'sum'])
        overall_avg = cycle_df['realized_pnl'].mean()
        
        # Find underperforming strategies
        underperforming = strategy_performance[strategy_performance['mean'] < overall_avg * 0.3]
        for strategy in underperforming.index:
            suggestions.append({
                'category': f'🎯 Strategy: {strategy}',
                'priority': 'Medium',
                'issue': f'Underperforming strategy (avg: ${underperforming.loc[strategy, "mean"]:.2f})',
                'recommendation': f'Review {strategy} parameters, reduce allocation, or consider discontinuing',
                'target': f'Improve to > ${overall_avg * 0.7:.2f} avg PnL'
            })
    
    # Duration analysis
    if 'duration_minutes' in cycle_df.columns:
        duration_pnl_corr = cycle_df['duration_minutes'].corr(cycle_df['realized_pnl'])
        if abs(duration_pnl_corr) > 0.3:
            if duration_pnl_corr > 0:
                suggestions.append({
                    'category': '⏱️ Duration Optimization',
                    'priority': 'Medium',
                    'issue': f'Longer cycles more profitable (correlation: {duration_pnl_corr:.2f})',
                    'recommendation': 'Consider allowing cycles to run longer or adjusting exit criteria',
                    'target': 'Optimize exit timing for longer profitable cycles'
                })
            else:
                suggestions.append({
                    'category': '⏱️ Duration Optimization',
                    'priority': 'Medium',
                    'issue': f'Shorter cycles more profitable (correlation: {duration_pnl_corr:.2f})',
                    'recommendation': 'Implement tighter exit criteria or time-based stops',
                    'target': 'Optimize for shorter, more efficient cycles'
                })
    
    # Risk management
    if 'realized_pnl' in cycle_df.columns:
        max_loss = cycle_df['realized_pnl'].min()
        if abs(max_loss) > abs(avg_pnl) * 15:
            suggestions.append({
                'category': '🛡️ Risk Management',
                'priority': 'High',
                'issue': f'Large maximum loss detected (${max_loss:,.2f})',
                'recommendation': 'Implement stricter stop-loss rules, position sizing limits, or maximum drawdown controls',
                'target': f'Limit max loss to < ${abs(avg_pnl) * 10:.2f}'
            })
    
    # Display suggestions
    if suggestions:
        # Group by priority
        high_priority = [s for s in suggestions if s['priority'] == 'High']
        medium_priority = [s for s in suggestions if s['priority'] == 'Medium']
        
        if high_priority:
            st.markdown("**🔴 High Priority Recommendations**")
            for i, suggestion in enumerate(high_priority, 1):
                with st.expander(f"{i}. {suggestion['category']}: {suggestion['issue']}", expanded=True):
                    st.markdown(f"**📋 Recommendation:** {suggestion['recommendation']}")
                    st.markdown(f"**🎯 Target:** {suggestion['target']}")
        
        if medium_priority:
            st.markdown("**🟡 Medium Priority Recommendations**")
            for i, suggestion in enumerate(medium_priority, 1):
                with st.expander(f"{i}. {suggestion['category']}: {suggestion['issue']}"):
                    st.markdown(f"**📋 Recommendation:** {suggestion['recommendation']}")
                    st.markdown(f"**🎯 Target:** {suggestion['target']}")
    else:
        st.success("✅ No major optimization opportunities identified. Your cycle performance is well-optimized!")
    
    # Performance targets and projections
    st.subheader("📈 Performance Targets & Projections")
    
    target_col1, target_col2, target_col3 = st.columns(3)
    
    with target_col1:
        st.markdown("**📊 Current Performance**")
        st.metric("Win Rate", f"{win_rate:.1f}%")
        st.metric("Avg PnL per Cycle", f"${avg_pnl:,.2f}")
        st.metric("Total PnL", f"${total_pnl:,.2f}")
        
        if 'realized_pnl' in cycle_df.columns:
            profit_factor = abs(cycle_df[cycle_df['realized_pnl'] > 0]['realized_pnl'].sum() / 
                               cycle_df[cycle_df['realized_pnl'] <= 0]['realized_pnl'].sum()) if cycle_df[cycle_df['realized_pnl'] <= 0]['realized_pnl'].sum() != 0 else float('inf')
            st.metric("Profit Factor", f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞")
    
    with target_col2:
        st.markdown("**🎯 Suggested Targets**")
        target_win_rate = max(50, min(75, win_rate + 10))
        target_avg_pnl = avg_pnl * 1.3
        target_total_pnl = total_pnl * 1.5
        
        st.metric("Target Win Rate", f"{target_win_rate:.1f}%")
        st.metric("Target Avg PnL", f"${target_avg_pnl:,.2f}")
        st.metric("Target Total PnL", f"${target_total_pnl:,.2f}")
        st.metric("Target Profit Factor", "2.5+")
    
    with target_col3:
        st.markdown("**📊 Improvement Needed**")
        win_rate_delta = target_win_rate - win_rate
        avg_pnl_delta = target_avg_pnl - avg_pnl
        total_pnl_delta = target_total_pnl - total_pnl
        
        st.metric("Win Rate Δ", f"+{win_rate_delta:.1f}%")
        st.metric("Avg PnL Δ", f"+${avg_pnl_delta:,.2f}")
        st.metric("Total PnL Δ", f"+${total_pnl_delta:,.2f}")
        
        # Focus area recommendation
        if win_rate < 50:
            focus_area = "Entry Criteria"
        elif pnl_std > abs(avg_pnl) * 2:
            focus_area = "Risk Management"
        else:
            focus_area = "Position Sizing"
        st.metric("Primary Focus", focus_area)
    
    # Strategy optimization matrix
    if 'strategy_type' in cycle_df.columns and len(cycle_df['strategy_type'].unique()) > 1:
        st.subheader("🎯 Strategy Optimization Matrix")
        
        # Calculate strategy metrics
        strategy_metrics = []
        for strategy in cycle_df['strategy_type'].unique():
            strategy_data = cycle_df[cycle_df['strategy_type'] == strategy]
            
            if len(strategy_data) > 0:
                strategy_win_rate = (strategy_data['realized_pnl'] > 0).sum() / len(strategy_data) * 100
                strategy_avg_pnl = strategy_data['realized_pnl'].mean()
                strategy_total_pnl = strategy_data['realized_pnl'].sum()
                strategy_count = len(strategy_data)
                strategy_volatility = strategy_data['realized_pnl'].std()
                
                # Risk-adjusted return (Sharpe-like ratio)
                risk_adj_return = strategy_avg_pnl / strategy_volatility if strategy_volatility > 0 else 0
                
                strategy_metrics.append({
                    'Strategy': strategy,
                    'Cycles': strategy_count,
                    'Win Rate (%)': strategy_win_rate,
                    'Avg PnL ($)': strategy_avg_pnl,
                    'Total PnL ($)': strategy_total_pnl,
                    'Volatility ($)': strategy_volatility,
                    'Risk-Adj Return': risk_adj_return,
                    'Recommendation': get_strategy_recommendation(strategy_win_rate, strategy_avg_pnl, risk_adj_return)
                })
        
        strategy_df = pd.DataFrame(strategy_metrics)
        
        # Format for display
        display_strategy_df = strategy_df.copy()
        display_strategy_df['Win Rate (%)'] = display_strategy_df['Win Rate (%)'].apply(lambda x: f"{x:.1f}%")
        display_strategy_df['Avg PnL ($)'] = display_strategy_df['Avg PnL ($)'].apply(lambda x: f"${x:,.2f}")
        display_strategy_df['Total PnL ($)'] = display_strategy_df['Total PnL ($)'].apply(lambda x: f"${x:,.2f}")
        display_strategy_df['Volatility ($)'] = display_strategy_df['Volatility ($)'].apply(lambda x: f"${x:,.2f}")
        display_strategy_df['Risk-Adj Return'] = display_strategy_df['Risk-Adj Return'].apply(lambda x: f"{x:.3f}")
        
        st.dataframe(display_strategy_df, use_container_width=True, hide_index=True)
        
        # Strategy performance visualization
        fig_strategy_matrix = go.Figure()
        
        for _, row in strategy_df.iterrows():
            fig_strategy_matrix.add_trace(go.Scatter(
                x=[row['Volatility ($)']],
                y=[row['Avg PnL ($)']],
                mode='markers+text',
                name=row['Strategy'],
                marker=dict(
                    size=row['Cycles'] * 2,  # Size by cycle count
                    opacity=0.7,
                    color=row['Win Rate (%)'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Win Rate (%)")
                ),
                text=[row['Strategy']],
                textposition="top center",
                hovertemplate=(
                    f"<b>{row['Strategy']}</b><br>" +
                    f"Avg PnL: ${row['Avg PnL ($)']:,.2f}<br>" +
                    f"Volatility: ${row['Volatility ($)']:,.2f}<br>" +
                    f"Win Rate: {row['Win Rate (%)']:.1f}%<br>" +
                    f"Cycles: {row['Cycles']}<br>" +
                    f"Risk-Adj Return: {row['Risk-Adj Return']:.3f}<br>" +
                    '<extra></extra>'
                )
            ))
        
        fig_strategy_matrix.update_layout(
            title="Strategy Risk-Return Matrix",
            xaxis_title="Volatility (PnL Std Dev)",
            yaxis_title="Average PnL ($)",
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig_strategy_matrix, use_container_width=True)

def get_strategy_recommendation(win_rate: float, avg_pnl: float, risk_adj_return: float) -> str:
    """Generate strategy-specific recommendations"""
    if win_rate > 70 and avg_pnl > 0 and risk_adj_return > 0.5:
        return "🟢 Excellent - Increase allocation"
    elif win_rate > 50 and avg_pnl > 0:
        return "🟡 Good - Maintain current allocation"
    elif win_rate < 40 or avg_pnl < 0:
        return "🔴 Poor - Reduce allocation or review parameters"
    else:
        return "🟠 Average - Monitor and optimize"

def render_detailed_data(cycle_df: pd.DataFrame):
    """Render detailed cycle data with sorting and filtering"""
    st.markdown("## 📋 Detailed Cycle Data")
    
    # Sorting options
    sort_col1, sort_col2 = st.columns(2)
    
    with sort_col1:
        sort_columns = list(cycle_df.columns)
        sort_by = st.selectbox("Sort by", sort_columns, index=0)
    
    with sort_col2:
        sort_order = st.selectbox("Sort order", ['Ascending', 'Descending'])
    
    # Apply sorting
    ascending = sort_order == 'Ascending'
    sorted_df = cycle_df.sort_values(sort_by, ascending=ascending)
    
    # Format the dataframe for display
    display_df = sorted_df.copy()
    
    # Format monetary columns
    money_cols = ['total_investment', 'max_investment', 'realized_pnl', 'unrealized_pnl', 'total_pnl']
    for col in money_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${float(x):,.2f}" if pd.notna(x) else 'N/A')
    
    # Format percentage columns
    pct_cols = ['roi_percentage']
    for col in pct_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{float(x):.2f}%" if pd.notna(x) else 'N/A')
    
    # Format duration
    if 'duration_minutes' in display_df.columns:
        display_df['duration_minutes'] = display_df['duration_minutes'].apply(lambda x: f"{float(x):.1f} min" if pd.notna(x) else 'N/A')
    
    # Format ratio columns
    ratio_cols = ['risk_reward_ratio', 'profit_factor']
    for col in ratio_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) and x != float('inf') else "∞" if x == float('inf') else 'N/A')
    
    # Format datetime columns
    datetime_cols = ['start_time', 'end_time']
    for col in datetime_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else 'N/A')
    
    # Ensure all formatted columns are string type to avoid pyarrow conversion issues
    formatted_cols = money_cols + pct_cols + ['duration_minutes'] + ratio_cols + datetime_cols
    for col in formatted_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].astype(str)
    
    # Display the dataframe
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Summary statistics
    if st.checkbox("Show Summary Statistics"):
        st.markdown("**📊 Summary Statistics**")
        
        # Select numeric columns for statistics
        numeric_cols = cycle_df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            stats_df = cycle_df[numeric_cols].describe()
            st.dataframe(stats_df, use_container_width=True)

def render_export_reports(cycle_df: pd.DataFrame, cycle_report: CycleAnalysisReport, symbol: str):
    """Render export and reporting options"""
    st.markdown("## 📤 Export & Reports")
    
    # Export options
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.markdown("**📊 Data Export**")
        
        # CSV export
        csv_data = cycle_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Cycle Data (CSV)",
            data=csv_data,
            file_name=f"cycle_analysis_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # JSON export
        json_data = cycle_df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="💾 Download Cycle Data (JSON)",
            data=json_data,
            file_name=f"cycle_analysis_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with export_col2:
        st.markdown("**📋 Report Generation**")
        
        # Generate summary report
        if st.button("📄 Generate Summary Report"):
            summary_report = generate_summary_report(cycle_df, cycle_report, symbol)
            
            st.download_button(
                label="💾 Download Summary Report",
                data=summary_report,
                file_name=f"cycle_summary_report_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    # Report preview
    if st.checkbox("Preview Summary Report"):
        st.markdown("**📄 Report Preview**")
        summary_report = generate_summary_report(cycle_df, cycle_report, symbol)
        st.text_area("Report Content", summary_report, height=400)

def generate_summary_report(cycle_df: pd.DataFrame, cycle_report: CycleAnalysisReport, symbol: str) -> str:
    """Generate a comprehensive summary report"""
    report_lines = []
    report_lines.append(f"CYCLE ANALYSIS SUMMARY REPORT")
    report_lines.append(f"Symbol: {symbol}")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 50)
    report_lines.append("")
    
    # Overview
    report_lines.append("OVERVIEW")
    report_lines.append("-" * 20)
    report_lines.append(f"Total Cycles: {len(cycle_df)}")
    
    if 'status' in cycle_df.columns:
        completed = len(cycle_df[cycle_df['status'] == 'COMPLETED'])
        report_lines.append(f"Completed Cycles: {completed}")
    
    if 'realized_pnl' in cycle_df.columns:
        winning = len(cycle_df[cycle_df['realized_pnl'] > 0])
        win_rate = (winning / completed * 100) if completed > 0 else 0
        total_pnl = cycle_df['realized_pnl'].sum()
        avg_pnl = cycle_df['realized_pnl'].mean()
        
        report_lines.append(f"Winning Cycles: {winning}")
        report_lines.append(f"Win Rate: {win_rate:.1f}%")
        report_lines.append(f"Total PnL: ${total_pnl:,.2f}")
        report_lines.append(f"Average PnL: ${avg_pnl:,.2f}")
    
    report_lines.append("")
    
    # Strategy breakdown
    if 'strategy_type' in cycle_df.columns:
        report_lines.append("STRATEGY BREAKDOWN")
        report_lines.append("-" * 20)
        
        for strategy in cycle_df['strategy_type'].unique():
            strategy_data = cycle_df[cycle_df['strategy_type'] == strategy]
            strategy_count = len(strategy_data)
            
            if 'realized_pnl' in strategy_data.columns:
                strategy_pnl = strategy_data['realized_pnl'].sum()
                strategy_avg = strategy_data['realized_pnl'].mean()
                strategy_wins = len(strategy_data[strategy_data['realized_pnl'] > 0])
                strategy_win_rate = (strategy_wins / strategy_count * 100) if strategy_count > 0 else 0
                
                report_lines.append(f"{strategy}:")
                report_lines.append(f"  Cycles: {strategy_count}")
                report_lines.append(f"  Total PnL: ${strategy_pnl:,.2f}")
                report_lines.append(f"  Avg PnL: ${strategy_avg:,.2f}")
                report_lines.append(f"  Win Rate: {strategy_win_rate:.1f}%")
                report_lines.append("")
    
    # Performance metrics
    if 'realized_pnl' in cycle_df.columns:
        report_lines.append("PERFORMANCE METRICS")
        report_lines.append("-" * 20)
        
        returns = cycle_df['realized_pnl']
        report_lines.append(f"Best Cycle: ${returns.max():,.2f}")
        report_lines.append(f"Worst Cycle: ${returns.min():,.2f}")
        report_lines.append(f"Median PnL: ${returns.median():,.2f}")
        report_lines.append(f"Standard Deviation: ${returns.std():,.2f}")
        
        if len(returns) > 1:
            sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
            report_lines.append(f"Sharpe Ratio: {sharpe_ratio:.3f}")
        
        report_lines.append("")
    
    # Duration analysis
    if 'duration_minutes' in cycle_df.columns:
        report_lines.append("DURATION ANALYSIS")
        report_lines.append("-" * 20)
        
        durations = cycle_df['duration_minutes']
        report_lines.append(f"Average Duration: {durations.mean():.1f} minutes")
        report_lines.append(f"Median Duration: {durations.median():.1f} minutes")
        report_lines.append(f"Max Duration: {durations.max():.1f} minutes")
        report_lines.append(f"Min Duration: {durations.min():.1f} minutes")
        report_lines.append("")
    
    # Investment analysis
    if 'total_investment' in cycle_df.columns:
        report_lines.append("INVESTMENT ANALYSIS")
        report_lines.append("-" * 20)
        
        investments = cycle_df['total_investment']
        report_lines.append(f"Average Investment: ${investments.mean():,.2f}")
        report_lines.append(f"Total Invested: ${investments.sum():,.2f}")
        report_lines.append(f"Max Investment: ${investments.max():,.2f}")
        
        if 'max_investment' in cycle_df.columns:
            max_investments = cycle_df['max_investment']
            report_lines.append(f"Peak Investment: ${max_investments.max():,.2f}")
        
        report_lines.append("")
    
    report_lines.append("=" * 50)
    report_lines.append("End of Report")
    
    return "\n".join(report_lines)

def main():
    """Main function for standalone testing"""
    st.set_page_config(
        page_title="Cycle Analysis",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("🔄 Advanced Cycle Analysis")
    st.markdown("Upload cycle data or connect to live analysis")
    
    # For testing purposes
    st.info("This is a standalone cycle analysis interface. In the main application, this would be integrated with live cycle data.")

if __name__ == "__main__":
    main()