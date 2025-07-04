import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from config import TradingConfig, StrategyType
from cycle_analysis import CycleAnalysisReport

class PositionSizingMethod(Enum):
    """Position sizing methods"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    PERFORMANCE_BASED = "performance_based"
    RISK_PARITY = "risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    DYNAMIC_ALLOCATION = "dynamic_allocation"

class RiskLevel(Enum):
    """Risk level classifications"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"

@dataclass
class PerformanceMetrics:
    """Performance metrics for position sizing decisions"""
    win_rate: float = 0.0
    avg_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    recent_performance: float = 0.0  # Last 10 trades performance
    consecutive_losses: int = 0
    consecutive_wins: int = 0

@dataclass
class RiskMetrics:
    """Risk metrics for portfolio management"""
    portfolio_heat: float = 0.0  # Percentage of portfolio at risk
    correlation_risk: float = 0.0  # Inter-strategy correlation
    concentration_risk: float = 0.0  # Single position concentration
    var_95: float = 0.0  # Value at Risk 95%
    expected_shortfall: float = 0.0  # Conditional VaR
    beta: float = 1.0  # Market beta

@dataclass
class PositionSizingConfig:
    """Configuration for advanced position sizing"""
    method: PositionSizingMethod = PositionSizingMethod.PERCENTAGE
    base_allocation: float = 0.05  # 5% base allocation
    max_allocation: float = 0.15  # 15% max allocation per position
    min_allocation: float = 0.01  # 1% min allocation
    
    # Volatility adjustment parameters
    target_volatility: float = 0.15  # 15% target volatility
    lookback_period: int = 20  # Days for volatility calculation
    
    # Performance-based parameters
    performance_lookback: int = 10  # Number of recent trades to consider
    performance_multiplier: float = 1.5  # Max multiplier based on performance
    
    # Risk parity parameters
    risk_budget_equal: bool = True  # Equal risk budget allocation
    rebalance_frequency: int = 5  # Days between rebalancing
    
    # Kelly criterion parameters
    kelly_fraction: float = 0.25  # Fraction of Kelly to use (conservative)
    min_edge: float = 0.02  # Minimum edge required for Kelly

class AdvancedMoneyManager:
    """Advanced money management system with dynamic position sizing and risk management"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.position_config = PositionSizingConfig()
        
        # Performance tracking
        self.strategy_performance: Dict[StrategyType, PerformanceMetrics] = {}
        self.portfolio_metrics: Dict[str, float] = {}
        self.risk_metrics = RiskMetrics()
        
        # Historical data for calculations
        self.price_history: Dict[str, List[float]] = {}
        self.return_history: Dict[str, List[float]] = {}
        self.trade_history: List[Dict] = []
        
        # Risk monitoring
        self.daily_pnl: List[float] = []
        self.portfolio_values: List[float] = []
        self.drawdown_history: List[float] = []
        
        self.logger.info("Advanced Money Manager initialized")
    
    def calculate_dynamic_position_size(
        self, 
        strategy_type: StrategyType, 
        symbol: str, 
        account_balance: float, 
        symbol_price: float,
        recent_performance: Optional[PerformanceMetrics] = None
    ) -> float:
        """Calculate dynamic position size based on multiple factors"""
        
        try:
            base_size = self._get_base_position_size(account_balance, symbol_price)
            
            # Get performance metrics
            if recent_performance is None:
                recent_performance = self._calculate_recent_performance(strategy_type)
            
            # Apply sizing method
            if self.position_config.method == PositionSizingMethod.VOLATILITY_ADJUSTED:
                adjusted_size = self._apply_volatility_adjustment(base_size, symbol)
            elif self.position_config.method == PositionSizingMethod.PERFORMANCE_BASED:
                adjusted_size = self._apply_performance_adjustment(base_size, recent_performance)
            elif self.position_config.method == PositionSizingMethod.RISK_PARITY:
                adjusted_size = self._apply_risk_parity_sizing(base_size, strategy_type, symbol)
            elif self.position_config.method == PositionSizingMethod.KELLY_CRITERION:
                adjusted_size = self._apply_kelly_criterion(base_size, recent_performance)
            else:
                adjusted_size = base_size
            
            # Apply risk constraints
            final_size = self._apply_risk_constraints(adjusted_size, account_balance, symbol_price)
            
            self.logger.info(
                f"Dynamic position sizing for {strategy_type.value} {symbol}: "
                f"Base: {base_size:.2f}, Adjusted: {adjusted_size:.2f}, Final: {final_size:.2f}"
            )
            
            return final_size
            
        except Exception as e:
            self.logger.error(f"Error calculating dynamic position size: {e}")
            return self._get_base_position_size(account_balance, symbol_price)
    
    def _get_base_position_size(self, account_balance: float, symbol_price: float) -> float:
        """Get base position size from configuration"""
        return self.config.get_effective_position_size_for_strategy(
            StrategyType.CDM,  # Use CDM as default for base calculation
            account_balance, 
            symbol_price
        )
    
    def _calculate_recent_performance(self, strategy_type: StrategyType) -> PerformanceMetrics:
        """Calculate recent performance metrics for a strategy"""
        if strategy_type not in self.strategy_performance:
            return PerformanceMetrics()
        
        # Get recent trades for this strategy
        recent_trades = [t for t in self.trade_history[-self.position_config.performance_lookback:] 
                        if t.get('strategy') == strategy_type.value]
        
        if not recent_trades:
            return PerformanceMetrics()
        
        returns = [t.get('pnl', 0) for t in recent_trades]
        wins = [r for r in returns if r > 0]
        
        metrics = PerformanceMetrics(
            win_rate=len(wins) / len(returns) if returns else 0,
            avg_return=np.mean(returns) if returns else 0,
            volatility=np.std(returns) if len(returns) > 1 else 0,
            recent_performance=sum(returns),
            consecutive_losses=self._count_consecutive_losses(returns),
            consecutive_wins=self._count_consecutive_wins(returns)
        )
        
        if metrics.volatility > 0 and metrics.avg_return != 0:
            metrics.sharpe_ratio = metrics.avg_return / metrics.volatility
        
        return metrics
    
    def _count_consecutive_losses(self, returns: List[float]) -> int:
        """Count consecutive losses from the end of returns list"""
        count = 0
        for ret in reversed(returns):
            if ret < 0:
                count += 1
            else:
                break
        return count
    
    def _count_consecutive_wins(self, returns: List[float]) -> int:
        """Count consecutive wins from the end of returns list"""
        count = 0
        for ret in reversed(returns):
            if ret > 0:
                count += 1
            else:
                break
        return count
    
    def _apply_volatility_adjustment(self, base_size: float, symbol: str) -> float:
        """Apply volatility-based position size adjustment"""
        if symbol not in self.return_history or len(self.return_history[symbol]) < 2:
            return base_size
        
        recent_returns = self.return_history[symbol][-self.position_config.lookback_period:]
        current_volatility = np.std(recent_returns) if len(recent_returns) > 1 else 0.15
        
        # Adjust position size inversely to volatility
        volatility_multiplier = self.position_config.target_volatility / max(current_volatility, 0.01)
        volatility_multiplier = np.clip(volatility_multiplier, 0.5, 2.0)  # Limit adjustment
        
        return base_size * volatility_multiplier
    
    def _apply_performance_adjustment(self, base_size: float, performance: PerformanceMetrics) -> float:
        """Apply performance-based position size adjustment"""
        # Reduce size after consecutive losses
        if performance.consecutive_losses >= 3:
            loss_penalty = 0.8 ** (performance.consecutive_losses - 2)  # Exponential reduction
            base_size *= max(loss_penalty, 0.3)  # Minimum 30% of base size
        
        # Increase size after good performance
        if performance.win_rate > 0.6 and performance.avg_return > 0:
            performance_multiplier = 1 + (performance.win_rate - 0.5) * self.position_config.performance_multiplier
            performance_multiplier = min(performance_multiplier, self.position_config.performance_multiplier)
            base_size *= performance_multiplier
        
        return base_size
    
    def _apply_risk_parity_sizing(self, base_size: float, strategy_type: StrategyType, symbol: str) -> float:
        """Apply risk parity position sizing"""
        # Calculate risk contribution of this position
        strategy_volatility = self._get_strategy_volatility(strategy_type)
        
        if strategy_volatility <= 0:
            return base_size
        
        # Adjust size inversely to risk contribution
        risk_adjustment = 0.15 / strategy_volatility  # Target 15% volatility
        risk_adjustment = np.clip(risk_adjustment, 0.5, 2.0)
        
        return base_size * risk_adjustment
    
    def _apply_kelly_criterion(self, base_size: float, performance: PerformanceMetrics) -> float:
        """Apply Kelly criterion for position sizing"""
        if performance.win_rate <= 0.5 or performance.avg_return <= 0:
            return base_size * 0.5  # Conservative sizing for poor performance
        
        # Simplified Kelly calculation
        # Kelly = (bp - q) / b, where b = avg_win/avg_loss, p = win_rate, q = loss_rate
        if performance.avg_return > 0 and performance.win_rate > 0:
            edge = performance.avg_return
            if edge >= self.position_config.min_edge:
                kelly_fraction = edge * self.position_config.kelly_fraction
                kelly_multiplier = np.clip(kelly_fraction, 0.1, 1.0)
                return base_size * kelly_multiplier
        
        return base_size * 0.5
    
    def _apply_risk_constraints(self, size: float, account_balance: float, symbol_price: float) -> float:
        """Apply risk constraints to position size"""
        # Convert to dollar amount for constraint checking
        dollar_amount = size * symbol_price
        max_dollar_amount = account_balance * self.position_config.max_allocation
        min_dollar_amount = account_balance * self.position_config.min_allocation
        
        # Apply constraints
        constrained_dollar_amount = np.clip(dollar_amount, min_dollar_amount, max_dollar_amount)
        
        # Convert back to shares
        return constrained_dollar_amount / symbol_price if symbol_price > 0 else size
    
    def _get_strategy_volatility(self, strategy_type: StrategyType) -> float:
        """Get volatility for a specific strategy"""
        if strategy_type in self.strategy_performance:
            return self.strategy_performance[strategy_type].volatility
        return 0.15  # Default volatility
    
    def calculate_portfolio_heat(self, positions: Dict[str, Dict]) -> float:
        """Calculate portfolio heat (percentage of portfolio at risk)"""
        total_risk = 0.0
        total_value = sum(pos.get('market_value', 0) for pos in positions.values())
        
        if total_value <= 0:
            return 0.0
        
        for symbol, position in positions.items():
            position_value = position.get('market_value', 0)
            position_risk = position_value * 0.02  # Assume 2% risk per position
            total_risk += position_risk
        
        portfolio_heat = (total_risk / total_value) * 100
        self.risk_metrics.portfolio_heat = portfolio_heat
        
        return portfolio_heat
    
    def calculate_correlation_risk(self, strategy_returns: Dict[StrategyType, List[float]]) -> float:
        """Calculate inter-strategy correlation risk"""
        if len(strategy_returns) < 2:
            return 0.0
        
        correlations = []
        strategies = list(strategy_returns.keys())
        
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                returns1 = strategy_returns[strategies[i]]
                returns2 = strategy_returns[strategies[j]]
                
                if len(returns1) > 1 and len(returns2) > 1:
                    min_length = min(len(returns1), len(returns2))
                    corr = np.corrcoef(returns1[-min_length:], returns2[-min_length:])[0, 1]
                    if not np.isnan(corr):
                        correlations.append(abs(corr))
        
        avg_correlation = np.mean(correlations) if correlations else 0.0
        self.risk_metrics.correlation_risk = avg_correlation
        
        return avg_correlation
    
    def calculate_var_95(self, returns: List[float]) -> float:
        """Calculate 95% Value at Risk"""
        if len(returns) < 20:
            return 0.0
        
        var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
        self.risk_metrics.var_95 = abs(var_95)
        
        return abs(var_95)
    
    def should_reduce_exposure(self) -> bool:
        """Determine if portfolio exposure should be reduced"""
        # Check multiple risk factors
        risk_factors = [
            self.risk_metrics.portfolio_heat > 15.0,  # High portfolio heat
            self.risk_metrics.correlation_risk > 0.7,  # High correlation
            len(self.drawdown_history) > 0 and self.drawdown_history[-1] > 10.0,  # High drawdown
            self.risk_metrics.var_95 > 5.0  # High VaR
        ]
        
        return sum(risk_factors) >= 2  # Reduce if 2+ risk factors present
    
    def get_recommended_allocation(self, strategy_type: StrategyType) -> float:
        """Get recommended capital allocation for a strategy"""
        base_allocation = self.config.get_strategy_settings(strategy_type).capital_allocation
        
        # Adjust based on recent performance
        performance = self._calculate_recent_performance(strategy_type)
        
        if performance.consecutive_losses >= 3:
            # Reduce allocation after consecutive losses
            reduction_factor = 0.8 ** (performance.consecutive_losses - 2)
            return base_allocation * max(reduction_factor, 0.3)
        
        if performance.win_rate > 0.6 and performance.avg_return > 0:
            # Increase allocation for good performance
            increase_factor = 1 + (performance.win_rate - 0.5) * 0.5
            return base_allocation * min(increase_factor, 1.5)
        
        return base_allocation
    
    def update_performance_metrics(self, trade_data: Dict):
        """Update performance metrics with new trade data"""
        self.trade_history.append(trade_data)
        
        # Keep only recent history
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-500:]
        
        # Update strategy-specific metrics
        strategy = trade_data.get('strategy')
        if strategy:
            strategy_type = StrategyType(strategy.lower())
            if strategy_type not in self.strategy_performance:
                self.strategy_performance[strategy_type] = PerformanceMetrics()
            
            # Recalculate metrics
            self.strategy_performance[strategy_type] = self._calculate_recent_performance(strategy_type)
    
    def update_price_history(self, symbol: str, price: float):
        """Update price history for volatility calculations"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.return_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Calculate return if we have previous price
        if len(self.price_history[symbol]) > 1:
            prev_price = self.price_history[symbol][-2]
            if prev_price > 0:
                return_pct = (price - prev_price) / prev_price
                self.return_history[symbol].append(return_pct)
        
        # Keep only recent history
        max_history = 100
        if len(self.price_history[symbol]) > max_history:
            self.price_history[symbol] = self.price_history[symbol][-max_history:]
            self.return_history[symbol] = self.return_history[symbol][-max_history:]
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        return {
            'portfolio_heat': self.risk_metrics.portfolio_heat,
            'correlation_risk': self.risk_metrics.correlation_risk,
            'var_95': self.risk_metrics.var_95,
            'should_reduce_exposure': self.should_reduce_exposure(),
            'current_drawdown': self.drawdown_history[-1] if self.drawdown_history else 0.0,
            'risk_level': self._assess_risk_level()
        }
    
    def _assess_risk_level(self) -> RiskLevel:
        """Assess current portfolio risk level"""
        risk_score = 0
        
        if self.risk_metrics.portfolio_heat > 20:
            risk_score += 2
        elif self.risk_metrics.portfolio_heat > 10:
            risk_score += 1
        
        if self.risk_metrics.correlation_risk > 0.8:
            risk_score += 2
        elif self.risk_metrics.correlation_risk > 0.6:
            risk_score += 1
        
        if self.drawdown_history and self.drawdown_history[-1] > 15:
            risk_score += 2
        elif self.drawdown_history and self.drawdown_history[-1] > 8:
            risk_score += 1
        
        if risk_score >= 5:
            return RiskLevel.VERY_AGGRESSIVE
        elif risk_score >= 3:
            return RiskLevel.AGGRESSIVE
        elif risk_score >= 1:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.CONSERVATIVE