"""
Battery monitoring service for Battery Health Guardian.
Continuously monitors battery percentage and charging state.
"""

import psutil
import threading
import time
import logging
from typing import Callable, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ChargingState(Enum):
    CHARGING = "charging"
    DISCHARGING = "discharging"
    FULL = "full"
    NOT_CHARGING = "not_charging"
    UNKNOWN = "unknown"


@dataclass
class BatteryStatus:
    """Current battery status information."""
    percent: int
    is_plugged: bool
    charging_state: ChargingState
    time_remaining: Optional[int]  # seconds until empty/full, None if unknown
    
    @property
    def needs_unplug(self) -> bool:
        """Check if battery needs to be unplugged (above threshold and charging)."""
        return self.is_plugged and self.charging_state in (ChargingState.CHARGING, ChargingState.FULL)
    
    def __str__(self) -> str:
        state_str = "Plugged In" if self.is_plugged else "On Battery"
        return f"Battery: {self.percent}% | {state_str} | {self.charging_state.value}"


class BatteryMonitor:
    """
    Monitors battery status and triggers callbacks when conditions are met.
    """
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable[[BatteryStatus], None]] = []
        self._threshold_callbacks: list[tuple[int, Callable[[BatteryStatus], None]]] = []
        self._last_status: Optional[BatteryStatus] = None
        self._lock = threading.Lock()
    
    def get_battery_status(self) -> Optional[BatteryStatus]:
        """Get current battery status."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                logger.warning("No battery detected - this might be a desktop computer")
                return None
            
            # Determine charging state
            if battery.power_plugged:
                if battery.percent >= 100:
                    state = ChargingState.FULL
                else:
                    state = ChargingState.CHARGING
            else:
                state = ChargingState.DISCHARGING
            
            return BatteryStatus(
                percent=int(battery.percent),
                is_plugged=battery.power_plugged,
                charging_state=state,
                time_remaining=battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            )
        except Exception as e:
            logger.error(f"Error reading battery status: {e}")
            return None
    
    def add_status_callback(self, callback: Callable[[BatteryStatus], None]) -> None:
        """Add a callback to be called on every status check."""
        with self._lock:
            self._callbacks.append(callback)
    
    def add_threshold_callback(self, threshold: int, callback: Callable[[BatteryStatus], None]) -> None:
        """Add a callback to be called when battery exceeds threshold while charging."""
        with self._lock:
            self._threshold_callbacks.append((threshold, callback))
    
    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
            self._threshold_callbacks = [(t, c) for t, c in self._threshold_callbacks if c != callback]
    
    def start(self) -> None:
        """Start the battery monitoring thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Battery monitor started (checking every {self.check_interval}s)")
    
    def stop(self) -> None:
        """Stop the battery monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Battery monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                status = self.get_battery_status()
                if status:
                    self._last_status = status
                    self._notify_callbacks(status)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.check_interval * 2):
                if not self._running:
                    break
                time.sleep(0.5)
    
    def _notify_callbacks(self, status: BatteryStatus) -> None:
        """Notify all registered callbacks."""
        with self._lock:
            # Regular status callbacks
            for callback in self._callbacks:
                try:
                    callback(status)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
            
            # Threshold callbacks (only when charging and above threshold)
            if status.is_plugged:
                for threshold, callback in self._threshold_callbacks:
                    if status.percent >= threshold:
                        try:
                            callback(status)
                        except Exception as e:
                            logger.error(f"Error in threshold callback: {e}")
    
    @property
    def last_status(self) -> Optional[BatteryStatus]:
        """Get the last known battery status."""
        return self._last_status
    
    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running


def format_time(seconds: Optional[int]) -> str:
    """Format seconds into human-readable time."""
    if seconds is None or seconds < 0:
        return "Unknown"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
