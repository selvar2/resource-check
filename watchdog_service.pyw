#!/usr/bin/env python
"""
Watchdog service for Battery Health Guardian.
Monitors the main application and restarts it if killed.
"""

import sys
import time
import subprocess
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
MAIN_SCRIPT = SCRIPT_DIR / "run_guardian.pyw"
CHECK_INTERVAL = 15  # seconds


def is_main_app_running() -> bool:
    """Check if the main application is running."""
    try:
        import psutil
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(str(arg) for arg in cmdline if arg)
                    if 'run_guardian' in cmdline_str.lower() or 'battery_guardian' in cmdline_str.lower():
                        # Make sure it's not this watchdog
                        if 'watchdog' not in cmdline_str.lower():
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception as e:
        logger.error(f"Error checking process: {e}")
        return False


def start_main_app() -> bool:
    """Start the main application."""
    try:
        if not MAIN_SCRIPT.exists():
            logger.error(f"Main script not found: {MAIN_SCRIPT}")
            return False
        
        # Use pythonw for windowless execution
        python_exe = "pythonw" if sys.platform == "win32" else "python"
        
        subprocess.Popen(
            [python_exe, str(MAIN_SCRIPT)],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0,
            close_fds=True
        )
        
        logger.info("Main application started")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start main application: {e}")
        return False


def main():
    """Watchdog main loop."""
    logger.info("Watchdog service started")
    
    # Initial delay to let main app start first
    time.sleep(5)
    
    while True:
        try:
            if not is_main_app_running():
                logger.warning("Main application not running, starting...")
                start_main_app()
                time.sleep(10)  # Give it time to start
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Watchdog interrupted")
            break
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
            time.sleep(CHECK_INTERVAL)
    
    logger.info("Watchdog service stopped")


if __name__ == "__main__":
    main()
