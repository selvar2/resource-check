"""
Alert management system for Battery Health Guardian.
Orchestrates the multi-stage warning escalation process.
"""

import threading
import time
import logging
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .battery_monitor import BatteryStatus, BatteryMonitor
from .dialogs import WarningDialog, WarningStage, trigger_system_shutdown, cancel_system_shutdown
from .config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class AlertState:
    """Current state of the alert system."""
    warning_count: int = 0
    elapsed_seconds: int = 0
    is_active: bool = False
    current_stage: WarningStage = WarningStage.TOAST
    shutdown_initiated: bool = False


class AlertManager:
    """
    Manages the warning escalation process.
    
    Stages:
    1. Toast notification (first detection)
    2. Popup dialogs every 30s (warnings 1-5)
    3. Modal dialogs (warnings 6-10) - cannot be closed
    4. System shutdown after 10 warnings OR 5 minutes
    """
    
    def __init__(self, config: ConfigManager, battery_monitor: BatteryMonitor):
        self.config = config
        self.battery_monitor = battery_monitor
        self.dialog = WarningDialog()
        self.state = AlertState()
        
        self._alert_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        
        # Callbacks for UI updates
        self._on_state_change: Optional[Callable[[AlertState], None]] = None
        
    def set_state_callback(self, callback: Callable[[AlertState], None]) -> None:
        """Set callback for alert state changes."""
        self._on_state_change = callback
    
    def handle_battery_status(self, status: BatteryStatus) -> None:
        """Handle battery status update from monitor."""
        threshold = self.config.get('battery_threshold', 95)
        
        # Check if we need to start/stop alert sequence
        if status.is_plugged and status.percent >= threshold:
            if not self.state.is_active:
                self._start_alert_sequence(status)
        else:
            if self.state.is_active:
                self._stop_alert_sequence(status)
    
    def _start_alert_sequence(self, status: BatteryStatus) -> None:
        """Start the alert escalation sequence."""
        with self._lock:
            if self.state.is_active:
                return
            
            self.state = AlertState(
                warning_count=0,
                elapsed_seconds=0,
                is_active=True,
                current_stage=WarningStage.TOAST,
                shutdown_initiated=False
            )
            self._running = True
        
        logger.info(f"Starting alert sequence - Battery at {status.percent}%")
        
        # Show initial toast notification
        self.dialog.show_warning(
            battery_percent=status.percent,
            warning_count=1,
            time_remaining_seconds=self.config.get('max_time_minutes', 5) * 60,
            stage=WarningStage.TOAST
        )
        
        # Start the escalation thread
        self._alert_thread = threading.Thread(target=self._escalation_loop, daemon=True)
        self._alert_thread.start()
        
        self._notify_state_change()
    
    def _stop_alert_sequence(self, status: Optional[BatteryStatus] = None) -> None:
        """Stop the alert sequence (charger unplugged or battery below threshold)."""
        with self._lock:
            if not self.state.is_active:
                return
            
            was_shutdown = self.state.shutdown_initiated
            self._running = False
            self.state = AlertState()
        
        # Close all dialogs
        self.dialog.close_all()
        
        # Cancel any pending shutdown
        if was_shutdown:
            cancel_system_shutdown()
            logger.info("Shutdown cancelled - charger unplugged")
        
        reason = "charger unplugged" if status and not status.is_plugged else "battery below threshold"
        logger.info(f"Alert sequence stopped - {reason}")
        
        self._notify_state_change()
    
    def _escalation_loop(self) -> None:
        """Main loop for warning escalation."""
        warning_interval = self.config.get('warning_interval_seconds', 30)
        max_warnings = self.config.get('max_warnings', 10)
        max_time = self.config.get('max_time_minutes', 5) * 60
        shutdown_countdown = self.config.get('shutdown_countdown_seconds', 60)
        
        last_warning_time = time.time()
        start_time = time.time()
        
        while self._running:
            time.sleep(1)
            
            # Update elapsed time
            with self._lock:
                self.state.elapsed_seconds = int(time.time() - start_time)
            
            # Check if charger was unplugged
            current_status = self.battery_monitor.last_status
            if current_status and not current_status.is_plugged:
                self._stop_alert_sequence(current_status)
                return
            
            # Check for shutdown conditions
            should_shutdown = (
                self.state.warning_count >= max_warnings or 
                self.state.elapsed_seconds >= max_time
            )
            
            if should_shutdown and not self.state.shutdown_initiated:
                self._initiate_shutdown(shutdown_countdown)
                return
            
            # Check if it's time for next warning
            time_since_last = time.time() - last_warning_time
            if time_since_last >= warning_interval:
                last_warning_time = time.time()
                self._show_next_warning(current_status)
            
            self._notify_state_change()
    
    def _show_next_warning(self, status: Optional[BatteryStatus]) -> None:
        """Show the next warning in the sequence."""
        with self._lock:
            self.state.warning_count += 1
            count = self.state.warning_count
            
            # Determine stage based on warning count
            if count <= 1:
                self.state.current_stage = WarningStage.TOAST
            elif count <= 5:
                self.state.current_stage = WarningStage.POPUP
            else:
                self.state.current_stage = WarningStage.MODAL
        
        battery_percent = status.percent if status else 95
        max_time = self.config.get('max_time_minutes', 5) * 60
        time_remaining = max(0, max_time - self.state.elapsed_seconds)
        
        logger.info(f"Showing warning {count} (Stage: {self.state.current_stage.name})")
        
        # Close any existing dialog first
        self.dialog.close_all()
        time.sleep(0.3)  # Brief pause for dialog cleanup
        
        self.dialog.show_warning(
            battery_percent=battery_percent,
            warning_count=count,
            time_remaining_seconds=time_remaining,
            stage=self.state.current_stage,
            on_dismiss=lambda: logger.debug(f"Warning {count} dismissed")
        )
    
    def _initiate_shutdown(self, countdown: int) -> None:
        """Initiate system shutdown sequence."""
        with self._lock:
            self.state.shutdown_initiated = True
            self.state.current_stage = WarningStage.SHUTDOWN
        
        logger.warning(f"Initiating shutdown sequence with {countdown}s countdown")
        
        # Close any existing warning dialogs
        self.dialog.close_all()
        time.sleep(0.3)
        
        # Show shutdown warning dialog
        self.dialog.show_shutdown_warning(
            countdown_seconds=countdown,
            on_shutdown=self._execute_shutdown,
            on_cancel=lambda: logger.info("Shutdown dialog closed")
        )
        
        # Also trigger actual Windows shutdown (with same countdown)
        trigger_system_shutdown(countdown, "Battery protection - please unplug charger")
        
        self._notify_state_change()
        
        # Monitor for charger unplugging during countdown
        self._monitor_during_shutdown(countdown)
    
    def _monitor_during_shutdown(self, countdown: int) -> None:
        """Monitor for charger being unplugged during shutdown countdown."""
        start_time = time.time()
        
        while time.time() - start_time < countdown and self._running:
            time.sleep(0.5)
            
            status = self.battery_monitor.last_status
            if status and not status.is_plugged:
                # Charger unplugged - cancel everything!
                self._stop_alert_sequence(status)
                return
    
    def _execute_shutdown(self) -> None:
        """Execute the actual system shutdown."""
        logger.critical("Executing system shutdown due to battery protection")
        # The shutdown was already triggered via Windows command
        # This callback is just for logging/cleanup
    
    def _notify_state_change(self) -> None:
        """Notify listener of state change."""
        if self._on_state_change:
            try:
                self._on_state_change(self.state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    def force_stop(self) -> None:
        """Force stop all alerts (for app shutdown)."""
        self._running = False
        self.dialog.close_all()
        cancel_system_shutdown()
        self.state = AlertState()
    
    @property
    def is_alerting(self) -> bool:
        """Check if alert sequence is active."""
        return self.state.is_active
    
    @property
    def current_state(self) -> AlertState:
        """Get current alert state."""
        return self.state
