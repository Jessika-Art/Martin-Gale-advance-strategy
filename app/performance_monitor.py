#!/usr/bin/env python3
"""
Performance Monitor for MartinGales Trading Bot
Helps identify memory leaks and performance issues
"""

import psutil
import time
import logging
from datetime import datetime
from typing import Dict, List

class PerformanceMonitor:
    """Monitor system performance and detect issues"""
    
    def __init__(self, log_file: str = "performance.log"):
        self.logger = logging.getLogger("PerformanceMonitor")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.process = psutil.Process()
        self.baseline_memory = None
        self.memory_samples = []
        self.cpu_samples = []
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return self.process.cpu_percent()
    
    def record_baseline(self):
        """Record baseline memory usage"""
        self.baseline_memory = self.get_memory_usage()
        self.logger.info(f"Baseline memory usage: {self.baseline_memory:.2f} MB")
    
    def check_memory_leak(self, threshold_mb: float = 100) -> bool:
        """Check for potential memory leaks"""
        current_memory = self.get_memory_usage()
        self.memory_samples.append(current_memory)
        
        # Keep only last 10 samples
        if len(self.memory_samples) > 10:
            self.memory_samples.pop(0)
        
        if self.baseline_memory and current_memory > self.baseline_memory + threshold_mb:
            self.logger.warning(f"Potential memory leak detected: {current_memory:.2f} MB (baseline: {self.baseline_memory:.2f} MB)")
            return True
        
        return False
    
    def check_cpu_usage(self, threshold_percent: float = 80) -> bool:
        """Check for high CPU usage"""
        current_cpu = self.get_cpu_usage()
        self.cpu_samples.append(current_cpu)
        
        # Keep only last 5 samples
        if len(self.cpu_samples) > 5:
            self.cpu_samples.pop(0)
        
        # Check if CPU usage is consistently high
        if len(self.cpu_samples) >= 3 and all(cpu > threshold_percent for cpu in self.cpu_samples[-3:]):
            self.logger.warning(f"High CPU usage detected: {current_cpu:.2f}%")
            return True
        
        return False
    
    def get_performance_report(self) -> Dict:
        """Get current performance metrics"""
        return {
            'memory_mb': self.get_memory_usage(),
            'cpu_percent': self.get_cpu_usage(),
            'baseline_memory_mb': self.baseline_memory,
            'memory_samples': self.memory_samples.copy(),
            'cpu_samples': self.cpu_samples.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def log_performance(self):
        """Log current performance metrics"""
        report = self.get_performance_report()
        self.logger.info(f"Performance: Memory={report['memory_mb']:.2f}MB, CPU={report['cpu_percent']:.2f}%")
        
        # Check for issues
        self.check_memory_leak()
        self.check_cpu_usage()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()