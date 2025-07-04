from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np
from enum import Enum

class CycleStatus(Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"

class TradeType(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Trade:
    """Individual trade within a cycle"""
    trade_id: str
    timestamp: datetime
    symbol: str
    trade_type: TradeType
    quantity: float
    price: float
    order_level: int  # Which martingale level (1, 2, 3, etc.)
    strategy_type: str  # CDM, WDM, ZRM, IZRM
    commission: float = 0.0
    
    @property
    def value(self) -> float:
        """Total trade value"""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Trade value after commission"""
        return self.value - self.commission

@dataclass
class Cycle:
    """Complete trading cycle with all trades and metrics"""
    cycle_id: str
    strategy_type: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: CycleStatus = CycleStatus.ACTIVE
    trades: List[Trade] = field(default_factory=list)
    
    # Cycle metrics
    total_investment: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0
    max_investment: float = 0.0
    duration_minutes: float = 0.0
    
    # Risk metrics
    risk_reward_ratio: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    def add_trade(self, trade: Trade):
        """Add a trade to the cycle"""
        self.trades.append(trade)
        self._update_metrics()
    
    def complete_cycle(self, end_time: datetime, final_pnl: float):
        """Mark cycle as completed"""
        self.end_time = end_time
        self.status = CycleStatus.COMPLETED
        self.realized_pnl = final_pnl
        self.duration_minutes = (end_time - self.start_time).total_seconds() / 60
        self._calculate_final_metrics()
    
    def _update_metrics(self):
        """Update cycle metrics after adding a trade"""
        if not self.trades:
            return
        
        # Calculate total investment
        buy_trades = [t for t in self.trades if t.trade_type == TradeType.BUY]
        self.total_investment = sum(t.net_value for t in buy_trades)
        self.max_investment = max(self.max_investment, self.total_investment)
    
    def _calculate_final_metrics(self):
        """Calculate final cycle metrics"""
        if not self.trades or self.total_investment == 0:
            return
        
        # Risk-Reward Ratio
        max_risk = self.max_investment
        if max_risk > 0:
            self.risk_reward_ratio = abs(self.realized_pnl) / max_risk
        
        # Profit Factor
        winning_trades = [t for t in self.trades if self._get_trade_pnl(t) > 0]
        losing_trades = [t for t in self.trades if self._get_trade_pnl(t) < 0]
        
        gross_profit = sum(self._get_trade_pnl(t) for t in winning_trades)
        gross_loss = abs(sum(self._get_trade_pnl(t) for t in losing_trades))
        
        if gross_loss > 0:
            self.profit_factor = gross_profit / gross_loss
        else:
            self.profit_factor = float('inf') if gross_profit > 0 else 0
    
    def _get_trade_pnl(self, trade: Trade) -> float:
        """Calculate PnL for a single trade (simplified)"""
        # This is a simplified calculation - in reality, you'd need to match buy/sell pairs
        return 0.0  # Placeholder
    
    @property
    def total_pnl(self) -> float:
        """Total PnL (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def roi_percentage(self) -> float:
        """Return on Investment percentage"""
        if self.total_investment == 0:
            return 0.0
        return (self.realized_pnl / self.total_investment) * 100
    
    @property
    def trade_count(self) -> int:
        """Number of trades in cycle"""
        return len(self.trades)
    
    @property
    def max_order_level(self) -> int:
        """Maximum martingale level reached"""
        if not self.trades:
            return 0
        return max(t.order_level for t in self.trades)

@dataclass
class CycleAnalysisReport:
    """Comprehensive cycle analysis report"""
    cycles: List[Cycle] = field(default_factory=list)
    analysis_period_start: Optional[datetime] = None
    analysis_period_end: Optional[datetime] = None
    
    # Aggregate metrics
    total_cycles: int = 0
    completed_cycles: int = 0
    winning_cycles: int = 0
    losing_cycles: int = 0
    
    # Performance metrics
    total_realized_pnl: float = 0.0
    total_unrealized_pnl: float = 0.0
    average_cycle_pnl: float = 0.0
    best_cycle_pnl: float = 0.0
    worst_cycle_pnl: float = 0.0
    
    # Risk metrics
    overall_profit_factor: float = 0.0
    overall_sharpe_ratio: float = 0.0
    overall_sortino_ratio: float = 0.0
    overall_calmar_ratio: float = 0.0
    maximum_drawdown_ratio: float = 0.0
    
    # Efficiency metrics
    order_completion_efficiency: float = 0.0  # OCE
    return_on_equity: float = 0.0  # ROE
    average_utilization_ratio: float = 0.0  # AUR
    time_weighted_return: float = 0.0  # TWR
    internal_rate_of_return: float = 0.0  # IRR
    maximum_daily_drawdown: float = 0.0  # MDD
    recovery_factor: float = 0.0
    compound_equivalent_rate: float = 0.0  # CER
    
    def add_cycle(self, cycle: Cycle):
        """Add a cycle to the analysis"""
        self.cycles.append(cycle)
        self._update_aggregate_metrics()
    
    def _update_aggregate_metrics(self):
        """Update aggregate metrics"""
        if not self.cycles:
            return
        
        self.total_cycles = len(self.cycles)
        self.completed_cycles = len([c for c in self.cycles if c.status == CycleStatus.COMPLETED])
        
        completed = [c for c in self.cycles if c.status == CycleStatus.COMPLETED]
        if completed:
            self.winning_cycles = len([c for c in completed if c.realized_pnl > 0])
            self.losing_cycles = len([c for c in completed if c.realized_pnl < 0])
            
            self.total_realized_pnl = sum(c.realized_pnl for c in completed)
            self.total_unrealized_pnl = sum(c.unrealized_pnl for c in self.cycles)
            self.average_cycle_pnl = self.total_realized_pnl / len(completed)
            
            cycle_pnls = [c.realized_pnl for c in completed]
            self.best_cycle_pnl = max(cycle_pnls) if cycle_pnls else 0.0
            self.worst_cycle_pnl = min(cycle_pnls) if cycle_pnls else 0.0
            
            self._calculate_advanced_metrics(completed)
    
    def _calculate_advanced_metrics(self, completed_cycles: List[Cycle]):
        """Calculate advanced performance metrics"""
        if not completed_cycles:
            return
        
        # Overall Profit Factor
        winning_cycles = [c for c in completed_cycles if c.realized_pnl > 0]
        losing_cycles = [c for c in completed_cycles if c.realized_pnl < 0]
        
        gross_profit = sum(c.realized_pnl for c in winning_cycles)
        gross_loss = abs(sum(c.realized_pnl for c in losing_cycles))
        
        if gross_loss > 0:
            self.overall_profit_factor = gross_profit / gross_loss
        else:
            self.overall_profit_factor = float('inf') if gross_profit > 0 else 0
        
        # Order Completion Efficiency (OCE)
        total_orders = sum(c.trade_count for c in completed_cycles)
        successful_cycles = len(winning_cycles)
        if total_orders > 0:
            self.order_completion_efficiency = (successful_cycles / len(completed_cycles)) * 100
        
        # Return on Equity (ROE)
        total_investment = sum(c.max_investment for c in completed_cycles)
        if total_investment > 0:
            self.return_on_equity = (self.total_realized_pnl / total_investment) * 100
        
        # Average Utilization Ratio (AUR)
        utilization_ratios = []
        for cycle in completed_cycles:
            if cycle.max_investment > 0:
                utilization = cycle.total_investment / cycle.max_investment
                utilization_ratios.append(utilization)
        
        if utilization_ratios:
            self.average_utilization_ratio = np.mean(utilization_ratios) * 100
        
        # Recovery Factor
        if self.worst_cycle_pnl < 0:
            self.recovery_factor = abs(self.total_realized_pnl / self.worst_cycle_pnl)
        
        # Calculate advanced financial ratios
        self._calculate_sharpe_ratio(completed_cycles)
        self._calculate_sortino_ratio(completed_cycles)
        self._calculate_calmar_ratio(completed_cycles)
        self._calculate_time_weighted_return(completed_cycles)
        self._calculate_internal_rate_of_return(completed_cycles)
        self._calculate_compound_equivalent_rate(completed_cycles)
        self._calculate_maximum_drawdown_detailed(completed_cycles)
    
    def _calculate_sharpe_ratio(self, completed_cycles: List[Cycle]):
        """Calculate Sharpe Ratio (risk-adjusted return)"""
        if not completed_cycles:
            return
        
        # Calculate returns for each cycle
        returns = []
        for cycle in completed_cycles:
            if cycle.max_investment > 0:
                cycle_return = cycle.realized_pnl / cycle.max_investment
                returns.append(cycle_return)
        
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=1)  # Sample standard deviation
            
            if std_return > 0:
                # Assuming risk-free rate of 0 for simplicity
                self.overall_sharpe_ratio = mean_return / std_return
            else:
                self.overall_sharpe_ratio = 0.0
        else:
            self.overall_sharpe_ratio = 0.0
    
    def _calculate_sortino_ratio(self, completed_cycles: List[Cycle]):
        """Calculate Sortino Ratio (downside deviation adjusted return)"""
        if not completed_cycles:
            return
        
        # Calculate returns for each cycle
        returns = []
        for cycle in completed_cycles:
            if cycle.max_investment > 0:
                cycle_return = cycle.realized_pnl / cycle.max_investment
                returns.append(cycle_return)
        
        if len(returns) > 1:
            mean_return = np.mean(returns)
            
            # Calculate downside deviation (only negative returns)
            negative_returns = [r for r in returns if r < 0]
            if negative_returns:
                downside_deviation = np.sqrt(np.mean([r**2 for r in negative_returns]))
                if downside_deviation > 0:
                    self.overall_sortino_ratio = mean_return / downside_deviation
                else:
                    self.overall_sortino_ratio = 0.0
            else:
                # No negative returns, set to high value
                self.overall_sortino_ratio = float('inf') if mean_return > 0 else 0.0
        else:
            self.overall_sortino_ratio = 0.0
    
    def _calculate_calmar_ratio(self, completed_cycles: List[Cycle]):
        """Calculate Calmar Ratio (annual return / maximum drawdown)"""
        if not completed_cycles:
            return
        
        # Calculate annualized return
        total_return = self.total_realized_pnl
        total_investment = sum(c.max_investment for c in completed_cycles)
        
        if total_investment > 0:
            # Calculate time period in years
            if self.analysis_period_start and self.analysis_period_end:
                time_diff = self.analysis_period_end - self.analysis_period_start
                years = time_diff.days / 365.25
                
                if years > 0:
                    annual_return = (total_return / total_investment) / years
                    
                    # Calculate maximum drawdown
                    max_dd = self._calculate_max_drawdown_percentage(completed_cycles)
                    
                    if max_dd > 0:
                        self.overall_calmar_ratio = annual_return / max_dd
                    else:
                        self.overall_calmar_ratio = float('inf') if annual_return > 0 else 0.0
                else:
                    self.overall_calmar_ratio = 0.0
            else:
                self.overall_calmar_ratio = 0.0
        else:
            self.overall_calmar_ratio = 0.0
    
    def _calculate_max_drawdown_percentage(self, completed_cycles: List[Cycle]) -> float:
        """Calculate maximum drawdown as percentage"""
        if not completed_cycles:
            return 0.0
        
        # Sort cycles by start time
        sorted_cycles = sorted(completed_cycles, key=lambda x: x.start_time)
        
        # Calculate cumulative PnL
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for cycle in sorted_cycles:
            cumulative_pnl += cycle.realized_pnl
            
            # Update peak
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            
            # Calculate drawdown from peak
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Convert to percentage
        total_investment = sum(c.max_investment for c in completed_cycles)
        if total_investment > 0:
            return (max_drawdown / total_investment) * 100
        else:
            return 0.0
    
    def _calculate_time_weighted_return(self, completed_cycles: List[Cycle]):
        """Calculate Time Weighted Return (TWR)"""
        if not completed_cycles:
            return
        
        # Sort cycles by start time
        sorted_cycles = sorted(completed_cycles, key=lambda x: x.start_time)
        
        # Calculate period returns
        period_returns = []
        for cycle in sorted_cycles:
            if cycle.max_investment > 0:
                period_return = 1 + (cycle.realized_pnl / cycle.max_investment)
                period_returns.append(period_return)
        
        if period_returns:
            # Calculate geometric mean
            twr = 1.0
            for ret in period_returns:
                twr *= ret
            
            # Convert to percentage
            self.time_weighted_return = (twr - 1) * 100
        else:
            self.time_weighted_return = 0.0
    
    def _calculate_internal_rate_of_return(self, completed_cycles: List[Cycle]):
        """Calculate Internal Rate of Return (IRR) - simplified approximation"""
        if not completed_cycles:
            return
        
        # Create cash flow series
        cash_flows = []
        dates = []
        
        for cycle in completed_cycles:
            # Initial investment (negative cash flow)
            cash_flows.append(-cycle.max_investment)
            dates.append(cycle.start_time)
            
            # Final return (positive cash flow)
            if cycle.end_time:
                final_value = cycle.max_investment + cycle.realized_pnl
                cash_flows.append(final_value)
                dates.append(cycle.end_time)
        
        if len(cash_flows) >= 2:
            # Simplified IRR calculation using XIRR approximation
            try:
                # Calculate weighted average return
                total_invested = sum(abs(cf) for cf in cash_flows if cf < 0)
                total_returned = sum(cf for cf in cash_flows if cf > 0)
                
                if total_invested > 0:
                    # Calculate time period
                    if dates:
                        time_diff = max(dates) - min(dates)
                        years = time_diff.days / 365.25
                        
                        if years > 0:
                            # Simple IRR approximation
                            irr = ((total_returned / total_invested) ** (1/years)) - 1
                            self.internal_rate_of_return = irr * 100
                        else:
                            self.internal_rate_of_return = 0.0
                    else:
                        self.internal_rate_of_return = 0.0
                else:
                    self.internal_rate_of_return = 0.0
            except:
                self.internal_rate_of_return = 0.0
        else:
            self.internal_rate_of_return = 0.0
    
    def _calculate_compound_equivalent_rate(self, completed_cycles: List[Cycle]):
        """Calculate Compound Equivalent Rate (CER)"""
        if not completed_cycles:
            return
        
        # Calculate total return
        total_investment = sum(c.max_investment for c in completed_cycles)
        total_return = self.total_realized_pnl
        
        if total_investment > 0 and self.analysis_period_start and self.analysis_period_end:
            # Calculate time period in years
            time_diff = self.analysis_period_end - self.analysis_period_start
            years = time_diff.days / 365.25
            
            if years > 0:
                # Calculate compound annual growth rate
                final_value = total_investment + total_return
                cer = ((final_value / total_investment) ** (1/years)) - 1
                self.compound_equivalent_rate = cer * 100
            else:
                self.compound_equivalent_rate = 0.0
        else:
            self.compound_equivalent_rate = 0.0
    
    def _calculate_maximum_drawdown_detailed(self, completed_cycles: List[Cycle]):
        """Calculate detailed maximum drawdown metrics"""
        if not completed_cycles:
            return
        
        # Sort cycles by start time
        sorted_cycles = sorted(completed_cycles, key=lambda x: x.start_time)
        
        # Calculate running maximum drawdown
        cumulative_pnl = 0
        peak = 0
        max_drawdown_amount = 0
        max_drawdown_pct = 0
        
        for cycle in sorted_cycles:
            cumulative_pnl += cycle.realized_pnl
            
            # Update peak
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            
            # Calculate drawdown from peak
            drawdown_amount = peak - cumulative_pnl
            if drawdown_amount > max_drawdown_amount:
                max_drawdown_amount = drawdown_amount
        
        # Calculate percentage drawdown
        total_investment = sum(c.max_investment for c in completed_cycles)
        if total_investment > 0:
            max_drawdown_pct = (max_drawdown_amount / total_investment) * 100
        
        self.maximum_drawdown_ratio = max_drawdown_pct
    
    def get_cycle_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all cycles"""
        if not self.cycles:
            return {}
        
        completed = [c for c in self.cycles if c.status == CycleStatus.COMPLETED]
        if not completed:
            return {}
        
        pnls = [c.realized_pnl for c in completed]
        durations = [c.duration_minutes for c in completed]
        investments = [c.total_investment for c in completed]
        
        return {
            'cycle_count': len(completed),
            'win_rate': (self.winning_cycles / len(completed)) * 100 if completed else 0,
            'average_pnl': np.mean(pnls),
            'median_pnl': np.median(pnls),
            'std_pnl': np.std(pnls),
            'average_duration_minutes': np.mean(durations),
            'median_duration_minutes': np.median(durations),
            'average_investment': np.mean(investments),
            'median_investment': np.median(investments),
            'total_trades': sum(c.trade_count for c in completed),
            'average_trades_per_cycle': np.mean([c.trade_count for c in completed]),
            'max_order_level_reached': max(c.max_order_level for c in completed) if completed else 0
        }
    
    def get_strategy_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by strategy type"""
        strategy_stats = {}
        
        for strategy_type in ['CDM', 'WDM', 'ZRM', 'IZRM']:
            strategy_cycles = [c for c in self.cycles if c.strategy_type == strategy_type and c.status == CycleStatus.COMPLETED]
            
            if strategy_cycles:
                pnls = [c.realized_pnl for c in strategy_cycles]
                winning = len([c for c in strategy_cycles if c.realized_pnl > 0])
                
                strategy_stats[strategy_type] = {
                    'cycle_count': len(strategy_cycles),
                    'total_pnl': sum(pnls),
                    'average_pnl': np.mean(pnls),
                    'win_rate': (winning / len(strategy_cycles)) * 100,
                    'best_cycle': max(pnls),
                    'worst_cycle': min(pnls),
                    'total_trades': sum(c.trade_count for c in strategy_cycles)
                }
            else:
                strategy_stats[strategy_type] = {
                    'cycle_count': 0,
                    'total_pnl': 0,
                    'average_pnl': 0,
                    'win_rate': 0,
                    'best_cycle': 0,
                    'worst_cycle': 0,
                    'total_trades': 0
                }
        
        return strategy_stats
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export cycle data to pandas DataFrame for analysis"""
        cycle_data = []
        
        for cycle in self.cycles:
            cycle_data.append({
                'cycle_id': cycle.cycle_id,
                'strategy_type': cycle.strategy_type,
                'symbol': cycle.symbol,
                'start_time': cycle.start_time,
                'end_time': cycle.end_time,
                'status': cycle.status.value,
                'duration_minutes': cycle.duration_minutes,
                'trade_count': cycle.trade_count,
                'max_order_level': cycle.max_order_level,
                'total_investment': cycle.total_investment,
                'max_investment': cycle.max_investment,
                'realized_pnl': cycle.realized_pnl,
                'unrealized_pnl': cycle.unrealized_pnl,
                'total_pnl': cycle.total_pnl,
                'roi_percentage': cycle.roi_percentage,
                'risk_reward_ratio': cycle.risk_reward_ratio,
                'profit_factor': cycle.profit_factor,
                'max_drawdown': cycle.max_drawdown
            })
        
        return pd.DataFrame(cycle_data)
    
    def export_trades_to_dataframe(self) -> pd.DataFrame:
        """Export all trades to pandas DataFrame"""
        trade_data = []
        
        for cycle in self.cycles:
            for trade in cycle.trades:
                trade_data.append({
                    'cycle_id': cycle.cycle_id,
                    'trade_id': trade.trade_id,
                    'timestamp': trade.timestamp,
                    'symbol': trade.symbol,
                    'strategy_type': trade.strategy_type,
                    'trade_type': trade.trade_type.value,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'value': trade.value,
                    'net_value': trade.net_value,
                    'order_level': trade.order_level,
                    'commission': trade.commission
                })
        
        return pd.DataFrame(trade_data)

class CycleAnalyzer:
    """Main class for cycle analysis functionality"""
    
    def __init__(self):
        self.report = CycleAnalysisReport()
        self.active_cycles: Dict[str, Cycle] = {}
    
    def start_cycle(self, cycle_id: str, strategy_type: str, symbol: str, start_time: datetime) -> Cycle:
        """Start a new trading cycle"""
        cycle = Cycle(
            cycle_id=cycle_id,
            strategy_type=strategy_type,
            symbol=symbol,
            start_time=start_time
        )
        
        self.active_cycles[cycle_id] = cycle
        return cycle
    
    def add_trade_to_cycle(self, cycle_id: str, trade: Trade):
        """Add a trade to an active cycle"""
        if cycle_id in self.active_cycles:
            self.active_cycles[cycle_id].add_trade(trade)
    
    def complete_cycle(self, cycle_id: str, end_time: datetime, final_pnl: float):
        """Complete a trading cycle"""
        if cycle_id in self.active_cycles:
            cycle = self.active_cycles[cycle_id]
            cycle.complete_cycle(end_time, final_pnl)
            self.report.add_cycle(cycle)
            del self.active_cycles[cycle_id]
    
    def get_analysis_report(self) -> CycleAnalysisReport:
        """Get the complete analysis report"""
        return self.report
    
    def reset_analysis(self):
        """Reset the analysis (clear all data)"""
        self.report = CycleAnalysisReport()
        self.active_cycles.clear()