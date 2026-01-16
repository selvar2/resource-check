"""
Watchdog service for Battery Health Guardian.
Ensures the application restarts if killed and provides persistence mechanisms.
"""

import subprocess
import sys
import os
import time
import logging
import threading
import ctypes
from pathlib import Path
from typing import Optional
import winreg

logger = logging.getLogger(__name__)

# Windows constants
SW_HIDE = 0
SW_SHOW = 5

STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "BatteryHealthGuardian"
WATCHDOG_NAME = "BatteryGuardianWatchdog"


def get_script_path() -> Path:
    """Get the path to the main script."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable)
    return Path(__file__).parent.parent / "run_guardian.pyw"


def get_watchdog_script_path() -> Path:
    """Get the path to the watchdog script."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable)
    return Path(__file__).parent.parent / "watchdog_service.pyw"


def is_process_running(process_name: str) -> bool:
    """Check if a process with the given name is running."""
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                # Check process name
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    return True
                # Check command line for script name
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    for arg in cmdline:
                        if arg and process_name.lower() in arg.lower():
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception as e:
        logger.error(f"Error checking for process: {e}")
        return False


def get_process_count(search_term: str) -> int:
    """Count processes matching the search term."""
    count = 0
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(str(arg) for arg in cmdline if arg)
                    if search_term.lower() in cmdline_str.lower():
                        count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.error(f"Error counting processes: {e}")
    return count


def hide_from_task_manager() -> bool:
    """
    Attempt to make the process harder to kill.
    Note: This has limited effectiveness without admin rights.
    """
    try:
        # Set process priority to high
        import psutil
        p = psutil.Process()
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        logger.debug("Process priority set to HIGH")
        return True
    except Exception as e:
        logger.debug(f"Could not modify process priority: {e}")
        return False


def create_scheduled_task() -> bool:
    """
    Create a Windows scheduled task for persistence.
    This provides another layer of auto-restart capability.
    """
    try:
        script_path = get_script_path()
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>pythonw</Command>
      <Arguments>"{script_path}"</Arguments>
    </Exec>
  </Actions>
</Task>'''
        
        # Save XML to temp file
        temp_dir = Path(os.environ.get('TEMP', '.'))
        xml_path = temp_dir / 'battery_guardian_task.xml'
        with open(xml_path, 'w', encoding='utf-16') as f:
            f.write(task_xml)
        
        # Create task using schtasks
        cmd = f'schtasks /create /tn "{APP_NAME}" /xml "{xml_path}" /f'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Clean up
        xml_path.unlink(missing_ok=True)
        
        if result.returncode == 0:
            logger.info("Scheduled task created successfully")
            return True
        else:
            logger.warning(f"Failed to create scheduled task: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating scheduled task: {e}")
        return False


def remove_scheduled_task() -> bool:
    """Remove the Windows scheduled task."""
    try:
        cmd = f'schtasks /delete /tn "{APP_NAME}" /f'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error removing scheduled task: {e}")
        return False


class WatchdogService:
    """
    Watchdog that monitors the main application and restarts it if killed.
    """
    
    def __init__(self, target_script: str, check_interval: int = 10):
        self.target_script = target_script
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._main_process: Optional[subprocess.Popen] = None
    
    def start(self) -> None:
        """Start the watchdog service."""
        if self._running:
            return
        
        self._running = True
        
        # Start the main application
        self._start_main_app()
        
        # Start monitoring thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        logger.info("Watchdog service started")
    
    def stop(self) -> None:
        """Stop the watchdog service."""
        self._running = False
        
        if self._main_process:
            try:
                self._main_process.terminate()
            except:
                pass
        
        logger.info("Watchdog service stopped")
    
    def _start_main_app(self) -> None:
        """Start or restart the main application."""
        try:
            # Use pythonw for windowless execution
            python_exe = "pythonw" if sys.platform == "win32" else "python"
            
            self._main_process = subprocess.Popen(
                [python_exe, self.target_script],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            logger.info(f"Main application started (PID: {self._main_process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to start main application: {e}")
    
    def _monitor_loop(self) -> None:
        """Monitor the main application and restart if needed."""
        while self._running:
            time.sleep(self.check_interval)
            
            if self._main_process:
                # Check if process is still running
                if self._main_process.poll() is not None:
                    logger.warning("Main application terminated, restarting...")
                    self._start_main_app()


def start_watchdog_background() -> bool:
    """Start the watchdog as a background process."""
    try:
        watchdog_script = get_watchdog_script_path()
        
        if not watchdog_script.exists():
            logger.warning(f"Watchdog script not found: {watchdog_script}")
            return False
        
        # Check if watchdog is already running
        if get_process_count('watchdog_service') > 0:
            logger.info("Watchdog is already running")
            return True
        
        python_exe = "pythonw" if sys.platform == "win32" else "python"
        
        subprocess.Popen(
            [python_exe, str(watchdog_script)],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0,
            close_fds=True
        )
        
        logger.info("Watchdog started in background")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start watchdog: {e}")
        return False


def setup_persistence() -> None:
    """Set up all persistence mechanisms."""
    # Try to hide from task manager (limited without admin)
    hide_from_task_manager()
    
    # Registry startup is handled in settings_dialog.py
    
    # Scheduled task provides additional persistence
    # Only attempt if we have appropriate permissions
    try:
        create_scheduled_task()
    except Exception as e:
        logger.debug(f"Scheduled task creation skipped: {e}")
