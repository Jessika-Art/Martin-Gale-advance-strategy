"""Control Panel for Multi-Martingales Trading Bot"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import os

from config import (
    TradingConfig, IBConfig, SharedSettings, StrategySettings,
    CDMSettings, WDMSettings, ZRMSettings, IZRMSettings,
    AccountType, StrategyType, ExecutionMode
)
from trading_engine import TradingEngine

class ControlPanel:
    """Control panel for managing trading bot parameters and execution"""
    
    def __init__(self, config_file: str = "trading_config.json"):
        self.config_file = config_file
        self.config: Optional[TradingConfig] = None
        self.engine: Optional[TradingEngine] = None
        self.logger = logging.getLogger("ControlPanel")
        
        # Default configuration templates
        self.default_configs = self._create_default_configs()
    
    def _create_default_configs(self) -> Dict[str, Any]:
        """Create default configuration templates"""
        return {
            "ib_config": {
                "host": "127.0.0.1",
                "demo_port": 4002,  # IB Gateway paper trading port
                "live_port": 4001,  # IB Gateway live trading port
                "client_id": 1,
                "timeout": 30
            },
            "shared_settings": {
                # Basic Trading Settings
                "continue_trading": True,
                "pre_after_hours": False,
                "money_management": True,
                "initial_balance": 100000.0,
                "order_type": "MARKET",
                
                # Global Strategy Coordination
                "enable_strategy_coordination": True,
                "global_strategy_alignment": "PARALLEL",
                "global_strategy_to_start_with": "CDM",
                "global_parallel_start_mode": True,
                "global_order_number_to_start": 1,
                "global_sequential_mode_strategy": "CDM",
                "strategy_start_priority": ["CDM", "WDM", "ZRM", "IZRM"],
                
                # Global Position Sizing
                "global_position_size_unit": "PERCENTAGE",
                "global_fixed_position_size": 100.0,
                "global_percentage_of_balance": 5.0,
                "enable_dynamic_sizing": False,
                "dynamic_sizing_factor": 1.0,
                "enable_portfolio_based_sizing": False,
                "portfolio_heat_limit": 2.0,
                
                # Global Risk Management
                "global_max_concurrent_cycles": 5,
                "enable_daily_limits": True,
                "global_daily_loss_limit": 1000.0,
                "global_daily_profit_target": 2000.0,
                "enable_drawdown_protection": True,
                "max_portfolio_drawdown_pct": 10.0,
                "drawdown_calculation_period_days": 30,
                
                # Trading Hours and Order Management
                "enable_trading_hours_restriction": False,
                "trading_start_time": "09:30",
                "trading_end_time": "16:00",
                "enable_order_timeout": True,
                "order_timeout_minutes": 60,
                "max_pending_orders_per_strategy": 10,
                
                # Cycle Management
                "cycle_completion_behavior": "RESTART",
                "max_cycles_per_day": 10,
                "cycle_cooldown_minutes": 5,
                "enable_cycle_profit_target": False,
                "cycle_profit_target_pct": 2.0,
                
                # Money Management
                "growth_threshold": 10000.0,
                "increase_value": 0.1,
                "progressive_reinvestment_step": 0.05,
                "enable_compound_growth": True,
                "compound_frequency_days": 30,
                "capital_allocation_method": "EQUAL",
                
                # Performance and Reporting
                "repeat_on_close": True,
                "backtest_performance_report": True,
                "enable_real_time_metrics": True,
                "performance_calculation_interval_minutes": 15,
                
                # Global Trailing Stops
                "enable_global_trailing_stops": False,
                "global_trailing_stop_pct": 2.0,
                "global_trailing_activation_pct": 1.0,
                "trailing_stop_update_frequency_seconds": 30,
                
                # Exit Conditions
                "enable_emergency_exit": True,
                "emergency_loss_threshold_pct": 15.0,
                "enable_time_based_exit": False,
                "max_position_hold_hours": 24,
                "force_exit_before_close_minutes": 30,
                
                # Notifications
                "enable_notifications": False,
                "notification_methods": [],
                "notify_on_trade_execution": True,
                "notify_on_cycle_completion": True,
                "notify_on_daily_limits": True,
                "notify_on_emergency_exit": True
            },
            "strategy_templates": {
                "CDM": {
                    "enabled": True,
                    "capital_allocation": 0.25,
                    "initial_trade_type": "BUY",
                    "max_orders": 5,
                    "hold_previous": False,
                    "order_distances": [2.0, 3.0, 4.0, 5.0, 6.0],
                    "order_sizes": [1.0, 1.5, 2.0, 2.5, 3.0],
                    "order_tps": [1.0, 1.5, 2.0, 2.5, 3.0],
                    "price_trigger": None
                },
                "WDM": {
                    "enabled": True,
                    "capital_allocation": 0.25,
                    "initial_trade_type": "BUY",
                    "max_orders": 5,
                    "hold_previous": False,
                    "order_distances": [2.0, 3.0, 4.0, 5.0, 6.0],
                    "order_sizes": [1.0, 1.5, 2.0, 2.5, 3.0],
                    "order_sls": [2.0, 3.0, 4.0, 5.0, 6.0],
                    "price_trigger": None
                },
                "ZRM": {
                    "enabled": False,
                    "capital_allocation": 0.25,
                    "initial_trade_type": "BUY",
                    "max_orders": 5,
                    "hold_previous": False,
                    "order_distances": [2.0, 3.0, 4.0, 5.0, 6.0],
                    "order_sizes": [1.0, 1.5, 2.0, 2.5, 3.0],
                    "order_tps": [1.0, 1.5, 2.0, 2.5, 3.0],
                    "zone_center_price": None,
                    "zone_width_pct": 5.0
                },
                "IZRM": {
                    "enabled": False,
                    "capital_allocation": 0.25,
                    "initial_trade_type": "BUY",
                    "max_orders": 5,
                    "hold_previous": False,
                    "order_distances": [2.0, 3.0, 4.0, 5.0, 6.0],
                    "order_sizes": [1.0, 1.5, 2.0, 2.5, 3.0],
                    "order_sls": [2.0, 3.0, 4.0, 5.0, 6.0],
                    "zone_center_price": None,
                    "zone_width_pct": 5.0
                }
            },
            "trading_parameters": {
                "symbols": ["AAPL"],
                "timeframe": "1min",
                "data_range": {
                    "type": "days",  # "days", "hours", "date_range"
                    "value": 30,
                    "start_date": None,
                    "end_date": None
                },
                "execution_mode": "parallel",
                "position_sizing": {
                    "type": "percentage",  # "percentage", "lots", "fixed_amount"
                    "value": 5.0  # 5% of account balance
                }
            }
        }
    
    def create_default_config(self, account_type: str = "demo") -> TradingConfig:
        """Create a default trading configuration"""
        defaults = self.default_configs
        
        # IB Configuration
        ib_config_data = defaults["ib_config"]
        ib_config = IBConfig(
            host=ib_config_data["host"],
            demo_port=ib_config_data["demo_port"],
            live_port=ib_config_data["live_port"],
            client_id=ib_config_data["client_id"],
            timeout=ib_config_data["timeout"]
        )
        
        # Shared Settings
        shared_data = defaults["shared_settings"]
        shared_settings = SharedSettings(
            continue_trading=shared_data["continue_trading"],
            pre_after_hours=shared_data["pre_after_hours"],
            money_management=shared_data["money_management"],
            growth_threshold=shared_data["growth_threshold"],
            increase_value=shared_data["increase_value"],
            progressive_reinvestment_step=shared_data["progressive_reinvestment_step"],
            repeat_on_close=shared_data["repeat_on_close"],
            backtest_performance_report=shared_data["backtest_performance_report"],
            order_type=shared_data["order_type"]
        )
        
        # Strategy Settings
        symbols = defaults["trading_parameters"]["symbols"]
        strategy_settings = {}
        
        for symbol in symbols:
            strategy_settings[symbol] = {}
            
            # CDM Settings
            cdm_data = defaults["strategy_templates"]["CDM"]
            strategy_settings[symbol][StrategyType.CDM] = CDMSettings(
                symbol=symbol,
                enabled=cdm_data["enabled"],
                capital_allocation=cdm_data["capital_allocation"],
                initial_trade_type=cdm_data["initial_trade_type"],
                max_orders=cdm_data["max_orders"],
                hold_previous=cdm_data["hold_previous"],
                order_distances=cdm_data["order_distances"],
                order_sizes=cdm_data["order_sizes"],
                order_tps=cdm_data["order_tps"],
                price_trigger=cdm_data["price_trigger"]
            )
            
            # WDM Settings
            wdm_data = defaults["strategy_templates"]["WDM"]
            strategy_settings[symbol][StrategyType.WDM] = WDMSettings(
                symbol=symbol,
                enabled=wdm_data["enabled"],
                capital_allocation=wdm_data["capital_allocation"],
                initial_trade_type=wdm_data["initial_trade_type"],
                max_orders=wdm_data["max_orders"],
                hold_previous=wdm_data["hold_previous"],
                order_distances=wdm_data["order_distances"],
                order_sizes=wdm_data["order_sizes"],
                order_sls=wdm_data["order_sls"],
                price_trigger=wdm_data["price_trigger"]
            )
            
            # ZRM Settings
            zrm_data = defaults["strategy_templates"]["ZRM"]
            strategy_settings[symbol][StrategyType.ZRM] = ZRMSettings(
                symbol=symbol,
                enabled=zrm_data["enabled"],
                capital_allocation=zrm_data["capital_allocation"],
                initial_trade_type=zrm_data["initial_trade_type"],
                max_orders=zrm_data["max_orders"],
                hold_previous=zrm_data["hold_previous"],
                order_distances=zrm_data["order_distances"],
                order_sizes=zrm_data["order_sizes"],
                order_tps=zrm_data["order_tps"],
                zone_center_price=zrm_data["zone_center_price"],
                zone_width_pct=zrm_data["zone_width_pct"]
            )
            
            # IZRM Settings
            izrm_data = defaults["strategy_templates"]["IZRM"]
            strategy_settings[symbol][StrategyType.IZRM] = IZRMSettings(
                symbol=symbol,
                enabled=izrm_data["enabled"],
                capital_allocation=izrm_data["capital_allocation"],
                initial_trade_type=izrm_data["initial_trade_type"],
                max_orders=izrm_data["max_orders"],
                hold_previous=izrm_data["hold_previous"],
                order_distances=izrm_data["order_distances"],
                order_sizes=izrm_data["order_sizes"],
                order_sls=izrm_data["order_sls"],
                zone_center_price=izrm_data["zone_center_price"],
                zone_width_pct=izrm_data["zone_width_pct"]
            )
        
        # Trading Configuration
        trading_params = defaults["trading_parameters"]
        config = TradingConfig(
            account_type=AccountType(account_type.lower()),
            execution_mode=ExecutionMode(trading_params["execution_mode"]),
            active_strategies=[StrategyType.CDM],  # Default to CDM
            tickers=trading_params["symbols"],
            timeframe=trading_params["timeframe"],
            duration=trading_params.get("duration", "30 D"),
            data_type=trading_params.get("data_type", "TRADES"),
            position_size_type=trading_params.get("position_size_type", "PERCENTAGE"),
            position_size_value=trading_params.get("position_size_value", 5.0),
            ib_config=ib_config,
            shared_settings=shared_settings
        )
        
        return config
    
    def save_config(self, config: TradingConfig, filename: Optional[str] = None) -> bool:
        """Save configuration to JSON file"""
        try:
            if filename is None:
                filename = self.config_file
            
            # Convert config to dictionary
            config_dict = self._config_to_dict(config)
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            self.logger.info(f"Configuration saved to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self, filename: Optional[str] = None) -> Optional[TradingConfig]:
        """Load configuration from JSON file"""
        try:
            if filename is None:
                filename = self.config_file
            
            if not os.path.exists(filename):
                self.logger.warning(f"Configuration file {filename} not found, creating default")
                config = self.create_default_config()
                self.save_config(config, filename)
                return config
            
            with open(filename, 'r') as f:
                config_dict = json.load(f)
            
            # Convert dictionary to config object
            config = self._dict_to_config(config_dict)
            self.config = config
            
            self.logger.info(f"Configuration loaded from {filename}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return None
    
    def _config_to_dict(self, config: TradingConfig) -> Dict[str, Any]:
        """Convert TradingConfig to dictionary"""
        config_dict = {
            "account_type": config.account_type.value,
            "execution_mode": config.execution_mode.value,
            "active_strategies": [s.value for s in config.active_strategies],
            "tickers": config.tickers,
            "timeframe": config.timeframe,
            "duration": config.duration,
            "data_type": config.data_type,
            "position_size_type": config.position_size_type,
            "position_size_value": config.position_size_value,
            "ib_config": asdict(config.ib_config),
            "shared_settings": asdict(config.shared_settings),
            "cdm_settings": asdict(config.cdm_settings),
            "wdm_settings": asdict(config.wdm_settings),
            "zrm_settings": asdict(config.zrm_settings),
            "izrm_settings": asdict(config.izrm_settings)
        }
        
        return config_dict
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> TradingConfig:
        """Convert dictionary to TradingConfig"""
        # IB Config
        ib_data = config_dict["ib_config"]
        ib_config = IBConfig(**ib_data)
        
        # Shared Settings
        shared_data = config_dict["shared_settings"]
        shared_settings = SharedSettings(**shared_data)
        
        # Strategy Settings
        cdm_settings = CDMSettings(**config_dict["cdm_settings"])
        wdm_settings = WDMSettings(**config_dict["wdm_settings"])
        zrm_settings = ZRMSettings(**config_dict["zrm_settings"])
        izrm_settings = IZRMSettings(**config_dict["izrm_settings"])
        
        # Trading Config
        config = TradingConfig(
            account_type=AccountType(config_dict["account_type"]),
            execution_mode=ExecutionMode(config_dict["execution_mode"]),
            active_strategies=[StrategyType(s) for s in config_dict["active_strategies"]],
            tickers=config_dict["tickers"],
            timeframe=config_dict["timeframe"],
            duration=config_dict["duration"],
            data_type=config_dict["data_type"],
            position_size_type=config_dict["position_size_type"],
            position_size_value=config_dict["position_size_value"],
            ib_config=ib_config,
            shared_settings=shared_settings,
            cdm_settings=cdm_settings,
            wdm_settings=wdm_settings,
            zrm_settings=zrm_settings,
            izrm_settings=izrm_settings
        )
        
        return config
    
    def update_account_type(self, account_type: str) -> bool:
        """Update account type (demo/live)"""
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
        
        try:
            if account_type.lower() == "demo":
                self.config.account_type = AccountType.DEMO
            elif account_type.lower() == "live":
                self.config.account_type = AccountType.LIVE
            else:
                self.logger.error(f"Invalid account type: {account_type}")
                return False
            
            self.logger.info(f"Account type updated to {account_type.upper()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update account type: {e}")
            return False
    
    def update_symbols(self, symbols: List[str]) -> bool:
        """Update trading symbols"""
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
        
        try:
            # Update tickers list
            self.config.tickers = symbols
            
            self.logger.info(f"Symbols updated to: {symbols}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update symbols: {e}")
            return False
    

    
    def enable_strategy(self, strategy_type: str, enabled: bool = True) -> bool:
        """Enable/disable a strategy"""
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
        
        try:
            strategy_enum = StrategyType(strategy_type.lower())
            
            if enabled:
                if strategy_enum not in self.config.active_strategies:
                    self.config.active_strategies.append(strategy_enum)
            else:
                if strategy_enum in self.config.active_strategies:
                    self.config.active_strategies.remove(strategy_enum)
            
            # Also update the strategy settings enabled flag
            if strategy_enum == StrategyType.CDM:
                self.config.cdm_settings.enabled = enabled
            elif strategy_enum == StrategyType.WDM:
                self.config.wdm_settings.enabled = enabled
            elif strategy_enum == StrategyType.ZRM:
                self.config.zrm_settings.enabled = enabled
            elif strategy_enum == StrategyType.IZRM:
                self.config.izrm_settings.enabled = enabled
            
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"Strategy {strategy_type} {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update strategy status: {e}")
            return False
    
    def update_position_sizing(self, sizing_type: str, value: float) -> bool:
        """Update position sizing parameters"""
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
        
        try:
            # Update position sizing configuration
            self.config.position_size_type = sizing_type
            self.config.position_size_value = value
            
            self.logger.info(f"Position sizing updated: {sizing_type} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update position sizing: {e}")
            return False
    
    def start_trading(self) -> bool:
        """Start the trading engine"""
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
        
        if self.engine and self.engine.state.value == "RUNNING":
            self.logger.warning("Trading engine is already running")
            return True
        
        try:
            self.engine = TradingEngine(self.config)
            
            if self.engine.start():
                self.logger.info("Trading engine started successfully")
                return True
            else:
                self.logger.error("Failed to start trading engine")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start trading: {e}")
            return False
    
    def stop_trading(self) -> bool:
        """Stop the trading engine"""
        if not self.engine:
            self.logger.warning("No trading engine to stop")
            return True
        
        try:
            self.engine.stop()
            self.logger.info("Trading engine stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop trading: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the trading system"""
        status = {
            "config_loaded": self.config is not None,
            "engine_running": False,
            "engine_status": None,
            "strategy_status": None
        }
        
        if self.config:
            status["account_type"] = self.config.account_type.value
            status["symbols"] = self.config.tickers
            status["enabled_strategies"] = []
            
            # Check enabled strategies
            if self.config.cdm_settings.enabled:
                status["enabled_strategies"].append("CDM")
            if self.config.wdm_settings.enabled:
                status["enabled_strategies"].append("WDM")
            if self.config.zrm_settings.enabled:
                status["enabled_strategies"].append("ZRM")
            if self.config.izrm_settings.enabled:
                status["enabled_strategies"].append("IZRM")
        
        if self.engine:
            status["engine_running"] = self.engine.state.value == "RUNNING"
            status["engine_status"] = self.engine.get_engine_status()
            status["strategy_status"] = self.engine.get_strategy_status()
        
        return status
    
    def force_exit_all(self) -> bool:
        """Force exit all active positions"""
        if not self.engine:
            self.logger.error("No trading engine running")
            return False
        
        try:
            self.engine.force_exit_all()
            self.logger.info("Force exit command sent to all strategies")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to force exit: {e}")
            return False
    
    def validate_configuration(self) -> List[str]:
        """Validate the current configuration"""
        if not self.config:
            return ["No configuration loaded"]
        
        return self.config.validate_configuration()
    
    def update_shared_settings(self, **kwargs) -> bool:
        """Update shared settings parameters"""
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
        
        try:
            shared_settings = self.config.shared_settings
            
            # Update provided parameters
            for key, value in kwargs.items():
                if hasattr(shared_settings, key):
                    setattr(shared_settings, key, value)
                    self.logger.info(f"Updated shared setting {key} = {value}")
                else:
                    self.logger.warning(f"Unknown shared setting: {key}")
            
            # Validate updated settings
            errors = shared_settings.validate_settings()
            if errors:
                self.logger.error(f"Validation errors after update: {errors}")
                return False
            
            # Apply shared settings to strategies
            self.config.apply_shared_settings_to_strategies()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update shared settings: {e}")
            return False
    
    def update_risk_management(self, daily_loss_limit: Optional[float] = None, 
                              daily_profit_target: Optional[float] = None,
                              max_drawdown_pct: Optional[float] = None,
                              max_concurrent_cycles: Optional[int] = None) -> bool:
        """Update risk management settings"""
        updates = {}
        
        if daily_loss_limit is not None:
            updates['global_daily_loss_limit'] = daily_loss_limit
            updates['enable_daily_limits'] = True
        
        if daily_profit_target is not None:
            updates['global_daily_profit_target'] = daily_profit_target
            updates['enable_daily_limits'] = True
        
        if max_drawdown_pct is not None:
            updates['max_portfolio_drawdown_pct'] = max_drawdown_pct
            updates['enable_drawdown_protection'] = True
        
        if max_concurrent_cycles is not None:
            updates['global_max_concurrent_cycles'] = max_concurrent_cycles
        
        return self.update_shared_settings(**updates)
    
    def update_position_sizing_advanced(self, size_unit: str, fixed_size: Optional[float] = None,
                                       percentage: Optional[float] = None,
                                       enable_dynamic: bool = False,
                                       dynamic_factor: float = 1.0) -> bool:
        """Update advanced position sizing settings"""
        updates = {
            'global_position_size_unit': size_unit,
            'enable_dynamic_sizing': enable_dynamic,
            'size_increment_factor': dynamic_factor
        }
        
        if fixed_size is not None:
            updates['global_fixed_position_size'] = fixed_size
        
        if percentage is not None:
            updates['global_percentage_of_portfolio'] = percentage
        
        return self.update_shared_settings(**updates)
    
    def enable_strategy_coordination(self, enabled: bool = True, 
                                   alignment: str = "PARALLEL",
                                   start_strategy: str = "CDM") -> bool:
        """Enable/disable strategy coordination"""
        updates = {
            'enable_strategy_coordination': enabled,
            'global_strategy_alignment': alignment,
            'global_strategy_to_start_with': start_strategy
        }
        
        return self.update_shared_settings(**updates)
    
    def enable_trailing_stops(self, enabled: bool = True,
                             trailing_pct: float = 2.0,
                             activation_pct: float = 1.0) -> bool:
        """Enable/disable global trailing stops"""
        updates = {
            'enable_global_trailing_stops': enabled,
            'global_trailing_stop_pct': trailing_pct,
            'global_trailing_activation_pct': activation_pct
        }
        
        return self.update_shared_settings(**updates)
    
    def get_risk_status(self, current_loss: float = 0.0, current_drawdown_pct: float = 0.0) -> Dict[str, Any]:
        """Get current risk management status"""
        if not self.config:
            return {'error': 'No configuration loaded'}
        
        return self.config.get_risk_limits_status(current_loss, current_drawdown_pct)
    
    def get_shared_settings_summary(self) -> Dict[str, Any]:
        """Get a summary of current shared settings"""
        if not self.config:
            return {'error': 'No configuration loaded'}
        
        shared = self.config.shared_settings
        
        return {
            'strategy_coordination': {
                'enabled': shared.enable_strategy_coordination,
                'alignment': shared.global_strategy_alignment,
                'start_strategy': shared.global_strategy_to_start_with,
                'priority_order': shared.strategy_priority_order
            },
            'position_sizing': {
                'unit': shared.global_position_size_unit,
                'fixed_size': shared.global_fixed_position_size,
                'percentage': shared.global_percentage_of_portfolio,
                'dynamic_enabled': shared.enable_dynamic_sizing
            },
            'risk_management': {
                'daily_limits_enabled': shared.enable_daily_limits,
                'daily_loss_limit': shared.global_daily_loss_limit,
                'daily_profit_target': shared.global_daily_profit_target,
                'drawdown_protection': shared.enable_drawdown_protection,
                'max_drawdown_pct': shared.max_portfolio_drawdown_pct,
                'max_concurrent_cycles': shared.global_max_concurrent_cycles
            },
            'trailing_stops': {
                'enabled': shared.enable_global_trailing_stops,
                'trailing_pct': shared.global_trailing_distance_pct,
                'activation_pct': shared.global_trailing_trigger_pct
            },
            'emergency_exit': {
                'enabled': shared.enable_emergency_exit,
                'threshold_usd': shared.emergency_loss_threshold,
                'threshold_pct': shared.emergency_drawdown_threshold
            }
        }
    
    def print_status(self):
        """Print current status to console"""
        status = self.get_status()
        
        print("\n" + "="*50)
        print("TRADING BOT STATUS")
        print("="*50)
        
        print(f"Configuration Loaded: {status['config_loaded']}")
        
        if status['config_loaded']:
            print(f"Account Type: {status['account_type']}")
            print(f"Symbols: {', '.join(status['symbols'])}")
            print(f"Enabled Strategies: {len(status['enabled_strategies'])}")
            for strategy in status['enabled_strategies']:
                print(f"  - {strategy}")
            
            # Print shared settings summary
            shared_summary = self.get_shared_settings_summary()
            if 'error' not in shared_summary:
                print("\nShared Settings:")
                print(f"  Strategy Coordination: {shared_summary['strategy_coordination']['enabled']}")
                print(f"  Position Sizing: {shared_summary['position_sizing']['unit']}")
                print(f"  Daily Limits: {shared_summary['risk_management']['daily_limits_enabled']}")
                print(f"  Trailing Stops: {shared_summary['trailing_stops']['enabled']}")
                print(f"  Emergency Exit: {shared_summary['emergency_exit']['enabled']}")
        
        print(f"\nEngine Running: {status['engine_running']}")
        
        if status['engine_status']:
            engine_status = status['engine_status']
            print(f"Engine State: {engine_status['state']}")
            print(f"Uptime: {engine_status['uptime_seconds']:.0f} seconds")
            print(f"Active Strategies: {engine_status['active_strategies']}")
            print(f"Pending Orders: {engine_status['pending_orders']}")
            print(f"Total Trades: {engine_status['total_trades']}")
            print(f"Total PnL: ${engine_status['total_pnl']:.2f}")
            print(f"Account Balance: ${engine_status['account_balance']:.2f}")
        
        if status['strategy_status']:
            print("\nStrategy Details:")
            for strategy_key, strategy_info in status['strategy_status'].items():
                print(f"  {strategy_key}:")
                print(f"    Active: {strategy_info['is_active']}")
                print(f"    Current Leg: {strategy_info['current_leg']}")
                print(f"    Positions: {strategy_info['positions']}")
                print(f"    Unrealized PnL: ${strategy_info['unrealized_pnl']:.2f}")
                print(f"    Win Rate: {strategy_info['win_rate']:.1f}%")
        
        print("="*50 + "\n")

# Example usage functions
def create_sample_config():
    """Create and save a sample configuration"""
    panel = ControlPanel()
    
    # Create default config
    config = panel.create_default_config("demo")
    
    # Customize for example
    config.symbols = ["AAPL", "TSLA"]
    
    # Enable CDM and WDM strategies
    for symbol in config.symbols:
        config.strategy_settings[symbol][StrategyType.CDM].enabled = True
        config.strategy_settings[symbol][StrategyType.WDM].enabled = True
        config.strategy_settings[symbol][StrategyType.ZRM].enabled = False
        config.strategy_settings[symbol][StrategyType.IZRM].enabled = False
    
    # Save configuration
    panel.save_config(config, "sample_config.json")
    print("Sample configuration created: sample_config.json")

def quick_start_demo():
    """Quick start with demo account"""
    panel = ControlPanel("demo_config.json")
    
    # Load or create config
    config = panel.load_config()
    if not config:
        config = panel.create_default_config("demo")
        panel.save_config(config)
    
    # Update to demo account
    panel.update_account_type("demo")
    
    # Set symbols
    panel.update_symbols(["AAPL"])
    
    # Enable only CDM strategy
    panel.enable_strategy("CDM", True)
    panel.enable_strategy("WDM", False)
    panel.enable_strategy("ZRM", False)
    panel.enable_strategy("IZRM", False)
    
    # Save updated config
    panel.save_config(panel.config)
    
    print("Demo configuration ready. Use panel.start_trading() to begin.")
    return panel

if __name__ == "__main__":
    # Create sample configuration
    create_sample_config()
    
    # Quick demo setup
    panel = quick_start_demo()
    panel.print_status()