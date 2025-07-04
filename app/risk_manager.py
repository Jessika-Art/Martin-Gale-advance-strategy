from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Optional
import logging
from enum import Enum

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class DailyRiskMetrics:
    """Daily risk tracking metrics"""
    date: date
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    active_cycles: int = 0
    completed_cycles: int = 0
    max_drawdown: float = 0.0
    peak_equity: float = 0.0
    trades_count: int = 0
    commission_paid: float = 0.0

class GlobalRiskManager:
    """Global risk management system for all strategies"""
    
    def __init__(self, max_concurrent_cycles: int = 3, 
                 daily_loss_limit: float = 1000.0, 
                 daily_profit_target: float = 2000.0,
                 enable_daily_limits: bool = True,
                 max_cycles_per_day: int = 100):
        self.max_concurrent_cycles = max_concurrent_cycles
        self.daily_loss_limit = daily_loss_limit
        self.daily_profit_target = daily_profit_target
        self.enable_daily_limits = enable_daily_limits
        self.max_cycles_per_day = max_cycles_per_day
        
        # Daily tracking
        self.daily_metrics: Dict[date, DailyRiskMetrics] = {}
        self.current_date = date.today()
        
        # Active cycle tracking
        self.active_cycles: Dict[str, str] = {}  # cycle_id -> strategy_type
        
        # Risk state
        self.trading_halted = False
        self.halt_reason = ""
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize today's metrics
        self._ensure_daily_metrics(self.current_date)
    
    def _ensure_daily_metrics(self, target_date: date):
        """Ensure daily metrics exist for the target date"""
        if target_date not in self.daily_metrics:
            self.daily_metrics[target_date] = DailyRiskMetrics(date=target_date)
    
    def update_daily_date(self, new_date: date):
        """Update current date and reset daily metrics if needed"""
        if new_date != self.current_date:
            self.current_date = new_date
            self._ensure_daily_metrics(new_date)
            # Reset trading halt for new day
            if self.trading_halted and "daily" in self.halt_reason.lower():
                self.resume_trading()
    
    def can_start_new_cycle(self, strategy_type: str) -> tuple[bool, str]:
        """Check if a new cycle can be started"""
        # Check if trading is halted
        if self.trading_halted:
            return False, f"Trading halted: {self.halt_reason}"
        
        # Check concurrent cycles limit
        if len(self.active_cycles) >= self.max_concurrent_cycles:
            return False, f"Maximum concurrent cycles reached ({self.max_concurrent_cycles})"
        
        # Check daily loss limit
        today_metrics = self.daily_metrics.get(self.current_date)
        if today_metrics and today_metrics.total_pnl <= -self.daily_loss_limit:
            self.halt_trading(f"Daily loss limit reached: ${today_metrics.total_pnl:.2f}")
            return False, self.halt_reason
        
        # Check daily profit target (halt if daily limits enabled)
        if today_metrics and today_metrics.total_pnl >= self.daily_profit_target:
            if self.enable_daily_limits:
                self.halt_trading(f"Daily profit target reached: ${today_metrics.total_pnl:.2f}")
                return False, self.halt_reason
            else:
                self.logger.info(f"Daily profit target reached: ${today_metrics.total_pnl:.2f} (continuing trading)")
        
        # Check daily cycle limit
        if today_metrics and today_metrics.completed_cycles >= self.max_cycles_per_day:
            return False, f"Daily cycle limit reached ({self.max_cycles_per_day})"
        
        return True, "OK"
    
    def register_cycle_start(self, cycle_id: str, strategy_type: str):
        """Register a new cycle start"""
        self.active_cycles[cycle_id] = strategy_type
        today_metrics = self.daily_metrics[self.current_date]
        today_metrics.active_cycles = len(self.active_cycles)
        
        self.logger.info(f"Cycle started: {cycle_id} ({strategy_type}). Active cycles: {len(self.active_cycles)}")
    
    def register_cycle_end(self, cycle_id: str, cycle_pnl: float):
        """Register a cycle completion"""
        if cycle_id in self.active_cycles:
            strategy_type = self.active_cycles.pop(cycle_id)
            
            today_metrics = self.daily_metrics[self.current_date]
            today_metrics.active_cycles = len(self.active_cycles)
            today_metrics.completed_cycles += 1
            today_metrics.realized_pnl += cycle_pnl
            today_metrics.total_pnl += cycle_pnl
            
            # Update peak equity and drawdown
            if today_metrics.total_pnl > today_metrics.peak_equity:
                today_metrics.peak_equity = today_metrics.total_pnl
            
            current_drawdown = today_metrics.peak_equity - today_metrics.total_pnl
            if current_drawdown > today_metrics.max_drawdown:
                today_metrics.max_drawdown = current_drawdown
            
            self.logger.info(f"Cycle completed: {cycle_id} ({strategy_type}). PnL: ${cycle_pnl:.2f}. Active cycles: {len(self.active_cycles)}")
            
            # Check risk limits after cycle completion
            self._check_risk_limits()
    
    def update_unrealized_pnl(self, total_unrealized: float):
        """Update total unrealized PnL"""
        today_metrics = self.daily_metrics[self.current_date]
        today_metrics.unrealized_pnl = total_unrealized
        today_metrics.total_pnl = today_metrics.realized_pnl + total_unrealized
        
        # Update peak equity and drawdown
        if today_metrics.total_pnl > today_metrics.peak_equity:
            today_metrics.peak_equity = today_metrics.total_pnl
        
        current_drawdown = today_metrics.peak_equity - today_metrics.total_pnl
        if current_drawdown > today_metrics.max_drawdown:
            today_metrics.max_drawdown = current_drawdown
    
    def register_trade(self, trade_value: float, commission: float = 0.0):
        """Register a trade execution"""
        today_metrics = self.daily_metrics[self.current_date]
        today_metrics.trades_count += 1
        today_metrics.commission_paid += commission
    
    def _check_risk_limits(self):
        """Check if risk limits have been breached"""
        today_metrics = self.daily_metrics[self.current_date]
        
        # Check daily loss limit
        if today_metrics.total_pnl <= -self.daily_loss_limit:
            self.halt_trading(f"Daily loss limit breached: ${today_metrics.total_pnl:.2f}")
    
    def halt_trading(self, reason: str):
        """Halt all trading activities"""
        self.trading_halted = True
        self.halt_reason = reason
        self.logger.warning(f"TRADING HALTED: {reason}")
    
    def resume_trading(self):
        """Resume trading activities"""
        self.trading_halted = False
        self.halt_reason = ""
        self.logger.info("Trading resumed")
    
    def get_current_risk_level(self) -> RiskLevel:
        """Assess current risk level"""
        today_metrics = self.daily_metrics[self.current_date]
        
        # Calculate risk factors
        loss_ratio = abs(today_metrics.total_pnl) / self.daily_loss_limit if today_metrics.total_pnl < 0 else 0
        cycle_ratio = len(self.active_cycles) / self.max_concurrent_cycles
        drawdown_ratio = today_metrics.max_drawdown / self.daily_loss_limit if self.daily_loss_limit > 0 else 0
        
        max_ratio = max(loss_ratio, cycle_ratio, drawdown_ratio)
        
        if max_ratio >= 0.9:
            return RiskLevel.CRITICAL
        elif max_ratio >= 0.7:
            return RiskLevel.HIGH
        elif max_ratio >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_daily_summary(self, target_date: Optional[date] = None) -> DailyRiskMetrics:
        """Get daily risk summary"""
        if target_date is None:
            target_date = self.current_date
        
        return self.daily_metrics.get(target_date, DailyRiskMetrics(date=target_date))
    
    def get_risk_status(self) -> Dict:
        """Get comprehensive risk status"""
        today_metrics = self.daily_metrics[self.current_date]
        risk_level = self.get_current_risk_level()
        
        # Generate warnings
        warnings = []
        if today_metrics.total_pnl <= -self.daily_loss_limit * 0.8:
            warnings.append("Approaching daily loss limit")
        if len(self.active_cycles) >= self.max_concurrent_cycles * 0.8:
            warnings.append("High cycle capacity usage")
        if today_metrics.max_drawdown >= self.daily_loss_limit * 0.5:
            warnings.append("Significant drawdown detected")
        
        can_start, _ = self.can_start_new_cycle("TEST")
        
        return {
            'daily_metrics': {
                'daily_realized_pnl': today_metrics.realized_pnl,
                'daily_unrealized_pnl': today_metrics.unrealized_pnl,
                'total_daily_pnl': today_metrics.total_pnl,
                'active_cycles': len(self.active_cycles),
                'total_trades_today': today_metrics.trades_count,
                'total_commission_today': today_metrics.commission_paid,
                'max_drawdown': today_metrics.max_drawdown,
                'peak_equity': today_metrics.peak_equity,
                'completed_cycles': today_metrics.completed_cycles
            },
            'limits': {
                'daily_loss_limit': self.daily_loss_limit,
                'daily_profit_target': self.daily_profit_target,
                'max_concurrent_cycles': self.max_concurrent_cycles
            },
            'status': {
                'trading_halted': self.trading_halted,
                'halt_reason': self.halt_reason,
                'risk_level': risk_level.value,
                'can_start_new_cycle': can_start,
                'warnings': warnings,
                'loss_limit_usage': abs(today_metrics.total_pnl) / self.daily_loss_limit if today_metrics.total_pnl < 0 else 0,
                'cycle_capacity_usage': len(self.active_cycles) / self.max_concurrent_cycles if self.max_concurrent_cycles > 0 else 0
            }
        }
    
    def reset_daily_limits(self):
        """Reset daily limits (for new trading day)"""
        self.current_date = date.today()
        self._ensure_daily_metrics(self.current_date)
        if self.trading_halted and "daily" in self.halt_reason.lower():
            self.resume_trading()