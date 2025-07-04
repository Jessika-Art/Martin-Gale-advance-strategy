import numpy as np
import pandas as pd
from typing import List, Optional
from scipy.optimize import fsolve
import warnings

def calculate_irr(cash_flows: List[float], periods: Optional[List[int]] = None) -> float:
    """
    Calculate Internal Rate of Return (IRR) for a series of cash flows.
    
    Args:
        cash_flows: List of cash flows (negative for investments, positive for returns)
        periods: List of periods corresponding to cash flows (optional)
    
    Returns:
        IRR as a decimal (e.g., 0.15 for 15%)
    """
    if not cash_flows or len(cash_flows) < 2:
        return 0.0
    
    # If periods not provided, assume regular intervals
    if periods is None:
        periods = list(range(len(cash_flows)))
    
    def npv(rate):
        """Calculate Net Present Value for given rate"""
        return sum(cf / (1 + rate) ** period for cf, period in zip(cash_flows, periods))
    
    try:
        # Use scipy to find the rate where NPV = 0
        irr = fsolve(npv, 0.1)[0]
        
        # Validate the result
        if abs(npv(irr)) > 1e-6:  # If NPV is not close to zero
            return 0.0
            
        return irr
    except:
        return 0.0

def calculate_recovery_factor(equity_curve: np.ndarray) -> float:
    """
    Calculate Recovery Factor: Net Profit / Maximum Drawdown.
    
    Args:
        equity_curve: Array of equity values over time
    
    Returns:
        Recovery factor as a ratio
    """
    if len(equity_curve) < 2:
        return 0.0
    
    # Calculate net profit
    net_profit = equity_curve[-1] - equity_curve[0]
    
    # Calculate maximum drawdown
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (peak - equity_curve) / peak
    max_drawdown = np.max(drawdown)
    
    if max_drawdown == 0:
        return float('inf') if net_profit > 0 else 0.0
    
    return net_profit / (equity_curve[0] * max_drawdown)

def calculate_sterling_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sterling Ratio: (Annual Return - Risk Free Rate) / Average Drawdown.
    
    Args:
        returns: Series of periodic returns
        risk_free_rate: Risk-free rate (annual)
    
    Returns:
        Sterling ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate annual return
    annual_return = (1 + returns.mean()) ** 252 - 1  # Assuming daily returns
    
    # Calculate equity curve from returns
    equity_curve = (1 + returns).cumprod()
    
    # Calculate drawdowns
    peak = equity_curve.expanding().max()
    drawdown = (peak - equity_curve) / peak
    
    # Average drawdown (excluding zero drawdowns)
    avg_drawdown = drawdown[drawdown > 0].mean()
    
    if pd.isna(avg_drawdown) or avg_drawdown == 0:
        return float('inf') if annual_return > risk_free_rate else 0.0
    
    return (annual_return - risk_free_rate) / avg_drawdown

def calculate_burke_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Burke Ratio: (Annual Return - Risk Free Rate) / sqrt(sum(drawdown^2)).
    
    Args:
        returns: Series of periodic returns
        risk_free_rate: Risk-free rate (annual)
    
    Returns:
        Burke ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate annual return
    annual_return = (1 + returns.mean()) ** 252 - 1  # Assuming daily returns
    
    # Calculate equity curve from returns
    equity_curve = (1 + returns).cumprod()
    
    # Calculate drawdowns
    peak = equity_curve.expanding().max()
    drawdown = (peak - equity_curve) / peak
    
    # Burke ratio denominator: sqrt of sum of squared drawdowns
    burke_denominator = np.sqrt((drawdown ** 2).sum())
    
    if burke_denominator == 0:
        return float('inf') if annual_return > risk_free_rate else 0.0
    
    return (annual_return - risk_free_rate) / burke_denominator

def calculate_martin_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Martin Ratio: (Annual Return - Risk Free Rate) / Ulcer Index.
    Ulcer Index = sqrt(mean(drawdown^2))
    
    Args:
        returns: Series of periodic returns
        risk_free_rate: Risk-free rate (annual)
    
    Returns:
        Martin ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate annual return
    annual_return = (1 + returns.mean()) ** 252 - 1  # Assuming daily returns
    
    # Calculate equity curve from returns
    equity_curve = (1 + returns).cumprod()
    
    # Calculate drawdowns
    peak = equity_curve.expanding().max()
    drawdown = (peak - equity_curve) / peak
    
    # Ulcer Index: sqrt of mean squared drawdown
    ulcer_index = np.sqrt((drawdown ** 2).mean())
    
    if ulcer_index == 0:
        return float('inf') if annual_return > risk_free_rate else 0.0
    
    return (annual_return - risk_free_rate) / ulcer_index

def calculate_pain_index(returns: pd.Series) -> float:
    """
    Calculate Pain Index: Mean of all drawdowns.
    
    Args:
        returns: Series of periodic returns
    
    Returns:
        Pain index as percentage
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate equity curve from returns
    equity_curve = (1 + returns).cumprod()
    
    # Calculate drawdowns
    peak = equity_curve.expanding().max()
    drawdown = (peak - equity_curve) / peak
    
    return drawdown.mean() * 100

def calculate_gain_to_pain_ratio(returns: pd.Series) -> float:
    """
    Calculate Gain-to-Pain Ratio: Total Return / Pain Index.
    
    Args:
        returns: Series of periodic returns
    
    Returns:
        Gain-to-Pain ratio
    """
    if len(returns) < 2:
        return 0.0
    
    total_return = (1 + returns).prod() - 1
    pain_index = calculate_pain_index(returns) / 100  # Convert back to decimal
    
    if pain_index == 0:
        return float('inf') if total_return > 0 else 0.0
    
    return total_return / pain_index

def calculate_lake_ratio(returns: pd.Series) -> float:
    """
    Calculate Lake Ratio: Measures the percentage of time spent in drawdown.
    
    Args:
        returns: Series of periodic returns
    
    Returns:
        Lake ratio as percentage
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate equity curve from returns
    equity_curve = (1 + returns).cumprod()
    
    # Calculate drawdowns
    peak = equity_curve.expanding().max()
    in_drawdown = equity_curve < peak
    
    return (in_drawdown.sum() / len(in_drawdown)) * 100

def calculate_comprehensive_metrics(equity_curve: np.ndarray, returns: pd.Series = None, 
                                  risk_free_rate: float = 0.0) -> dict:
    """
    Calculate a comprehensive set of advanced financial metrics.
    
    Args:
        equity_curve: Array of equity values over time
        returns: Series of periodic returns (optional, will be calculated if not provided)
        risk_free_rate: Risk-free rate (annual)
    
    Returns:
        Dictionary of calculated metrics
    """
    metrics = {}
    
    # Calculate returns if not provided
    if returns is None and len(equity_curve) > 1:
        returns = pd.Series(np.diff(equity_curve) / equity_curve[:-1])
    
    # Recovery Factor
    metrics['Recovery Factor'] = calculate_recovery_factor(equity_curve)
    
    if returns is not None and len(returns) > 1:
        # Advanced ratios
        metrics['Sterling Ratio'] = calculate_sterling_ratio(returns, risk_free_rate)
        metrics['Burke Ratio'] = calculate_burke_ratio(returns, risk_free_rate)
        metrics['Martin Ratio'] = calculate_martin_ratio(returns, risk_free_rate)
        
        # Pain-based metrics
        metrics['Pain Index'] = calculate_pain_index(returns)
        metrics['Gain-to-Pain Ratio'] = calculate_gain_to_pain_ratio(returns)
        metrics['Lake Ratio'] = calculate_lake_ratio(returns)
        
        # IRR calculation (simplified for equity curve)
        if len(equity_curve) > 1:
            cash_flows = [-equity_curve[0]] + [0] * (len(equity_curve) - 2) + [equity_curve[-1]]
            metrics['IRR'] = calculate_irr(cash_flows) * 100  # Convert to percentage
    
    return metrics

def format_metric_value(value: float, metric_name: str) -> str:
    """
    Format metric values for display.
    
    Args:
        value: The metric value
        metric_name: Name of the metric
    
    Returns:
        Formatted string representation
    """
    if pd.isna(value) or value == 0:
        return "N/A"
    
    if value == float('inf'):
        return "∞"
    
    if value == float('-inf'):
        return "-∞"
    
    # Percentage metrics
    if any(keyword in metric_name.lower() for keyword in ['index', 'ratio', 'irr']):
        if 'ratio' in metric_name.lower() and metric_name.lower() not in ['lake ratio', 'gain-to-pain ratio']:
            return f"{value:.3f}"
        else:
            return f"{value:.2f}%"
    
    # Regular ratios
    return f"{value:.3f}"