"""
Configuration Manager for AI Gold Grid Trading System v3.0
Centralized configuration management with hot-reload capability
"""

import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Centralized configuration management with hot-reload and validation"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.last_modified = 0
        self.reload_callbacks: Dict[str, Callable] = {}
        self.lock = threading.RLock()
        self.hot_reload_enabled = True
        self.validation_rules = self._setup_validation_rules()
        
        # Load initial configuration
        self.load_config()
        
        # Start hot-reload monitoring if enabled
        if self.hot_reload_enabled:
            self._start_hot_reload_monitor()
    
    def _setup_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Setup validation rules for configuration parameters"""
        return {
            "trading_parameters.base_lot_size": {"type": float, "min": 0.01, "max": 1.0},
            "trading_parameters.max_lot_size": {"type": float, "min": 0.01, "max": 10.0},
            "trading_parameters.max_positions": {"type": int, "min": 1, "max": 200},
            "trading_parameters.min_margin_level": {"type": float, "min": 100.0, "max": 1000.0},
            "trading_parameters.signal_cooldown": {"type": int, "min": 1, "max": 300},
            "trading_parameters.max_signals_per_hour": {"type": int, "min": 1, "max": 100},
            
            "decision_weights.safety_check": {"type": float, "min": 0.0, "max": 1.0},
            "decision_weights.portfolio_health": {"type": float, "min": 0.0, "max": 1.0},
            "decision_weights.zone_distribution": {"type": float, "min": 0.0, "max": 1.0},
            "decision_weights.balance_optimization": {"type": float, "min": 0.0, "max": 1.0},
            "decision_weights.signal_quality": {"type": float, "min": 0.0, "max": 1.0},
            
            "portfolio_management.balance_target_ratio": {"type": float, "min": 0.1, "max": 0.9},
            "portfolio_management.balance_tolerance": {"type": float, "min": 0.05, "max": 0.3},
            "portfolio_management.redirect_threshold": {"type": float, "min": 0.5, "max": 0.8},
            "portfolio_management.max_redirect_ratio": {"type": float, "min": 0.1, "max": 0.8},
            
            "zone_based_trading.zone_size_pips": {"type": int, "min": 5, "max": 100},
            "zone_based_trading.max_positions_per_zone": {"type": int, "min": 1, "max": 10},
            "zone_based_trading.zone_cache_ttl": {"type": int, "min": 10, "max": 300},
            
            "lot_sizing.risk_percent_range": {"type": list, "length": 2},
            "lot_sizing.stop_loss_pips": {"type": int, "min": 10, "max": 200},
            
            "performance_optimization.max_cache_size": {"type": int, "min": 100, "max": 10000},
            "performance_optimization.cleanup_interval": {"type": int, "min": 60, "max": 3600}
        }
    
    def load_config(self) -> bool:
        """Load configuration from file with validation"""
        try:
            with self.lock:
                if not os.path.exists(self.config_path):
                    logger.error(f"Configuration file not found: {self.config_path}")
                    self._create_default_config()
                    return False
                
                # Check file modification time
                current_modified = os.path.getmtime(self.config_path)
                if current_modified <= self.last_modified:
                    return True  # No changes
                
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    new_config = json.load(f)
                
                # Validate configuration
                if self._validate_config(new_config):
                    old_config = self.config.copy()
                    self.config = new_config
                    self.last_modified = current_modified
                    
                    # Trigger callbacks for changed sections
                    self._trigger_reload_callbacks(old_config, new_config)
                    
                    logger.info("Configuration loaded successfully")
                    return True
                else:
                    logger.error("Configuration validation failed")
                    return False
                    
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against rules"""
        try:
            # Check decision weights sum to approximately 1.0
            weights = config.get("decision_weights", {})
            if weights:
                total_weight = sum(weights.values())
                if not (0.95 <= total_weight <= 1.05):
                    logger.error(f"Decision weights must sum to ~1.0, got {total_weight}")
                    return False
            
            # Validate individual parameters
            for rule_path, rules in self.validation_rules.items():
                value = self._get_nested_value(config, rule_path)
                if value is not None:
                    if not self._validate_parameter(value, rules, rule_path):
                        return False
            
            # Custom validation logic
            lot_range = config.get("lot_sizing", {}).get("lot_multiplier_range", [])
            if len(lot_range) == 2 and lot_range[0] >= lot_range[1]:
                logger.error("lot_multiplier_range: min must be less than max")
                return False
            
            risk_range = config.get("lot_sizing", {}).get("risk_percent_range", [])
            if len(risk_range) == 2 and risk_range[0] >= risk_range[1]:
                logger.error("risk_percent_range: min must be less than max")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {str(e)}")
            return False
    
    def _validate_parameter(self, value: Any, rules: Dict[str, Any], path: str) -> bool:
        """Validate a single parameter against its rules"""
        try:
            # Type check
            expected_type = rules.get("type")
            if expected_type and not isinstance(value, expected_type):
                logger.error(f"{path}: Expected {expected_type.__name__}, got {type(value).__name__}")
                return False
            
            # Range checks for numbers
            if isinstance(value, (int, float)):
                if "min" in rules and value < rules["min"]:
                    logger.error(f"{path}: Value {value} below minimum {rules['min']}")
                    return False
                if "max" in rules and value > rules["max"]:
                    logger.error(f"{path}: Value {value} above maximum {rules['max']}")
                    return False
            
            # Length check for lists
            if isinstance(value, list) and "length" in rules:
                if len(value) != rules["length"]:
                    logger.error(f"{path}: Expected length {rules['length']}, got {len(value)}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation error for {path}: {str(e)}")
            return False
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get nested configuration value using dot notation"""
        try:
            keys = path.split('.')
            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        except:
            return None
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "trading_parameters": {
                "symbol": "XAUUSD.v",
                "base_lot_size": 0.01,
                "max_lot_size": 0.10,
                "max_positions": 50,
                "min_margin_level": 200.0,
                "signal_cooldown": 60,
                "max_signals_per_hour": 40
            },
            "decision_weights": {
                "safety_check": 0.35,
                "portfolio_health": 0.25,
                "zone_distribution": 0.20,
                "balance_optimization": 0.15,
                "signal_quality": 0.05
            }
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration file: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default config: {str(e)}")
    
    def _start_hot_reload_monitor(self):
        """Start background thread for hot-reload monitoring"""
        def monitor():
            while self.hot_reload_enabled:
                try:
                    time.sleep(5)  # Check every 5 seconds
                    self.load_config()
                except Exception as e:
                    logger.error(f"Hot-reload monitor error: {str(e)}")
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("Hot-reload monitoring started")
    
    def _trigger_reload_callbacks(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Trigger registered callbacks for configuration changes"""
        try:
            for section, callback in self.reload_callbacks.items():
                old_section = old_config.get(section, {})
                new_section = new_config.get(section, {})
                if old_section != new_section:
                    try:
                        callback(old_section, new_section)
                        logger.info(f"Reload callback triggered for section: {section}")
                    except Exception as e:
                        logger.error(f"Reload callback error for {section}: {str(e)}")
        except Exception as e:
            logger.error(f"Error triggering reload callbacks: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        with self.lock:
            return self._get_nested_value(self.config, key) or default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        with self.lock:
            return self.config.get(section, {})
    
    def register_reload_callback(self, section: str, callback: Callable):
        """Register callback for configuration section changes"""
        self.reload_callbacks[section] = callback
        logger.info(f"Registered reload callback for section: {section}")
    
    def update(self, key: str, value: Any) -> bool:
        """Update configuration value at runtime"""
        try:
            with self.lock:
                # Create a test config to validate the change
                test_config = json.loads(json.dumps(self.config))  # Deep copy
                self._set_nested_value(test_config, key, value)
                
                if self._validate_config(test_config):
                    # Apply the change
                    old_config = self.config.copy()
                    self._set_nested_value(self.config, key, value)
                    
                    # Save to file
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=2)
                    
                    # Trigger callbacks
                    self._trigger_reload_callbacks(old_config, self.config)
                    
                    logger.info(f"Configuration updated: {key} = {value}")
                    return True
                else:
                    logger.error(f"Configuration update failed validation: {key} = {value}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating configuration {key}: {str(e)}")
            return False
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings for optimization"""
        return {
            "cache_enabled": self.get("performance_optimization.enable_caching", True),
            "cache_hot_threshold": self.get("performance_optimization.cache_hot_threshold", 10),
            "cache_warm_threshold": self.get("performance_optimization.cache_warm_threshold", 60),
            "max_cache_size": self.get("performance_optimization.max_cache_size", 1000),
            "cleanup_interval": self.get("performance_optimization.cleanup_interval", 300),
            "monitoring_enabled": self.get("performance_optimization.performance_monitoring", True)
        }
    
    def stop_hot_reload(self):
        """Stop hot-reload monitoring"""
        self.hot_reload_enabled = False
        logger.info("Hot-reload monitoring stopped")