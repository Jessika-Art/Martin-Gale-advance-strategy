"""Enhanced Risk Management UI for MartinGales Trading Bot

This module provides a comprehensive Streamlit interface for advanced risk management,
including real-time monitoring, alerts, stress testing, and risk analytics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_risk_management import (
    EnhancedRiskManager, RiskLimits, RiskLevel, AlertType,
    RiskAlert, CorrelationMatrix, VaRMetrics, StressTestResult, RiskMetrics
)
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

def render_risk_management_page(config: TradingConfig):
    """Render the enhanced risk management page"""
    
    render_title_with_tooltip(
        "🛡️ Enhanced Risk Management", 
        "Comprehensive risk management system with real-time monitoring, alerts, stress testing, and advanced analytics",
        "header"
    )
    
    # Initialize risk manager in session state
    if 'risk_manager' not in st.session_state:
        st.session_state.risk_manager = EnhancedRiskManager()
        # Load sample data for demonstration
        _load_sample_risk_data(st.session_state.risk_manager)
    
    risk_manager = st.session_state.risk_manager
    
    # Create tabs for different risk management sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Risk Dashboard",
        "🔗 Correlation Analysis", 
        "📉 VaR & Stress Testing",
        "🚨 Risk Alerts",
        "📈 Risk Metrics",
        "⚙️ Risk Configuration"
    ])
    
    with tab1:
        render_risk_dashboard(risk_manager)
    
    with tab2:
        render_correlation_analysis(risk_manager)
    
    with tab3:
        render_var_stress_testing(risk_manager)
    
    with tab4:
        render_risk_alerts(risk_manager)
    
    with tab5:
        render_risk_metrics(risk_manager)
    
    with tab6:
        render_risk_configuration(risk_manager)

def render_risk_dashboard(risk_manager: EnhancedRiskManager):
    """Render the main risk dashboard"""
    
    render_title_with_tooltip(
        "🎯 Real-Time Risk Overview", 
        "Live monitoring of key risk metrics including portfolio heat, drawdown, VaR, and correlation analysis"
    )
    
    # Get risk summary
    risk_summary = risk_manager.get_risk_summary()
    
    # Risk score gauge
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_score = risk_summary["risk_score"]
        risk_level = risk_summary["risk_level"]
        
        # Color based on risk level
        color = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "orange", 
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "darkred"
        }[risk_level]
        
        st.metric(
            "Overall Risk Score",
            f"{risk_score:.1f}/100",
            delta=f"Risk Level: {risk_level.value.upper()}",
            help="Composite risk score based on multiple factors"
        )
        
        # Risk gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Risk Score"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 25], 'color': "lightgreen"},
                    {'range': [25, 50], 'color': "yellow"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        metrics = risk_summary["metrics"]
        st.metric(
            "Current Drawdown",
            f"{metrics.current_drawdown:.2%}",
            delta=f"Max: {metrics.max_drawdown:.2%}",
            help="Current portfolio drawdown from peak"
        )
        
        st.metric(
            "30-Day Volatility",
            f"{metrics.volatility_30d:.2%}",
            help="Annualized 30-day rolling volatility"
        )
    
    with col3:
        st.metric(
            "95% VaR",
            f"{metrics.portfolio_var.var_95:.2%}",
            delta=f"99% VaR: {metrics.portfolio_var.var_99:.2%}",
            help="Value at Risk - potential loss at 95% confidence"
        )
        
        st.metric(
            "Sharpe Ratio",
            f"{metrics.sharpe_ratio:.2f}",
            delta=f"Sortino: {metrics.sortino_ratio:.2f}",
            help="Risk-adjusted return metrics"
        )
    
    with col4:
        active_alerts = len([a for a in risk_summary["alerts"] if a.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        st.metric(
            "Active Alerts",
            str(active_alerts),
            delta=f"Total: {len(risk_summary['alerts'])}",
            help="Number of active risk alerts"
        )
        
        diversification = metrics.correlation_analysis.diversification_ratio
        st.metric(
            "Diversification Ratio",
            f"{diversification:.2f}",
            help="Portfolio diversification effectiveness"
        )
    
    # Risk trend chart
    st.subheader("📈 Risk Trends")
    
    if len(risk_manager.portfolio_returns) > 0:
        # Create sample risk history for visualization
        dates = pd.date_range(end=datetime.now(), periods=len(risk_manager.portfolio_returns), freq='D')
        returns_df = pd.DataFrame({
            'Date': dates,
            'Returns': risk_manager.portfolio_returns
        })
        
        # Calculate rolling metrics
        returns_df['Cumulative_Returns'] = returns_df['Returns'].cumsum()
        returns_df['Rolling_Vol'] = returns_df['Returns'].rolling(window=30, min_periods=1).std() * np.sqrt(252)
        returns_df['Rolling_Drawdown'] = (returns_df['Cumulative_Returns'] - returns_df['Cumulative_Returns'].expanding().max()) / returns_df['Cumulative_Returns'].expanding().max()
        
        # Create subplot
        fig_trends = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Cumulative Returns', 'Rolling Volatility', 'Drawdown'],
            vertical_spacing=0.08
        )
        
        # Cumulative returns
        fig_trends.add_trace(
            go.Scatter(x=returns_df['Date'], y=returns_df['Cumulative_Returns'], 
                      name='Cumulative Returns', line=dict(color='blue')),
            row=1, col=1
        )
        
        # Rolling volatility
        fig_trends.add_trace(
            go.Scatter(x=returns_df['Date'], y=returns_df['Rolling_Vol'], 
                      name='30D Volatility', line=dict(color='orange')),
            row=2, col=1
        )
        
        # Drawdown
        fig_trends.add_trace(
            go.Scatter(x=returns_df['Date'], y=returns_df['Rolling_Drawdown'], 
                      name='Drawdown', fill='tonexty', line=dict(color='red')),
            row=3, col=1
        )
        
        fig_trends.update_layout(height=600, showlegend=False)
        fig_trends.update_xaxes(title_text="Date", row=3, col=1)
        fig_trends.update_yaxes(title_text="Return", row=1, col=1)
        fig_trends.update_yaxes(title_text="Volatility", row=2, col=1)
        fig_trends.update_yaxes(title_text="Drawdown", row=3, col=1)
        
        st.plotly_chart(fig_trends, use_container_width=True)
    
    # Recommendations
    st.subheader("💡 Risk Management Recommendations")
    recommendations = risk_summary["recommendations"]
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.info(f"**{i}.** {rec}")
    else:
        st.success("✅ No immediate risk management actions required.")

def render_correlation_analysis(risk_manager: EnhancedRiskManager):
    """Render correlation analysis section"""
    
    st.subheader("🔗 Inter-Strategy Correlation Analysis")
    
    correlation_analysis = risk_manager.calculate_correlation_matrix()
    
    if correlation_analysis.correlation_matrix.empty:
        st.info("📊 No correlation data available. Need at least 2 strategies with return data.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Correlation Matrix")
        
        # Create correlation heatmap
        fig_corr = px.imshow(
            correlation_analysis.correlation_matrix.values,
            x=correlation_analysis.correlation_matrix.columns,
            y=correlation_analysis.correlation_matrix.index,
            color_continuous_scale='RdBu_r',
            aspect='auto',
            title="Strategy Correlation Matrix"
        )
        
        fig_corr.update_layout(height=400)
        st.plotly_chart(fig_corr, use_container_width=True)
    
    with col2:
        st.subheader("Correlation Metrics")
        
        st.metric(
            "Diversification Ratio",
            f"{correlation_analysis.diversification_ratio:.3f}",
            help="Higher values indicate better diversification"
        )
        
        st.metric(
            "Concentration Risk",
            f"{correlation_analysis.concentration_risk:.3f}",
            help="Lower values indicate less concentration risk"
        )
        
        st.metric(
            "High Correlations",
            str(len(correlation_analysis.high_correlations)),
            help="Number of strategy pairs with correlation > threshold"
        )
    
    # High correlation alerts
    if correlation_analysis.high_correlations:
        st.subheader("⚠️ High Correlation Alerts")
        
        corr_df = pd.DataFrame([
            {
                "Strategy 1": s1,
                "Strategy 2": s2,
                "Correlation": f"{corr:.3f}",
                "Risk Level": "High" if abs(corr) > 0.8 else "Medium"
            }
            for s1, s2, corr in correlation_analysis.high_correlations
        ])
        
        st.dataframe(corr_df, use_container_width=True)
        
        st.warning("🚨 High correlations detected! Consider diversifying your strategy allocation.")
    else:
        st.success("✅ No concerning correlations detected.")
    
    # Correlation network graph
    st.subheader("📊 Correlation Network")
    
    if len(correlation_analysis.correlation_matrix) > 1:
        # Create network-style visualization
        strategies = list(correlation_analysis.correlation_matrix.columns)
        
        # Create edges for correlations above threshold
        edges = []
        for i, s1 in enumerate(strategies):
            for j, s2 in enumerate(strategies):
                if i < j:  # Avoid duplicates
                    corr = correlation_analysis.correlation_matrix.loc[s1, s2]
                    if abs(corr) > 0.3:  # Show correlations above 0.3
                        edges.append((s1, s2, corr))
        
        if edges:
            # Simple network visualization using scatter plot
            fig_network = go.Figure()
            
            # Add nodes (strategies)
            angles = np.linspace(0, 2*np.pi, len(strategies), endpoint=False)
            x_pos = np.cos(angles)
            y_pos = np.sin(angles)
            
            fig_network.add_trace(go.Scatter(
                x=x_pos, y=y_pos,
                mode='markers+text',
                marker=dict(size=20, color='lightblue'),
                text=strategies,
                textposition='middle center',
                name='Strategies'
            ))
            
            # Add edges (correlations)
            for s1, s2, corr in edges:
                i1 = strategies.index(s1)
                i2 = strategies.index(s2)
                
                color = 'red' if abs(corr) > 0.7 else 'orange' if abs(corr) > 0.5 else 'yellow'
                width = abs(corr) * 5
                
                fig_network.add_trace(go.Scatter(
                    x=[x_pos[i1], x_pos[i2]], y=[y_pos[i1], y_pos[i2]],
                    mode='lines',
                    line=dict(color=color, width=width),
                    showlegend=False,
                    hovertemplate=f'{s1} - {s2}<br>Correlation: {corr:.3f}<extra></extra>'
                ))
            
            fig_network.update_layout(
                title="Strategy Correlation Network",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=400
            )
            
            st.plotly_chart(fig_network, use_container_width=True)
        else:
            st.info("No significant correlations to display in network view.")

def render_var_stress_testing(risk_manager: EnhancedRiskManager):
    """Render VaR and stress testing section"""
    
    st.subheader("📉 Value-at-Risk & Stress Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Value-at-Risk Analysis")
        
        var_metrics = risk_manager.calculate_var_metrics()
        
        if var_metrics.methodology == "insufficient_data":
            st.warning("⚠️ Insufficient data for VaR calculation (need at least 30 observations)")
        else:
            # VaR metrics display
            var_df = pd.DataFrame({
                "Confidence Level": ["95%", "99%"],
                "Value-at-Risk": [f"{var_metrics.var_95:.2%}", f"{var_metrics.var_99:.2%}"],
                "Expected Shortfall": [f"{var_metrics.expected_shortfall_95:.2%}", f"{var_metrics.expected_shortfall_99:.2%}"]
            })
            
            st.dataframe(var_df, use_container_width=True)
            
            # VaR visualization
            if len(risk_manager.portfolio_returns) > 0:
                returns = np.array(risk_manager.portfolio_returns)
                
                fig_var = go.Figure()
                
                # Histogram of returns
                fig_var.add_trace(go.Histogram(
                    x=returns,
                    nbinsx=50,
                    name='Return Distribution',
                    opacity=0.7
                ))
                
                # VaR lines
                fig_var.add_vline(x=-var_metrics.var_95, line_dash="dash", line_color="red", 
                                annotation_text="95% VaR")
                fig_var.add_vline(x=-var_metrics.var_99, line_dash="dash", line_color="darkred", 
                                annotation_text="99% VaR")
                
                fig_var.update_layout(
                    title="Return Distribution with VaR Levels",
                    xaxis_title="Daily Returns",
                    yaxis_title="Frequency",
                    height=400
                )
                
                st.plotly_chart(fig_var, use_container_width=True)
    
    with col2:
        st.subheader("🧪 Stress Testing")
        
        stress_tests = risk_manager.run_stress_tests()
        
        if not stress_tests:
            st.warning("⚠️ Insufficient data for stress testing")
        else:
            # Stress test results
            stress_df = pd.DataFrame([
                {
                    "Scenario": test.scenario_name,
                    "Portfolio Loss": f"{test.portfolio_loss:.2%}",
                    "Max Drawdown": f"{test.max_drawdown:.2%}",
                    "Recovery Days": test.recovery_time_estimate,
                    "Risk Level": test.risk_level.value.title(),
                    "Passed": "✅" if test.passed else "❌"
                }
                for test in stress_tests
            ])
            
            st.dataframe(stress_df, use_container_width=True)
            
            # Stress test visualization
            scenario_names = [test.scenario_name for test in stress_tests]
            portfolio_losses = [abs(test.portfolio_loss) for test in stress_tests]
            colors = ['green' if test.passed else 'red' for test in stress_tests]
            
            fig_stress = go.Figure(data=[
                go.Bar(
                    x=scenario_names,
                    y=portfolio_losses,
                    marker_color=colors,
                    text=[f"{loss:.1%}" for loss in portfolio_losses],
                    textposition='auto'
                )
            ])
            
            fig_stress.update_layout(
                title="Stress Test Results",
                xaxis_title="Scenario",
                yaxis_title="Portfolio Loss",
                height=400
            )
            
            st.plotly_chart(fig_stress, use_container_width=True)
            
            # Failed tests warning
            failed_tests = [test for test in stress_tests if not test.passed]
            if failed_tests:
                st.error(f"🚨 {len(failed_tests)} stress test(s) failed! Review risk exposure.")
            else:
                st.success("✅ All stress tests passed.")

def render_risk_alerts(risk_manager: EnhancedRiskManager):
    """Render risk alerts section"""
    
    render_title_with_tooltip(
        "🚨 Risk Alerts & Notifications", 
        "Active risk alerts and notifications based on configured thresholds and risk limits"
    )
    
    alerts = risk_manager.check_risk_alerts()
    
    if not alerts:
        st.success("✅ No active risk alerts. Portfolio risk levels are within acceptable ranges.")
        return
    
    # Alert summary
    alert_counts = {
        RiskLevel.CRITICAL: len([a for a in alerts if a.severity == RiskLevel.CRITICAL]),
        RiskLevel.HIGH: len([a for a in alerts if a.severity == RiskLevel.HIGH]),
        RiskLevel.MEDIUM: len([a for a in alerts if a.severity == RiskLevel.MEDIUM]),
        RiskLevel.LOW: len([a for a in alerts if a.severity == RiskLevel.LOW])
    }
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Critical", alert_counts[RiskLevel.CRITICAL], help="Immediate action required")
    with col2:
        st.metric("High", alert_counts[RiskLevel.HIGH], help="Urgent attention needed")
    with col3:
        st.metric("Medium", alert_counts[RiskLevel.MEDIUM], help="Monitor closely")
    with col4:
        st.metric("Low", alert_counts[RiskLevel.LOW], help="Informational")
    
    # Alert details
    render_title_with_tooltip(
        "📋 Alert Details", 
        "Detailed information about each active risk alert including severity, thresholds, and recommendations",
        "subheader"
    )
    
    for alert in sorted(alerts, key=lambda x: (x.severity.value, x.timestamp), reverse=True):
        severity_color = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠", 
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🔵"
        }[alert.severity]
        
        with st.expander(f"{severity_color} {alert.severity.value.upper()}: {alert.alert_type.value.replace('_', ' ').title()}"):
            st.write(f"**Message:** {alert.message}")
            st.write(f"**Timestamp:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if alert.value is not None and alert.threshold is not None:
                st.write(f"**Current Value:** {alert.value:.4f}")
                st.write(f"**Threshold:** {alert.threshold:.4f}")
            
            if alert.strategy:
                st.write(f"**Strategy:** {alert.strategy}")
            
            if alert.symbol:
                st.write(f"**Symbol:** {alert.symbol}")
            
            if alert.recommendation:
                st.info(f"**Recommendation:** {alert.recommendation}")
    
    # Alert timeline
    render_title_with_tooltip(
        "📈 Alert Timeline", 
        "Visual timeline showing when risk alerts occurred and their severity levels",
        "subheader"
    )
    
    if len(alerts) > 1:
        alert_timeline_df = pd.DataFrame([
            {
                "Timestamp": alert.timestamp,
                "Alert Type": alert.alert_type.value.replace('_', ' ').title(),
                "Severity": alert.severity.value.title(),
                "Value": alert.value or 0,
                "Size": max(abs(alert.value or 0), 0.1)  # Ensure positive size for scatter plot
            }
            for alert in alerts
        ])
        
        fig_timeline = px.scatter(
            alert_timeline_df,
            x="Timestamp",
            y="Alert Type",
            color="Severity",
            size="Size",  # Use positive Size instead of Value
            title="Risk Alert Timeline",
            color_discrete_map={
                "Critical": "red",
                "High": "orange",
                "Medium": "yellow",
                "Low": "blue"
            }
        )
        
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)

def render_risk_metrics(risk_manager: EnhancedRiskManager):
    """Render detailed risk metrics section"""
    
    render_title_with_tooltip(
        "📈 Detailed Risk Metrics", 
        "Comprehensive risk and performance metrics including Sharpe ratio, VaR, drawdown, and volatility measures"
    )
    
    metrics = risk_manager.calculate_comprehensive_risk_metrics()
    
    # Risk metrics table
    col1, col2 = st.columns(2)
    
    with col1:
        render_title_with_tooltip(
            "📊 Performance Metrics", 
            "Risk-adjusted performance measures including Sharpe, Sortino, and Information ratios",
            "subheader"
        )
        
        perf_metrics = {
            "Sharpe Ratio": f"{metrics.sharpe_ratio:.3f}",
            "Sortino Ratio": f"{metrics.sortino_ratio:.3f}",
            "Information Ratio": f"{metrics.information_ratio:.3f}",
            "Beta": f"{metrics.beta:.3f}",
            "Tracking Error": f"{metrics.tracking_error:.3f}"
        }
        
        for metric, value in perf_metrics.items():
            st.metric(metric, value)
    
    with col2:
        render_title_with_tooltip(
            "⚠️ Risk Metrics", 
            "Key risk indicators including drawdown, volatility, and Value-at-Risk measurements",
            "subheader"
        )
        
        risk_metrics_dict = {
            "Current Drawdown": f"{metrics.current_drawdown:.2%}",
            "Maximum Drawdown": f"{metrics.max_drawdown:.2%}",
            "30-Day Volatility": f"{metrics.volatility_30d:.2%}",
            "95% VaR": f"{metrics.portfolio_var.var_95:.2%}",
            "99% VaR": f"{metrics.portfolio_var.var_99:.2%}"
        }
        
        for metric, value in risk_metrics_dict.items():
            st.metric(metric, value)
    
    # Risk metrics over time (if historical data available)
    render_title_with_tooltip(
        "📈 Risk Metrics History", 
        "Historical trends of key risk metrics showing how portfolio risk has evolved over time",
        "subheader"
    )
    
    if len(risk_manager.risk_metrics_history) > 1:
        # Create historical metrics chart
        history_df = pd.DataFrame([
            {
                "Date": m.timestamp,
                "Sharpe Ratio": m.sharpe_ratio,
                "Volatility": m.volatility_30d,
                "VaR 95%": m.portfolio_var.var_95,
                "Drawdown": abs(m.current_drawdown)
            }
            for m in risk_manager.risk_metrics_history
        ])
        
        fig_history = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Sharpe Ratio', 'Volatility', 'VaR 95%', 'Drawdown']
        )
        
        fig_history.add_trace(
            go.Scatter(x=history_df['Date'], y=history_df['Sharpe Ratio'], name='Sharpe'),
            row=1, col=1
        )
        fig_history.add_trace(
            go.Scatter(x=history_df['Date'], y=history_df['Volatility'], name='Volatility'),
            row=1, col=2
        )
        fig_history.add_trace(
            go.Scatter(x=history_df['Date'], y=history_df['VaR 95%'], name='VaR'),
            row=2, col=1
        )
        fig_history.add_trace(
            go.Scatter(x=history_df['Date'], y=history_df['Drawdown'], name='Drawdown'),
            row=2, col=2
        )
        
        fig_history.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig_history, use_container_width=True)
    else:
        st.info("📊 Historical risk metrics will appear here as data accumulates over time.")

def render_risk_configuration(risk_manager: EnhancedRiskManager):
    """Render risk configuration section"""
    
    render_title_with_tooltip(
        "⚙️ Risk Management Configuration", 
        "Configure risk limits, thresholds, and parameters for automated risk monitoring and alert generation"
    )
    
    st.write("Configure risk limits and thresholds for automated monitoring and alerts.")
    
    # Current risk limits
    limits = risk_manager.risk_limits
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_title_with_tooltip(
            "📉 Drawdown Limits", 
            "Set maximum allowable drawdown levels for portfolio and individual strategies before alerts are triggered",
            "subheader"
        )
        
        max_portfolio_dd = st.slider(
            "Maximum Portfolio Drawdown",
            min_value=0.05,
            max_value=0.50,
            value=limits.max_portfolio_drawdown,
            step=0.01,
            format="%.2f",
            help="Maximum allowed portfolio drawdown before alerts"
        )
        
        max_strategy_dd = st.slider(
            "Maximum Strategy Drawdown",
            min_value=0.05,
            max_value=0.30,
            value=limits.max_strategy_drawdown,
            step=0.01,
            format="%.2f",
            help="Maximum allowed individual strategy drawdown"
        )
        
        render_title_with_tooltip(
            "🔗 Correlation Limits", 
            "Configure correlation thresholds and diversification requirements to manage portfolio concentration risk",
            "subheader"
        )
        
        max_correlation = st.slider(
            "Maximum Correlation Threshold",
            min_value=0.3,
            max_value=0.9,
            value=limits.max_correlation_threshold,
            step=0.05,
            format="%.2f",
            help="Correlation threshold for alerts"
        )
        
        min_diversification = st.slider(
            "Minimum Diversification Ratio",
            min_value=0.3,
            max_value=0.9,
            value=limits.min_diversification_ratio,
            step=0.05,
            format="%.2f",
            help="Minimum required diversification ratio"
        )
    
    with col2:
        render_title_with_tooltip(
            "💰 VaR & Risk Limits", 
            "Set Value-at-Risk limits and position concentration thresholds for portfolio risk management",
            "subheader"
        )
        
        var_95_limit = st.slider(
            "95% VaR Limit",
            min_value=0.01,
            max_value=0.15,
            value=limits.var_95_limit,
            step=0.005,
            format="%.3f",
            help="Maximum allowed 95% Value-at-Risk"
        )
        
        position_concentration = st.slider(
            "Maximum Position Concentration",
            min_value=0.10,
            max_value=0.50,
            value=limits.max_position_concentration,
            step=0.05,
            format="%.2f",
            help="Maximum allocation to single position"
        )
        
        render_title_with_tooltip(
            "📊 Volatility & Stress Testing", 
            "Configure volatility spike detection and stress test loss limits for extreme market condition monitoring",
            "subheader"
        )
        
        volatility_spike = st.slider(
            "Volatility Spike Threshold",
            min_value=1.5,
            max_value=5.0,
            value=limits.volatility_spike_threshold,
            step=0.1,
            format="%.1f",
            help="Multiplier for volatility spike detection"
        )
        
        stress_test_limit = st.slider(
            "Stress Test Loss Limit",
            min_value=0.10,
            max_value=0.40,
            value=limits.stress_test_loss_limit,
            step=0.05,
            format="%.2f",
            help="Maximum allowed loss in stress tests"
        )
    
    # Update button
    if st.button("💾 Update Risk Limits", type="primary"):
        # Update risk limits
        new_limits = RiskLimits(
            max_portfolio_drawdown=max_portfolio_dd,
            max_strategy_drawdown=max_strategy_dd,
            max_correlation_threshold=max_correlation,
            var_95_limit=var_95_limit,
            max_position_concentration=position_concentration,
            volatility_spike_threshold=volatility_spike,
            min_diversification_ratio=min_diversification,
            stress_test_loss_limit=stress_test_limit
        )
        
        risk_manager.risk_limits = new_limits
        st.success("✅ Risk limits updated successfully!")
        st.rerun()
    
    # Export/Import configuration
    render_title_with_tooltip(
        "💾 Configuration Management", 
        "Export current risk settings or import previously saved risk configuration files",
        "subheader"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Configuration"):
            config_dict = {
                "max_portfolio_drawdown": limits.max_portfolio_drawdown,
                "max_strategy_drawdown": limits.max_strategy_drawdown,
                "max_correlation_threshold": limits.max_correlation_threshold,
                "var_95_limit": limits.var_95_limit,
                "max_position_concentration": limits.max_position_concentration,
                "volatility_spike_threshold": limits.volatility_spike_threshold,
                "min_diversification_ratio": limits.min_diversification_ratio,
                "stress_test_loss_limit": limits.stress_test_loss_limit
            }
            
            st.download_button(
                label="📥 Download Risk Config",
                data=str(config_dict),
                file_name=f"risk_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("📤 Import Configuration", type=['json'])
        if uploaded_file is not None:
            try:
                import json
                config_data = json.loads(uploaded_file.read())
                # Apply imported configuration
                st.success("✅ Configuration imported successfully!")
            except Exception as e:
                st.error(f"❌ Error importing configuration: {str(e)}")

def _load_sample_risk_data(risk_manager: EnhancedRiskManager):
    """Load sample data for demonstration purposes"""
    
    # Generate sample portfolio returns
    np.random.seed(42)
    n_days = 100
    
    # Generate correlated strategy returns
    base_return = np.random.normal(0.001, 0.02, n_days)  # Base market return
    
    strategy_returns = {
        'CDM': base_return + np.random.normal(0, 0.01, n_days),
        'WDM': base_return * 0.8 + np.random.normal(0, 0.015, n_days),
        'ZRM': -base_return * 0.5 + np.random.normal(0, 0.008, n_days),  # Contrarian
        'IZRM': -base_return * 0.3 + np.random.normal(0, 0.012, n_days)
    }
    
    # Portfolio returns (weighted average)
    portfolio_returns = (
        0.3 * strategy_returns['CDM'] +
        0.3 * strategy_returns['WDM'] +
        0.2 * strategy_returns['ZRM'] +
        0.2 * strategy_returns['IZRM']
    )
    
    # Update risk manager with sample data
    for strategy, returns in strategy_returns.items():
        risk_manager.update_strategy_returns(strategy, returns.tolist())
    
    risk_manager.update_portfolio_returns(portfolio_returns.tolist())
    
    # Generate sample price data
    for symbol in ['AAPL', 'GOOGL', 'MSFT']:
        dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, n_days)))
        
        price_df = pd.DataFrame({
            'Date': dates,
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, n_days)
        })
        
        risk_manager.update_price_data(symbol, price_df)