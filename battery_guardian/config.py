"""
Configuration management for Battery Health Guardian.
Handles loading, saving, and validating application settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "battery_threshold": 95,
    "check_interval_seconds": 30,
    "warning_interval_seconds": 30,
    "max_warnings": 10,
    "max_time_minutes": 5,
    "shutdown_countdown_seconds": 60,
    "auto_start_with_windows": True,
    "enable_sounds": True,
    "low_battery_alert": False,
    "low_battery_threshold": 20
}


def get_app_data_dir() -> Path:
    """Get the application data directory for storing config."""
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    config_dir = Path(app_data) / 'BatteryHealthGuardian'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return get_app_data_dir() / 'config.json'


def load_config() -> Dict[str, Any]:
    """Load configuration from file, creating default if not exists."""
    config_path = get_config_path()
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config: {e}. Using defaults.")
            return DEFAULT_CONFIG.copy()
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError as e:
        logger.error(f"Error saving config: {e}")
        return False


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize configuration values."""
    validated = config.copy()
    
    # Ensure threshold is within valid range
    validated['battery_threshold'] = max(50, min(100, config.get('battery_threshold', 95)))
    
    # Ensure intervals are positive
    validated['check_interval_seconds'] = max(5, config.get('check_interval_seconds', 30))
    validated['warning_interval_seconds'] = max(10, config.get('warning_interval_seconds', 30))
    
    # Ensure warnings count is reasonable
    validated['max_warnings'] = max(1, min(50, config.get('max_warnings', 10)))
    
    # Ensure time limits are reasonable
    validated['max_time_minutes'] = max(1, min(60, config.get('max_time_minutes', 5)))
    validated['shutdown_countdown_seconds'] = max(30, min(300, config.get('shutdown_countdown_seconds', 60)))
    
    return validated


class ConfigManager:
    """Singleton configuration manager."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = validate_config(load_config())
        return cls._instance
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
        self._config = validate_config(self._config)
        save_config(self._config)
    
    def update(self, updates: Dict[str, Any]) -> None:
        self._config.update(updates)
        self._config = validate_config(self._config)
        save_config(self._config)
    
    def reload(self) -> None:
        self._config = validate_config(load_config())
