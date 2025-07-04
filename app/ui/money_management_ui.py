import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_money_management import (
    AdvancedMoneyManager, PositionSizingMethod, RiskLevel,
    PositionSizingConfig, PerformanceMetrics, RiskMetrics
)
from config import TradingConfig, StrategyType
from cycle_analysis import CycleAnalysisReport

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

def render_money_management_dashboard(config: TradingConfig, money_manager: AdvancedMoneyManager):
    """Render the advanced money management dashboard"""
    render_title_with_tooltip(
        "💰 Advanced Money Management", 
        "Comprehensive money management system with dynamic position sizing, risk monitoring, and portfolio optimization tools",
        "header"
    )
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Position Sizing", "Risk Monitoring", "Performance Analysis", 
        "Portfolio Heat Map", "Configuration"
    ])
    
    with tab1:
        render_position_sizing_section(config, money_manager)
    
    with tab2:
        render_risk_monitoring_section(money_manager)
    
    with tab3:
        render_performance_analysis_section(money_manager)
    
    with tab4:
        render_portfolio_heat_map(money_manager)
    
    with tab5:
        render_money_management_config(money_manager)

def render_position_sizing_section(config: TradingConfig, money_manager: AdvancedMoneyManager):
    """Render position sizing analysis and calculator"""
    render_title_with_tooltip(
        "📊 Dynamic Position Sizing", 
        "Calculate optimal position sizes using various methods including volatility adjustment, performance-based sizing, and Kelly criterion"
    )
    
    # Position sizing calculator
    col1, col2 = st.columns(2)
    
    with col1:
        render_title_with_tooltip(
            "Position Size Calculator", 
            "Interactive calculator to determine optimal position size for a specific symbol and strategy",
            "markdown"
        )
        
        # Input parameters
        strategy = st.selectbox(
            "Strategy",
            options=[s.value for s in StrategyType],
            key="pos_sizing_strategy"
        )
        
        symbol = st.text_input("Symbol", value="AAPL", key="pos_sizing_symbol")
        account_balance = st.number_input(
            "Account Balance ($)", 
            min_value=1000.0, 
            value=100000.0, 
            step=1000.0,
            key="pos_sizing_balance"
        )
        symbol_price = st.number_input(
            "Symbol Price ($)", 
            min_value=0.01, 
            value=150.0, 
            step=0.01,
            key="pos_sizing_price"
        )
        
        if st.button("Calculate Position Size", key="calc_pos_size"):
            try:
                strategy_type = StrategyType(strategy.lower())
                position_size = money_manager.calculate_dynamic_position_size(
                    strategy_type, symbol, account_balance, symbol_price
                )
                
                # Display results
                st.success(f"**Recommended Position Size: {position_size:.2f} shares**")
                st.info(f"**Dollar Amount: ${position_size * symbol_price:,.2f}**")
                st.info(f"**Portfolio Allocation: {(position_size * symbol_price / account_balance) * 100:.2f}%**")
                
            except Exception as e:
                st.error(f"Error calculating position size: {e}")
    
    with col2:
        render_title_with_tooltip(
            "Position Sizing Methods Comparison", 
            "Compare different position sizing methods side-by-side to see how each approach affects allocation",
            "markdown"
        )
        
        # Compare different sizing methods
        if st.button("Compare Sizing Methods", key="compare_methods"):
            try:
                strategy_type = StrategyType(strategy.lower())
                methods_comparison = {}
                
                for method in PositionSizingMethod:
                    # Temporarily change method
                    original_method = money_manager.position_config.method
                    money_manager.position_config.method = method
                    
                    size = money_manager.calculate_dynamic_position_size(
                        strategy_type, symbol, account_balance, symbol_price
                    )
                    
                    methods_comparison[method.value] = {
                        'shares': size,
                        'dollar_amount': size * symbol_price,
                        'allocation_pct': (size * symbol_price / account_balance) * 100
                    }
                    
                    # Restore original method
                    money_manager.position_config.method = original_method
                
                # Display comparison table
                comparison_df = pd.DataFrame(methods_comparison).T
                comparison_df.columns = ['Shares', 'Dollar Amount', 'Allocation %']
                comparison_df['Dollar Amount'] = comparison_df['Dollar Amount'].apply(lambda x: f"${x:,.2f}")
                comparison_df['Allocation %'] = comparison_df['Allocation %'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(comparison_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error comparing methods: {e}")
    
    # Strategy-specific position sizing recommendations
    render_title_with_tooltip(
        "Strategy-Specific Recommendations", 
        "Recommended position allocations for each trading strategy based on recent performance and risk metrics",
        "markdown"
    )
    
    strategy_cols = st.columns(len(StrategyType))
    
    for i, strategy_type in enumerate(StrategyType):
        with strategy_cols[i]:
            recommended_allocation = money_manager.get_recommended_allocation(strategy_type)
            performance = money_manager._calculate_recent_performance(strategy_type)
            
            st.metric(
                label=f"{strategy_type.value.upper()}",
                value=f"{recommended_allocation:.1%}",
                delta=f"Win Rate: {performance.win_rate:.1%}" if performance.win_rate > 0 else "No Data"
            )

def render_risk_monitoring_section(money_manager: AdvancedMoneyManager):
    """Render risk monitoring dashboard"""
    render_title_with_tooltip(
        "⚠️ Risk Monitoring Dashboard", 
        "Real-time monitoring of portfolio risk metrics including heat, correlation, VaR, and drawdown levels"
    )
    
    # Get risk summary
    risk_summary = money_manager.get_risk_summary()
    
    # Risk level indicator
    risk_level = risk_summary.get('risk_level', RiskLevel.CONSERVATIVE)
    risk_colors = {
        RiskLevel.CONSERVATIVE: "green",
        RiskLevel.MODERATE: "yellow", 
        RiskLevel.AGGRESSIVE: "orange",
        RiskLevel.VERY_AGGRESSIVE: "red"
    }
    
    render_title_with_tooltip(
        f"Current Risk Level: {risk_level.value.upper()}", 
        "Overall portfolio risk assessment based on multiple risk factors and thresholds",
        "markdown"
    )
    
    # Risk metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        portfolio_heat = risk_summary.get('portfolio_heat', 0)
        heat_color = "red" if portfolio_heat > 15 else "orange" if portfolio_heat > 10 else "green"
        st.metric(
            "Portfolio Heat",
            f"{portfolio_heat:.1f}%",
            delta="High Risk" if portfolio_heat > 15 else "Normal",
            delta_color="inverse" if portfolio_heat > 15 else "normal"
        )
    
    with col2:
        correlation_risk = risk_summary.get('correlation_risk', 0)
        corr_color = "red" if correlation_risk > 0.8 else "orange" if correlation_risk > 0.6 else "green"
        st.metric(
            "Correlation Risk",
            f"{correlation_risk:.2f}",
            delta="High Correlation" if correlation_risk > 0.8 else "Normal",
            delta_color="inverse" if correlation_risk > 0.8 else "normal"
        )
    
    with col3:
        var_95 = risk_summary.get('var_95', 0)
        st.metric(
            "VaR 95%",
            f"{var_95:.2f}%",
            delta="High Risk" if var_95 > 5 else "Normal",
            delta_color="inverse" if var_95 > 5 else "normal"
        )
    
    with col4:
        current_drawdown = risk_summary.get('current_drawdown', 0)
        st.metric(
            "Current Drawdown",
            f"{current_drawdown:.2f}%",
            delta="High Drawdown" if current_drawdown > 10 else "Normal",
            delta_color="inverse" if current_drawdown > 10 else "normal"
        )
    
    # Risk recommendations
    if risk_summary.get('should_reduce_exposure', False):
        st.error("🚨 **RECOMMENDATION: Reduce portfolio exposure immediately!**")
        st.markdown("""
        **Risk factors detected:**
        - High portfolio heat or correlation risk
        - Significant drawdown
        - High Value at Risk
        
        **Suggested actions:**
        - Reduce position sizes by 20-30%
        - Close correlated positions
        - Implement stricter stop losses
        """)
    else:
        st.success("✅ **Portfolio risk levels are within acceptable ranges**")
    
    # Risk trend chart
    if money_manager.drawdown_history:
        render_title_with_tooltip(
            "Drawdown History", 
            "Historical portfolio drawdown showing peak-to-trough declines over time",
            "markdown"
        )
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=money_manager.drawdown_history,
            mode='lines',
            name='Drawdown %',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Drawdown Over Time",
            yaxis_title="Drawdown %",
            xaxis_title="Time Period",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_performance_analysis_section(money_manager: AdvancedMoneyManager):
    """Render performance analysis for money management"""
    render_title_with_tooltip(
        "📈 Performance Analysis", 
        "Comprehensive analysis of strategy performance, trade history, and risk-return metrics"
    )
    
    # Strategy performance comparison
    if money_manager.strategy_performance:
        render_title_with_tooltip(
            "Strategy Performance Metrics", 
            "Detailed performance statistics for each trading strategy including win rates, returns, and risk metrics",
            "markdown"
        )
        
        # Create performance dataframe
        perf_data = []
        for strategy, metrics in money_manager.strategy_performance.items():
            perf_data.append({
                'Strategy': strategy.value.upper(),
                'Win Rate': f"{metrics.win_rate:.1%}",
                'Avg Return': f"{metrics.avg_return:.2f}",
                'Volatility': f"{metrics.volatility:.2f}",
                'Sharpe Ratio': f"{metrics.sharpe_ratio:.2f}",
                'Recent Performance': f"{metrics.recent_performance:.2f}",
                'Consecutive Losses': metrics.consecutive_losses,
                'Consecutive Wins': metrics.consecutive_wins
            })
        
        if perf_data:
            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True)
            
            # Performance visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Win rate comparison
                win_rates = [float(row['Win Rate'].strip('%'))/100 for row in perf_data]
                strategies = [row['Strategy'] for row in perf_data]
                
                fig = px.bar(
                    x=strategies,
                    y=win_rates,
                    title="Win Rate by Strategy",
                    labels={'x': 'Strategy', 'y': 'Win Rate'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Risk-return scatter
                returns = [float(row['Avg Return']) for row in perf_data]
                volatilities = [float(row['Volatility']) for row in perf_data]
                
                fig = px.scatter(
                    x=volatilities,
                    y=returns,
                    text=strategies,
                    title="Risk-Return Profile",
                    labels={'x': 'Volatility (Risk)', 'y': 'Average Return'}
                )
                fig.update_traces(textposition="top center")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No performance data available yet. Start trading to see performance metrics.")
    
    # Recent trade analysis
    if money_manager.trade_history:
        render_title_with_tooltip(
            "Recent Trade Analysis", 
            "Analysis of the last 20 trades showing PnL trends and trading performance",
            "markdown"
        )
        
        recent_trades = money_manager.trade_history[-20:]  # Last 20 trades
        
        if recent_trades:
            trade_df = pd.DataFrame(recent_trades)
            
            # Trade summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_pnl = sum(trade.get('pnl', 0) for trade in recent_trades)
                st.metric("Total PnL (Last 20)", f"${total_pnl:.2f}")
            
            with col2:
                winning_trades = len([t for t in recent_trades if t.get('pnl', 0) > 0])
                win_rate = winning_trades / len(recent_trades) if recent_trades else 0
                st.metric("Win Rate", f"{win_rate:.1%}")
            
            with col3:
                avg_pnl = total_pnl / len(recent_trades) if recent_trades else 0
                st.metric("Average PnL", f"${avg_pnl:.2f}")
            
            # Trade history chart
            if 'pnl' in trade_df.columns:
                cumulative_pnl = trade_df['pnl'].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=cumulative_pnl,
                    mode='lines+markers',
                    name='Cumulative PnL',
                    line=dict(color='blue', width=2)
                ))
                
                fig.update_layout(
                    title="Cumulative PnL - Last 20 Trades",
                    yaxis_title="Cumulative PnL ($)",
                    xaxis_title="Trade Number",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)

def render_portfolio_heat_map(money_manager: AdvancedMoneyManager):
    """Render portfolio heat map visualization"""
    render_title_with_tooltip(
        "🔥 Portfolio Heat Map", 
        "Visual representation of portfolio positions showing size, PnL, and risk concentration"
    )
    
    # Simulated portfolio data for demonstration
    # In real implementation, this would come from actual positions
    sample_positions = {
        'AAPL': {'market_value': 15000, 'pnl': 1200, 'risk_score': 0.15},
        'GOOGL': {'market_value': 12000, 'pnl': -800, 'risk_score': 0.18},
        'MSFT': {'market_value': 18000, 'pnl': 2100, 'risk_score': 0.12},
        'TSLA': {'market_value': 8000, 'pnl': -1500, 'risk_score': 0.25},
        'AMZN': {'market_value': 14000, 'pnl': 900, 'risk_score': 0.16},
        'NVDA': {'market_value': 10000, 'pnl': 1800, 'risk_score': 0.22}
    }
    
    if sample_positions:
        # Calculate portfolio heat
        portfolio_heat = money_manager.calculate_portfolio_heat(sample_positions)
        
        st.metric("Current Portfolio Heat", f"{portfolio_heat:.1f}%")
        
        # Create heat map data
        symbols = list(sample_positions.keys())
        market_values = [pos['market_value'] for pos in sample_positions.values()]
        pnls = [pos['pnl'] for pos in sample_positions.values()]
        risk_scores = [pos['risk_score'] for pos in sample_positions.values()]
        
        # Position size heat map
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.treemap(
                names=symbols,
                values=market_values,
                color=pnls,
                color_continuous_scale='RdYlGn',
                title="Position Size & PnL Heat Map"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Risk score visualization
            fig = px.bar(
                x=symbols,
                y=risk_scores,
                color=risk_scores,
                color_continuous_scale='Reds',
                title="Risk Score by Position",
                labels={'y': 'Risk Score', 'x': 'Symbol'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Position details table
        render_title_with_tooltip(
            "Position Details", 
            "Detailed breakdown of each position including market value, PnL, allocation percentage, and risk assessment",
            "markdown"
        )
        
        position_data = []
        total_value = sum(market_values)
        
        for symbol, pos in sample_positions.items():
            allocation_pct = (pos['market_value'] / total_value) * 100
            position_data.append({
                'Symbol': symbol,
                'Market Value': f"${pos['market_value']:,}",
                'PnL': f"${pos['pnl']:,}",
                'Allocation %': f"{allocation_pct:.1f}%",
                'Risk Score': f"{pos['risk_score']:.2f}",
                'Risk Level': 'High' if pos['risk_score'] > 0.2 else 'Medium' if pos['risk_score'] > 0.15 else 'Low'
            })
        
        position_df = pd.DataFrame(position_data)
        st.dataframe(position_df, use_container_width=True)
        
        # Risk warnings
        high_risk_positions = [pos for pos in position_data if 'High' in pos['Risk Level']]
        if high_risk_positions:
            st.warning(f"⚠️ {len(high_risk_positions)} position(s) have high risk scores. Consider reducing exposure.")
    
    else:
        st.info("No position data available. Portfolio heat map will be displayed when positions are active.")

def render_money_management_config(money_manager: AdvancedMoneyManager):
    """Render money management configuration interface"""
    render_title_with_tooltip(
        "⚙️ Money Management Configuration", 
        "Configure position sizing methods, allocation limits, and risk parameters for automated money management"
    )
    
    # Position sizing configuration
    render_title_with_tooltip(
        "Position Sizing Settings", 
        "Configure how position sizes are calculated including method selection and allocation limits",
        "markdown"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Position sizing method
        current_method = money_manager.position_config.method.value
        new_method = st.selectbox(
            "Position Sizing Method",
            options=[method.value for method in PositionSizingMethod],
            index=[method.value for method in PositionSizingMethod].index(current_method),
            key="pos_sizing_method"
        )
        
        # Base allocation settings
        base_allocation = st.slider(
            "Base Allocation %",
            min_value=1.0,
            max_value=20.0,
            value=money_manager.position_config.base_allocation * 100,
            step=0.5,
            key="base_allocation"
        )
        
        max_allocation = st.slider(
            "Maximum Allocation %",
            min_value=5.0,
            max_value=50.0,
            value=money_manager.position_config.max_allocation * 100,
            step=1.0,
            key="max_allocation"
        )
        
        min_allocation = st.slider(
            "Minimum Allocation %",
            min_value=0.1,
            max_value=5.0,
            value=money_manager.position_config.min_allocation * 100,
            step=0.1,
            key="min_allocation"
        )
    
    with col2:
        # Advanced settings based on method
        if new_method == PositionSizingMethod.VOLATILITY_ADJUSTED.value:
            st.markdown("**Volatility Adjustment Settings**")
            
            target_volatility = st.slider(
                "Target Volatility %",
                min_value=5.0,
                max_value=30.0,
                value=money_manager.position_config.target_volatility * 100,
                step=1.0,
                key="target_volatility"
            )
            
            lookback_period = st.number_input(
                "Lookback Period (days)",
                min_value=5,
                max_value=60,
                value=money_manager.position_config.lookback_period,
                key="lookback_period"
            )
        
        elif new_method == PositionSizingMethod.PERFORMANCE_BASED.value:
            st.markdown("**Performance-Based Settings**")
            
            performance_lookback = st.number_input(
                "Performance Lookback (trades)",
                min_value=5,
                max_value=50,
                value=money_manager.position_config.performance_lookback,
                key="performance_lookback"
            )
            
            performance_multiplier = st.slider(
                "Performance Multiplier",
                min_value=1.0,
                max_value=3.0,
                value=money_manager.position_config.performance_multiplier,
                step=0.1,
                key="performance_multiplier"
            )
        
        elif new_method == PositionSizingMethod.KELLY_CRITERION.value:
            st.markdown("**Kelly Criterion Settings**")
            
            kelly_fraction = st.slider(
                "Kelly Fraction",
                min_value=0.1,
                max_value=1.0,
                value=money_manager.position_config.kelly_fraction,
                step=0.05,
                key="kelly_fraction"
            )
            
            min_edge = st.slider(
                "Minimum Edge Required",
                min_value=0.01,
                max_value=0.10,
                value=money_manager.position_config.min_edge,
                step=0.005,
                key="min_edge"
            )
    
    # Apply configuration changes
    if st.button("Apply Configuration Changes", key="apply_config"):
        try:
            # Update position sizing method
            money_manager.position_config.method = PositionSizingMethod(new_method)
            
            # Update allocation settings
            money_manager.position_config.base_allocation = base_allocation / 100
            money_manager.position_config.max_allocation = max_allocation / 100
            money_manager.position_config.min_allocation = min_allocation / 100
            
            # Update method-specific settings
            if new_method == PositionSizingMethod.VOLATILITY_ADJUSTED.value:
                money_manager.position_config.target_volatility = target_volatility / 100
                money_manager.position_config.lookback_period = lookback_period
            elif new_method == PositionSizingMethod.PERFORMANCE_BASED.value:
                money_manager.position_config.performance_lookback = performance_lookback
                money_manager.position_config.performance_multiplier = performance_multiplier
            elif new_method == PositionSizingMethod.KELLY_CRITERION.value:
                money_manager.position_config.kelly_fraction = kelly_fraction
                money_manager.position_config.min_edge = min_edge
            
            st.success("✅ Configuration updated successfully!")
            
        except Exception as e:
            st.error(f"Error updating configuration: {e}")
    
    # Configuration summary
    render_title_with_tooltip(
        "Current Configuration Summary", 
        "Overview of all current money management settings and parameters",
        "markdown"
    )
    
    config_summary = {
        'Position Sizing Method': money_manager.position_config.method.value,
        'Base Allocation': f"{money_manager.position_config.base_allocation:.1%}",
        'Max Allocation': f"{money_manager.position_config.max_allocation:.1%}",
        'Min Allocation': f"{money_manager.position_config.min_allocation:.1%}",
        'Target Volatility': f"{money_manager.position_config.target_volatility:.1%}",
        'Lookback Period': f"{money_manager.position_config.lookback_period} days",
        'Performance Lookback': f"{money_manager.position_config.performance_lookback} trades",
        'Kelly Fraction': f"{money_manager.position_config.kelly_fraction:.2f}"
    }
    
    config_df = pd.DataFrame(list(config_summary.items()), columns=['Setting', 'Value'])
    st.dataframe(config_df, use_container_width=True, hide_index=True)

def render_money_management_alerts(money_manager: AdvancedMoneyManager):
    """Render money management alerts and notifications"""
    risk_summary = money_manager.get_risk_summary()
    
    alerts = []
    
    # Check for various risk conditions
    if risk_summary.get('portfolio_heat', 0) > 20:
        alerts.append({
            'type': 'error',
            'message': f"🚨 Portfolio heat is {risk_summary['portfolio_heat']:.1f}% - Consider reducing exposure"
        })
    
    if risk_summary.get('correlation_risk', 0) > 0.8:
        alerts.append({
            'type': 'warning',
            'message': f"⚠️ High correlation risk detected ({risk_summary['correlation_risk']:.2f}) - Diversify positions"
        })
    
    if risk_summary.get('current_drawdown', 0) > 15:
        alerts.append({
            'type': 'error',
            'message': f"🚨 High drawdown detected ({risk_summary['current_drawdown']:.1f}%) - Review risk management"
        })
    
    # Display alerts
    for alert in alerts:
        if alert['type'] == 'error':
            st.error(alert['message'])
        elif alert['type'] == 'warning':
            st.warning(alert['message'])
        else:
            st.info(alert['message'])
    
    if not alerts:
        st.success("✅ All risk metrics are within acceptable ranges")

def render_money_management_page(config: TradingConfig):
    """Main function to render the money management page"""
    
    st.markdown('<h1 class="main-header">💰 Advanced Money Management</h1>', unsafe_allow_html=True)
    
    # Initialize money manager in session state
    if 'money_manager' not in st.session_state:
        st.session_state.money_manager = AdvancedMoneyManager(config)
        # Load sample data for demonstration
        _load_sample_data(st.session_state.money_manager)
    
    money_manager = st.session_state.money_manager
    
    # Render the main dashboard
    render_money_management_dashboard(config, money_manager)

def _load_sample_data(money_manager: AdvancedMoneyManager):
    """Load sample data for demonstration purposes"""
    try:
        # Add sample trade history
        sample_trades = [
            {'strategy': 'cdm', 'pnl': 150.0, 'timestamp': datetime.now() - timedelta(days=i)}
            for i in range(20)
        ]
        money_manager.trade_history = sample_trades
        
        # Add sample price history
        money_manager.price_history['AAPL'] = [150.0 + np.random.normal(0, 2) for _ in range(30)]
        money_manager.price_history['MSFT'] = [300.0 + np.random.normal(0, 5) for _ in range(30)]
        
        # Add sample portfolio values
        money_manager.portfolio_values = [100000.0 + np.random.normal(0, 1000) for _ in range(30)]
        money_manager.daily_pnl = [np.random.normal(100, 500) for _ in range(30)]
        
    except Exception as e:
        st.error(f"Error loading sample data: {e}")