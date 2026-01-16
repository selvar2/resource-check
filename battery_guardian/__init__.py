"""
Battery Health Guardian - Laptop battery protection application.

This application monitors your laptop battery and enforces unplugging
at 95% charge to extend battery lifespan.
"""

__version__ = "1.0.0"
__author__ = "Battery Health Guardian"

from .config import ConfigManager
from .battery_monitor import BatteryMonitor, BatteryStatus
from .alert_manager import AlertManager
from .tray_app import BatteryTrayApp

__all__ = [
    'ConfigManager',
    'BatteryMonitor', 
    'BatteryStatus',
    'AlertManager',
    'BatteryTrayApp',
]
