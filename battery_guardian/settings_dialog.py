"""
Settings dialog for Battery Health Guardian.
Allows users to configure thresholds and behavior.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import winreg
import sys
import os
from pathlib import Path
from typing import Optional

from .config import ConfigManager

logger = logging.getLogger(__name__)

STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "BatteryHealthGuardian"


def get_executable_path() -> str:
    """Get the path to the main executable/script."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as script
        return f'pythonw "{Path(__file__).parent.parent / "run_guardian.pyw"}"'


def is_startup_enabled() -> bool:
    """Check if app is set to start with Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except WindowsError:
            return False
        finally:
            winreg.CloseKey(key)
    except WindowsError:
        return False


def set_startup_enabled(enabled: bool) -> bool:
    """Enable or disable Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            if enabled:
                exe_path = get_executable_path()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                logger.info(f"Added to Windows startup: {exe_path}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Removed from Windows startup")
                except WindowsError:
                    pass  # Key doesn't exist
            return True
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        logger.error(f"Failed to modify startup setting: {e}")
        return False


class SettingsDialog:
    """Settings dialog for configuring Battery Health Guardian."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self._window: Optional[tk.Tk] = None
        self._is_showing = False
        
        # Tkinter variables
        self._threshold_var: Optional[tk.IntVar] = None
        self._check_interval_var: Optional[tk.IntVar] = None
        self._warning_interval_var: Optional[tk.IntVar] = None
        self._max_warnings_var: Optional[tk.IntVar] = None
        self._max_time_var: Optional[tk.IntVar] = None
        self._shutdown_countdown_var: Optional[tk.IntVar] = None
        self._auto_start_var: Optional[tk.BooleanVar] = None
        self._sounds_var: Optional[tk.BooleanVar] = None
    
    def show(self) -> None:
        """Show the settings dialog."""
        if self._is_showing:
            if self._window:
                self._window.lift()
                self._window.focus_force()
            return
        
        self._is_showing = True
        self._create_window()
    
    def _create_window(self) -> None:
        """Create the settings window."""
        self._window = tk.Tk()
        self._window.title("Settings - Battery Health Guardian")
        self._window.configure(bg='#1a1a2e')
        self._window.geometry("500x720")
        self._window.resizable(False, False)
        
        # Center on screen
        self._window.update_idletasks()
        x = (self._window.winfo_screenwidth() - 500) // 2
        y = (self._window.winfo_screenheight() - 720) // 2
        self._window.geometry(f"+{x}+{y}")
        
        self._window.protocol("WM_DELETE_WINDOW", self._close)
        
        # Initialize variables with current config
        self._threshold_var = tk.IntVar(value=self.config.get('battery_threshold', 95))
        self._check_interval_var = tk.IntVar(value=self.config.get('check_interval_seconds', 30))
        self._warning_interval_var = tk.IntVar(value=self.config.get('warning_interval_seconds', 30))
        self._max_warnings_var = tk.IntVar(value=self.config.get('max_warnings', 10))
        self._max_time_var = tk.IntVar(value=self.config.get('max_time_minutes', 5))
        self._shutdown_countdown_var = tk.IntVar(value=self.config.get('shutdown_countdown_seconds', 60))
        self._auto_start_var = tk.BooleanVar(value=is_startup_enabled())
        self._sounds_var = tk.BooleanVar(value=self.config.get('enable_sounds', True))
        
        # Main container with scrolling
        main_frame = tk.Frame(self._window, bg='#1a1a2e', padx=25, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(
            main_frame,
            text="⚙️ Settings",
            font=("Segoe UI", 18, "bold"),
            fg='#e94560',
            bg='#1a1a2e'
        ).pack(pady=(0, 20))
        
        # Battery Threshold Section
        self._create_section(main_frame, "Battery Threshold", [
            ("Alert when charging above:", self._threshold_var, "%", 50, 100),
        ])
        
        # Timing Section
        self._create_section(main_frame, "Timing Settings", [
            ("Check battery every:", self._check_interval_var, "seconds", 5, 300),
            ("Warning interval:", self._warning_interval_var, "seconds", 10, 120),
            ("Maximum warnings:", self._max_warnings_var, "", 1, 50),
            ("Maximum time before shutdown:", self._max_time_var, "minutes", 1, 60),
            ("Shutdown countdown:", self._shutdown_countdown_var, "seconds", 30, 300),
        ])
        
        # Behavior Section
        behavior_frame = tk.Frame(main_frame, bg='#16213e', padx=15, pady=15)
        behavior_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            behavior_frame,
            text="Behavior",
            font=("Segoe UI", 12, "bold"),
            fg='#ffffff',
            bg='#16213e'
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Checkboxes
        tk.Checkbutton(
            behavior_frame,
            text="Start with Windows",
            variable=self._auto_start_var,
            font=("Segoe UI", 10),
            fg='#ffffff',
            bg='#16213e',
            activebackground='#16213e',
            activeforeground='#ffffff',
            selectcolor='#0f3460'
        ).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(
            behavior_frame,
            text="Enable notification sounds",
            variable=self._sounds_var,
            font=("Segoe UI", 10),
            fg='#ffffff',
            bg='#16213e',
            activebackground='#16213e',
            activeforeground='#ffffff',
            selectcolor='#0f3460'
        ).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#1a1a2e')
        button_frame.pack(fill=tk.X, pady=(25, 0))
        
        tk.Button(
            button_frame,
            text="OK",
            font=("Segoe UI", 10, "bold"),
            fg='#ffffff',
            bg='#10b981',
            activebackground='#059669',
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor="hand2",
            command=self._save
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            fg='#ffffff',
            bg='#6b7280',
            activebackground='#4b5563',
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self._close
        ).pack(side=tk.RIGHT)
        
        tk.Button(
            button_frame,
            text="Reset Defaults",
            font=("Segoe UI", 10),
            fg='#ffffff',
            bg='#dc2626',
            activebackground='#b91c1c',
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor="hand2",
            command=self._reset_defaults
        ).pack(side=tk.LEFT)
        
        self._window.mainloop()
    
    def _create_section(self, parent: tk.Frame, title: str, 
                       settings: list[tuple]) -> None:
        """Create a settings section with spinboxes."""
        section_frame = tk.Frame(parent, bg='#16213e', padx=15, pady=15)
        section_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            section_frame,
            text=title,
            font=("Segoe UI", 12, "bold"),
            fg='#ffffff',
            bg='#16213e'
        ).pack(anchor=tk.W, pady=(0, 10))
        
        for label, var, suffix, min_val, max_val in settings:
            row_frame = tk.Frame(section_frame, bg='#16213e')
            row_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                row_frame,
                text=label,
                font=("Segoe UI", 10),
                fg='#94a3b8',
                bg='#16213e'
            ).pack(side=tk.LEFT)
            
            value_frame = tk.Frame(row_frame, bg='#16213e')
            value_frame.pack(side=tk.RIGHT)
            
            spinbox = tk.Spinbox(
                value_frame,
                from_=min_val,
                to=max_val,
                textvariable=var,
                width=6,
                font=("Segoe UI", 10),
                fg='#ffffff',
                bg='#0f3460',
                buttonbackground='#1a1a2e',
                relief=tk.FLAT,
                justify=tk.CENTER
            )
            spinbox.pack(side=tk.LEFT)
            
            if suffix:
                tk.Label(
                    value_frame,
                    text=f" {suffix}",
                    font=("Segoe UI", 10),
                    fg='#94a3b8',
                    bg='#16213e'
                ).pack(side=tk.LEFT)
    
    def _save(self) -> None:
        """Save settings and close dialog. Settings are applied immediately."""
        try:
            # Collect all settings BEFORE any dialog operations
            new_settings = {
                'battery_threshold': self._threshold_var.get(),
                'check_interval_seconds': self._check_interval_var.get(),
                'warning_interval_seconds': self._warning_interval_var.get(),
                'max_warnings': self._max_warnings_var.get(),
                'max_time_minutes': self._max_time_var.get(),
                'shutdown_countdown_seconds': self._shutdown_countdown_var.get(),
                'enable_sounds': self._sounds_var.get(),
            }
            auto_start = self._auto_start_var.get()
            
            # Update config - this saves to file AND notifies listeners
            # The tray app listens for config changes and applies them immediately
            self.config.update(new_settings)
            
            # Update Windows startup registry
            set_startup_enabled(auto_start)
            
            logger.info(f"Settings saved and applied: threshold={new_settings['battery_threshold']}%, "
                       f"check_interval={new_settings['check_interval_seconds']}s")
            
            # Close dialog first (no confirmation dialog - just close)
            self._close()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            # Don't show messagebox - it causes threading issues
            # Just log the error
    
    def _reset_defaults(self) -> None:
        """Reset settings to defaults."""
        from .config import DEFAULT_CONFIG
        
        try:
            if self._threshold_var:
                self._threshold_var.set(DEFAULT_CONFIG['battery_threshold'])
            if self._check_interval_var:
                self._check_interval_var.set(DEFAULT_CONFIG['check_interval_seconds'])
            if self._warning_interval_var:
                self._warning_interval_var.set(DEFAULT_CONFIG['warning_interval_seconds'])
            if self._max_warnings_var:
                self._max_warnings_var.set(DEFAULT_CONFIG['max_warnings'])
            if self._max_time_var:
                self._max_time_var.set(DEFAULT_CONFIG['max_time_minutes'])
            if self._shutdown_countdown_var:
                self._shutdown_countdown_var.set(DEFAULT_CONFIG['shutdown_countdown_seconds'])
            if self._sounds_var:
                self._sounds_var.set(DEFAULT_CONFIG['enable_sounds'])
            
            logger.info("Settings reset to defaults (in dialog)")
        except Exception as e:
            logger.error(f"Error resetting defaults: {e}")
    
    def _close(self) -> None:
        """Close the settings dialog with proper cleanup."""
        if self._window:
            try:
                # Clear all Tkinter variables BEFORE destroying window
                # This prevents "main thread is not in main loop" errors
                self._threshold_var = None
                self._check_interval_var = None
                self._warning_interval_var = None
                self._max_warnings_var = None
                self._max_time_var = None
                self._shutdown_countdown_var = None
                self._auto_start_var = None
                self._sounds_var = None
                
                # Quit mainloop first, then destroy
                self._window.quit()
                self._window.destroy()
            except Exception as e:
                logger.debug(f"Error during dialog cleanup: {e}")
            finally:
                self._window = None
        self._is_showing = False
