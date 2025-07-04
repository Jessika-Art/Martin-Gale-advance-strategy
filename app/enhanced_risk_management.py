"""Enhanced Risk Management Module for MartinGales Trading Bot

This module provides advanced risk management features including:
- Real-time portfolio risk monitoring
- Inter-strategy correlation analysis
- Dynamic stop-loss adjustments
- Portfolio-level drawdown controls
- Risk alerts and notifications
- Stress testing and scenario analysis
- Value-at-Risk (VaR) calculations
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import warnings
from scipy import stats
import logging

class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of risk alerts"""
    CORRELATION_HIGH = "correlation_high"
    DRAWDOWN_LIMIT = "drawdown_limit"
    VAR_BREACH = "var_breach"
    VOLATILITY_SPIKE = "volatility_spike"
    POSITION_CONCENTRATION = "position_concentration"
    LIQUIDITY_RISK = "liquidity_risk"
    STRESS_TEST_FAIL = "stress_test_fail"

@dataclass
class RiskAlert:
    """Risk alert data structure"""
    alert_type: AlertType
    severity: RiskLevel
    message: str
    timestamp: datetime
    strategy: Optional[str] = None
    symbol: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    recommendation: Optional[str] = None

@dataclass
class CorrelationMatrix:
    """Strategy correlation analysis"""
    correlation_matrix: pd.DataFrame
    high_correlations: List[Tuple[str, str, float]]
    diversification_ratio: float
    concentration_risk: float
    timestamp: datetime

@dataclass
class VaRMetrics:
    """Value-at-Risk calculations"""
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    expected_shortfall_95: float  # Conditional VaR at 95%
    expected_shortfall_99: float  # Conditional VaR at 99%
    confidence_interval: Tuple[float, float]
    methodology: str
    timestamp: datetime

@dataclass
class StressTestResult:
    """Stress testing results"""
    scenario_name: str
    portfolio_loss: float
    strategy_losses: Dict[str, float]
    max_drawdown: float
    recovery_time_estimate: int  # days
    risk_level: RiskLevel
    passed: bool
    timestamp: datetime

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    portfolio_var: VaRMetrics
    correlation_analysis: CorrelationMatrix
    current_drawdown: float
    max_drawdown: float
    volatility_30d: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    tracking_error: float
    information_ratio: float
    timestamp: datetime

@dataclass
class RiskLimits:
    """Risk management limits and thresholds"""
    max_portfolio_drawdown: float = 0.15  # 15%
    max_strategy_drawdown: float = 0.10   # 10%
    max_correlation_threshold: float = 0.7  # 70%
    var_95_limit: float = 0.05  # 5%
    max_position_concentration: float = 0.25  # 25%
    volatility_spike_threshold: float = 2.0  # 2x normal volatility
    min_diversification_ratio: float = 0.6
    stress_test_loss_limit: float = 0.20  # 20%

class EnhancedRiskManager:
    """Enhanced risk management system"""
    
    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        self.risk_limits = risk_limits or RiskLimits()
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.strategy_returns: Dict[str, List[float]] = {}
        self.portfolio_returns: List[float] = []
        self.alerts: List[RiskAlert] = []
        self.risk_metrics_history: List[RiskMetrics] = []
        self.logger = logging.getLogger(__name__)
        
    def update_price_data(self, symbol: str, price_data: pd.DataFrame):
        """Update price data for risk calculations"""
        self.price_history[symbol] = price_data.copy()
        
    def update_strategy_returns(self, strategy: str, returns: List[float]):
        """Update strategy return data"""
        self.strategy_returns[strategy] = returns.copy()
        
    def update_portfolio_returns(self, returns: List[float]):
        """Update portfolio return data"""
        self.portfolio_returns = returns.copy()
        
    def calculate_correlation_matrix(self) -> CorrelationMatrix:
        """Calculate inter-strategy correlation matrix"""
        if len(self.strategy_returns) < 2:
            return CorrelationMatrix(
                correlation_matrix=pd.DataFrame(),
                high_correlations=[],
                diversification_ratio=1.0,
                concentration_risk=0.0,
                timestamp=datetime.now()
            )
            
        # Create returns dataframe
        returns_df = pd.DataFrame(self.strategy_returns)
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Find high correlations
        high_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > self.risk_limits.max_correlation_threshold:
                    high_correlations.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_value
                    ))
        
        # Calculate diversification ratio
        weights = np.array([1/len(returns_df.columns)] * len(returns_df.columns))
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(corr_matrix.values, weights)))
        avg_vol = np.mean([returns_df[col].std() for col in returns_df.columns])
        diversification_ratio = avg_vol / portfolio_vol if portfolio_vol > 0 else 1.0
        
        # Calculate concentration risk
        eigenvalues = np.linalg.eigvals(corr_matrix.values)
        concentration_risk = 1 - (len(eigenvalues) * np.var(eigenvalues)) / (np.sum(eigenvalues) ** 2)
        
        return CorrelationMatrix(
            correlation_matrix=corr_matrix,
            high_correlations=high_correlations,
            diversification_ratio=diversification_ratio,
            concentration_risk=concentration_risk,
            timestamp=datetime.now()
        )
    
    def calculate_var_metrics(self, confidence_levels: List[float] = [0.95, 0.99]) -> VaRMetrics:
        """Calculate Value-at-Risk metrics"""
        if len(self.portfolio_returns) < 30:
            return VaRMetrics(
                var_95=0.0, var_99=0.0,
                expected_shortfall_95=0.0, expected_shortfall_99=0.0,
                confidence_interval=(0.0, 0.0),
                methodology="insufficient_data",
                timestamp=datetime.now()
            )
        
        returns = np.array(self.portfolio_returns)
        
        # Historical VaR
        var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
        var_99 = np.percentile(returns, 1)  # 1st percentile for 99% VaR
        
        # Expected Shortfall (Conditional VaR)
        es_95 = np.mean(returns[returns <= var_95])
        es_99 = np.mean(returns[returns <= var_99])
        
        # Confidence interval using bootstrap
        n_bootstrap = 1000
        var_bootstrap = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(returns, size=len(returns), replace=True)
            var_bootstrap.append(np.percentile(sample, 5))
        
        confidence_interval = (np.percentile(var_bootstrap, 2.5), np.percentile(var_bootstrap, 97.5))
        
        return VaRMetrics(
            var_95=abs(var_95),
            var_99=abs(var_99),
            expected_shortfall_95=abs(es_95),
            expected_shortfall_99=abs(es_99),
            confidence_interval=confidence_interval,
            methodology="historical_simulation",
            timestamp=datetime.now()
        )
    
    def run_stress_tests(self) -> List[StressTestResult]:
        """Run various stress test scenarios"""
        stress_tests = []
        
        if len(self.portfolio_returns) < 30:
            return stress_tests
        
        returns = np.array(self.portfolio_returns)
        
        # Scenario 1: Market crash (3 standard deviations down)
        crash_scenario = self._simulate_scenario(
            "Market Crash", returns, shock_magnitude=-3.0
        )
        stress_tests.append(crash_scenario)
        
        # Scenario 2: High volatility period
        volatility_scenario = self._simulate_scenario(
            "High Volatility", returns, volatility_multiplier=2.0
        )
        stress_tests.append(volatility_scenario)
        
        # Scenario 3: Correlation breakdown
        correlation_scenario = self._simulate_scenario(
            "Correlation Breakdown", returns, correlation_shock=0.9
        )
        stress_tests.append(correlation_scenario)
        
        return stress_tests
    
    def _simulate_scenario(self, scenario_name: str, returns: np.ndarray, 
                          shock_magnitude: float = 0.0, volatility_multiplier: float = 1.0,
                          correlation_shock: float = 0.0) -> StressTestResult:
        """Simulate a specific stress scenario"""
        
        # Apply shock to returns
        shocked_returns = returns.copy()
        
        if shock_magnitude != 0.0:
            shock = shock_magnitude * np.std(returns)
            shocked_returns += shock
        
        if volatility_multiplier != 1.0:
            shocked_returns = shocked_returns * volatility_multiplier
        
        # Calculate portfolio loss
        portfolio_loss = np.sum(shocked_returns[shocked_returns < 0])
        
        # Calculate strategy-specific losses (simplified)
        strategy_losses = {}
        for strategy in self.strategy_returns.keys():
            strategy_returns = np.array(self.strategy_returns[strategy])
            if len(strategy_returns) > 0:
                strategy_shocked = strategy_returns * volatility_multiplier + (shock_magnitude * np.std(strategy_returns) if shock_magnitude != 0 else 0)
                strategy_losses[strategy] = np.sum(strategy_shocked[strategy_shocked < 0])
        
        # Calculate max drawdown in scenario
        cumulative = np.cumsum(shocked_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0.0
        
        # Estimate recovery time (simplified)
        recovery_time = max(30, int(abs(max_drawdown) * 365)) if max_drawdown < 0 else 0
        
        # Determine risk level and pass/fail
        risk_level = RiskLevel.LOW
        passed = True
        
        if abs(portfolio_loss) > self.risk_limits.stress_test_loss_limit:
            risk_level = RiskLevel.CRITICAL
            passed = False
        elif abs(max_drawdown) > self.risk_limits.max_portfolio_drawdown:
            risk_level = RiskLevel.HIGH
            passed = False
        elif abs(portfolio_loss) > self.risk_limits.stress_test_loss_limit * 0.5:
            risk_level = RiskLevel.MEDIUM
        
        return StressTestResult(
            scenario_name=scenario_name,
            portfolio_loss=portfolio_loss,
            strategy_losses=strategy_losses,
            max_drawdown=max_drawdown,
            recovery_time_estimate=recovery_time,
            risk_level=risk_level,
            passed=passed,
            timestamp=datetime.now()
        )
    
    def calculate_comprehensive_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        
        # Calculate VaR metrics
        var_metrics = self.calculate_var_metrics()
        
        # Calculate correlation analysis
        correlation_analysis = self.calculate_correlation_matrix()
        
        # Calculate drawdown metrics
        current_dd, max_dd = self._calculate_drawdown_metrics()
        
        # Calculate other risk metrics
        volatility_30d = self._calculate_rolling_volatility(30)
        sharpe_ratio = self._calculate_sharpe_ratio()
        sortino_ratio = self._calculate_sortino_ratio()
        beta = self._calculate_beta()
        tracking_error = self._calculate_tracking_error()
        information_ratio = self._calculate_information_ratio()
        
        return RiskMetrics(
            portfolio_var=var_metrics,
            correlation_analysis=correlation_analysis,
            current_drawdown=current_dd,
            max_drawdown=max_dd,
            volatility_30d=volatility_30d,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            beta=beta,
            tracking_error=tracking_error,
            information_ratio=information_ratio,
            timestamp=datetime.now()
        )
    
    def _calculate_drawdown_metrics(self) -> Tuple[float, float]:
        """Calculate current and maximum drawdown"""
        if len(self.portfolio_returns) == 0:
            return 0.0, 0.0
        
        cumulative = np.cumsum(self.portfolio_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        current_drawdown = drawdown[-1] if len(drawdown) > 0 else 0.0
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0.0
        
        return current_drawdown, max_drawdown
    
    def _calculate_rolling_volatility(self, window: int) -> float:
        """Calculate rolling volatility"""
        if len(self.portfolio_returns) < window:
            return 0.0
        
        recent_returns = self.portfolio_returns[-window:]
        return np.std(recent_returns) * np.sqrt(252)  # Annualized
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(self.portfolio_returns) == 0:
            return 0.0
        
        returns = np.array(self.portfolio_returns)
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        if len(self.portfolio_returns) == 0:
            return 0.0
        
        returns = np.array(self.portfolio_returns)
        excess_returns = returns - (risk_free_rate / 252)
        
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return 0.0
        
        return np.mean(excess_returns) / downside_deviation * np.sqrt(252)
    
    def _calculate_beta(self, benchmark_returns: Optional[List[float]] = None) -> float:
        """Calculate portfolio beta (simplified, using market proxy)"""
        if benchmark_returns is None or len(self.portfolio_returns) == 0:
            return 1.0  # Default beta
        
        if len(benchmark_returns) != len(self.portfolio_returns):
            return 1.0
        
        portfolio_returns = np.array(self.portfolio_returns)
        market_returns = np.array(benchmark_returns)
        
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        return covariance / market_variance if market_variance != 0 else 1.0
    
    def _calculate_tracking_error(self, benchmark_returns: Optional[List[float]] = None) -> float:
        """Calculate tracking error"""
        if benchmark_returns is None or len(self.portfolio_returns) == 0:
            return 0.0
        
        if len(benchmark_returns) != len(self.portfolio_returns):
            return 0.0
        
        portfolio_returns = np.array(self.portfolio_returns)
        market_returns = np.array(benchmark_returns)
        
        tracking_diff = portfolio_returns - market_returns
        return np.std(tracking_diff) * np.sqrt(252)
    
    def _calculate_information_ratio(self, benchmark_returns: Optional[List[float]] = None) -> float:
        """Calculate information ratio"""
        if benchmark_returns is None or len(self.portfolio_returns) == 0:
            return 0.0
        
        tracking_error = self._calculate_tracking_error(benchmark_returns)
        if tracking_error == 0:
            return 0.0
        
        portfolio_returns = np.array(self.portfolio_returns)
        market_returns = np.array(benchmark_returns)
        
        excess_return = np.mean(portfolio_returns) - np.mean(market_returns)
        return (excess_return * 252) / tracking_error
    
    def check_risk_alerts(self) -> List[RiskAlert]:
        """Check for risk alerts and generate notifications"""
        alerts = []
        
        # Calculate current metrics
        risk_metrics = self.calculate_comprehensive_risk_metrics()
        
        # Check correlation alerts
        for strategy1, strategy2, correlation in risk_metrics.correlation_analysis.high_correlations:
            alerts.append(RiskAlert(
                alert_type=AlertType.CORRELATION_HIGH,
                severity=RiskLevel.HIGH if abs(correlation) > 0.8 else RiskLevel.MEDIUM,
                message=f"High correlation detected between {strategy1} and {strategy2}: {correlation:.2f}",
                timestamp=datetime.now(),
                value=correlation,
                threshold=self.risk_limits.max_correlation_threshold,
                recommendation="Consider reducing position sizes or diversifying strategies"
            ))
        
        # Check drawdown alerts
        if abs(risk_metrics.current_drawdown) > self.risk_limits.max_portfolio_drawdown:
            alerts.append(RiskAlert(
                alert_type=AlertType.DRAWDOWN_LIMIT,
                severity=RiskLevel.CRITICAL,
                message=f"Portfolio drawdown exceeded limit: {risk_metrics.current_drawdown:.2%}",
                timestamp=datetime.now(),
                value=risk_metrics.current_drawdown,
                threshold=self.risk_limits.max_portfolio_drawdown,
                recommendation="Consider reducing position sizes or stopping trading"
            ))
        
        # Check VaR alerts
        if risk_metrics.portfolio_var.var_95 > self.risk_limits.var_95_limit:
            alerts.append(RiskAlert(
                alert_type=AlertType.VAR_BREACH,
                severity=RiskLevel.HIGH,
                message=f"95% VaR exceeded limit: {risk_metrics.portfolio_var.var_95:.2%}",
                timestamp=datetime.now(),
                value=risk_metrics.portfolio_var.var_95,
                threshold=self.risk_limits.var_95_limit,
                recommendation="Review position sizes and risk exposure"
            ))
        
        # Check volatility alerts
        if risk_metrics.volatility_30d > self.risk_limits.volatility_spike_threshold:
            alerts.append(RiskAlert(
                alert_type=AlertType.VOLATILITY_SPIKE,
                severity=RiskLevel.MEDIUM,
                message=f"Volatility spike detected: {risk_metrics.volatility_30d:.2%}",
                timestamp=datetime.now(),
                value=risk_metrics.volatility_30d,
                threshold=self.risk_limits.volatility_spike_threshold,
                recommendation="Monitor positions closely and consider reducing leverage"
            ))
        
        # Store alerts
        self.alerts.extend(alerts)
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
        
        return alerts
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        risk_metrics = self.calculate_comprehensive_risk_metrics()
        stress_tests = self.run_stress_tests()
        alerts = self.check_risk_alerts()
        
        # Calculate overall risk score (0-100)
        risk_score = self._calculate_overall_risk_score(risk_metrics, stress_tests, alerts)
        
        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level_from_score(risk_score),
            "metrics": risk_metrics,
            "stress_tests": stress_tests,
            "alerts": alerts,
            "recommendations": self._generate_recommendations(risk_metrics, alerts)
        }
    
    def _calculate_overall_risk_score(self, metrics: RiskMetrics, 
                                    stress_tests: List[StressTestResult],
                                    alerts: List[RiskAlert]) -> float:
        """Calculate overall risk score (0-100, higher is riskier)"""
        score = 0.0
        
        # VaR component (0-25 points)
        var_score = min(25, (metrics.portfolio_var.var_95 / self.risk_limits.var_95_limit) * 25)
        score += var_score
        
        # Drawdown component (0-25 points)
        dd_score = min(25, (abs(metrics.current_drawdown) / self.risk_limits.max_portfolio_drawdown) * 25)
        score += dd_score
        
        # Correlation component (0-20 points)
        corr_score = min(20, len(metrics.correlation_analysis.high_correlations) * 5)
        score += corr_score
        
        # Stress test component (0-20 points)
        failed_tests = sum(1 for test in stress_tests if not test.passed)
        stress_score = min(20, failed_tests * 7)
        score += stress_score
        
        # Alert component (0-10 points)
        critical_alerts = sum(1 for alert in alerts if alert.severity == RiskLevel.CRITICAL)
        alert_score = min(10, critical_alerts * 5)
        score += alert_score
        
        return min(100, score)
    
    def _get_risk_level_from_score(self, score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if score >= 75:
            return RiskLevel.CRITICAL
        elif score >= 50:
            return RiskLevel.HIGH
        elif score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendations(self, metrics: RiskMetrics, alerts: List[RiskAlert]) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        # High correlation recommendations
        if len(metrics.correlation_analysis.high_correlations) > 0:
            recommendations.append("Consider diversifying strategies to reduce correlation risk")
        
        # High drawdown recommendations
        if abs(metrics.current_drawdown) > self.risk_limits.max_portfolio_drawdown * 0.7:
            recommendations.append("Current drawdown is approaching limits - consider reducing position sizes")
        
        # High VaR recommendations
        if metrics.portfolio_var.var_95 > self.risk_limits.var_95_limit * 0.8:
            recommendations.append("Value-at-Risk is elevated - review risk exposure")
        
        # Low diversification recommendations
        if metrics.correlation_analysis.diversification_ratio < self.risk_limits.min_diversification_ratio:
            recommendations.append("Portfolio lacks diversification - consider adding uncorrelated strategies")
        
        # Critical alerts recommendations
        critical_alerts = [alert for alert in alerts if alert.severity == RiskLevel.CRITICAL]
        if critical_alerts:
            recommendations.append("Critical risk alerts detected - immediate action required")
        
        return recommendations