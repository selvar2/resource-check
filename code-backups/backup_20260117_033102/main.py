"""
Main entry point for Battery Health Guardian.
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from battery_guardian.tray_app import BatteryTrayApp
from battery_guardian.watchdog import setup_persistence
from battery_guardian.config import get_app_data_dir


def setup_logging() -> None:
    """Configure logging for the application."""
    log_dir = get_app_data_dir()
    log_file = log_dir / 'battery_guardian.log'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler (only if running with console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    # Only add console handler if we have a console
    if sys.stdout is not None:
        root_logger.addHandler(console_handler)


def check_single_instance() -> bool:
    """
    Check if another instance is already running.
    Uses a mutex on Windows.
    """
    if sys.platform != 'win32':
        return True
    
    try:
        import ctypes
        mutex_name = "BatteryHealthGuardian_SingleInstance"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        
        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            logging.warning("Another instance is already running")
            return False
        return True
    except Exception as e:
        logging.error(f"Error checking single instance: {e}")
        return True  # Allow running if check fails


def main() -> None:
    """Main entry point."""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("Battery Health Guardian starting...")
    logger.info("=" * 50)
    
    # Check single instance
    if not check_single_instance():
        logger.info("Exiting - another instance is running")
        sys.exit(0)
    
    # Setup persistence mechanisms
    try:
        setup_persistence()
    except Exception as e:
        logger.warning(f"Persistence setup failed: {e}")
    
    # Create and start the tray application
    try:
        app = BatteryTrayApp()
        app.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Battery Health Guardian stopped")


if __name__ == "__main__":
    main()
