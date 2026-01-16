"""
System tray application for Battery Health Guardian.
Provides status icon, menu, and user interaction.
"""

import threading
import logging
import sys
import os
from typing import Optional, Callable
from pathlib import Path

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Required packages not found. Run: pip install pystray Pillow")
    sys.exit(1)

from .battery_monitor import BatteryMonitor, BatteryStatus, format_time
from .alert_manager import AlertManager, AlertState
from .config import ConfigManager
from .settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class BatteryTrayApp:
    """
    System tray application that displays battery status
    and provides user controls.
    """
    
    def __init__(self):
        self.config = ConfigManager()
        self.battery_monitor = BatteryMonitor(
            check_interval=self.config.get('check_interval_seconds', 30)
        )
        self.alert_manager = AlertManager(self.config, self.battery_monitor)
        
        self._icon: Optional[pystray.Icon] = None
        self._running = False
        self._current_status: Optional[BatteryStatus] = None
        self._settings_dialog: Optional[SettingsDialog] = None
        
        # Set up callbacks
        self.battery_monitor.add_status_callback(self._on_battery_status)
        self.battery_monitor.add_threshold_callback(
            self.config.get('battery_threshold', 95),
            self._on_threshold_reached
        )
        self.alert_manager.set_state_callback(self._on_alert_state_change)
    
    def _create_icon_image(self, percent: int, is_charging: bool = False, 
                           is_alerting: bool = False) -> Image.Image:
        """Create battery icon with current percentage."""
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Battery outline
        margin = 4
        battery_width = size - margin * 2 - 6
        battery_height = size - margin * 2
        
        # Battery body
        outline_color = (255, 255, 255, 255)
        draw.rectangle(
            [margin, margin + 6, margin + battery_width, margin + battery_height],
            outline=outline_color,
            width=2
        )
        
        # Battery cap
        cap_width = 10
        cap_height = 8
        cap_x = margin + battery_width
        cap_y = margin + 6 + (battery_height - 6) // 2 - cap_height // 2
        draw.rectangle(
            [cap_x, cap_y, cap_x + cap_width, cap_y + cap_height],
            fill=outline_color
        )
        
        # Fill based on percentage
        fill_margin = 4
        fill_width = int((battery_width - fill_margin * 2) * (percent / 100))
        fill_height = battery_height - fill_margin * 2 - 6
        
        # Color based on state
        if is_alerting:
            fill_color = (220, 38, 38, 255)  # Red for alert
        elif percent >= 95:
            fill_color = (251, 146, 60, 255)  # Orange for high
        elif percent >= 20:
            fill_color = (34, 197, 94, 255)  # Green for normal
        else:
            fill_color = (239, 68, 68, 255)  # Red for low
        
        if fill_width > 0:
            draw.rectangle(
                [
                    margin + fill_margin,
                    margin + 6 + fill_margin,
                    margin + fill_margin + fill_width,
                    margin + 6 + fill_margin + fill_height
                ],
                fill=fill_color
            )
        
        # Charging indicator (lightning bolt)
        if is_charging:
            bolt_color = (255, 255, 0, 255)  # Yellow
            center_x = size // 2
            center_y = size // 2 + 3
            bolt_size = 8
            
            # Simple lightning bolt shape
            bolt_points = [
                (center_x, center_y - bolt_size),
                (center_x - bolt_size//2, center_y),
                (center_x + 2, center_y - 2),
                (center_x, center_y + bolt_size),
                (center_x + bolt_size//2, center_y),
                (center_x - 2, center_y + 2),
            ]
            draw.polygon(bolt_points, fill=bolt_color)
        
        return img
    
    def _on_battery_status(self, status: BatteryStatus) -> None:
        """Handle battery status update."""
        self._current_status = status
        self._update_icon()
        logger.debug(f"Battery status: {status}")
    
    def _on_threshold_reached(self, status: BatteryStatus) -> None:
        """Handle battery threshold reached while charging."""
        self.alert_manager.handle_battery_status(status)
    
    def _on_alert_state_change(self, state: AlertState) -> None:
        """Handle alert state change."""
        self._update_icon()
    
    def _update_icon(self) -> None:
        """Update the tray icon based on current status."""
        if not self._icon:
            return
        
        status = self._current_status
        if status:
            is_alerting = self.alert_manager.is_alerting
            self._icon.icon = self._create_icon_image(
                percent=status.percent,
                is_charging=status.is_plugged,
                is_alerting=is_alerting
            )
            
            # Update tooltip
            state_str = "⚡ Charging" if status.is_plugged else "🔋 On Battery"
            alert_str = " ⚠️ ALERT" if is_alerting else ""
            self._icon.title = f"Battery: {status.percent}% | {state_str}{alert_str}"
    
    def _create_menu(self) -> pystray.Menu:
        """Create the system tray right-click menu."""
        return pystray.Menu(
            item('📊 Battery Status', self._show_status),
            item('⚙️ Settings', self._show_settings),
            pystray.Menu.SEPARATOR,
            item('🔄 Check Now', self._check_now),
            item('⏸️ Snooze (5 min)', self._snooze),
            pystray.Menu.SEPARATOR,
            item('ℹ️ About', self._show_about),
            item('❌ Exit', self._quit_app)
        )
    
    def _show_status(self, icon=None, item=None) -> None:
        """Show battery status dialog."""
        import tkinter as tk
        from tkinter import ttk
        
        def create_dialog():
            status = self._current_status
            if not status:
                return
            
            root = tk.Tk()
            root.title("Battery Status")
            root.configure(bg='#1a1a2e')
            root.geometry("350x300")
            root.resizable(False, False)
            
            # Center on screen
            root.update_idletasks()
            x = (root.winfo_screenwidth() - 350) // 2
            y = (root.winfo_screenheight() - 300) // 2
            root.geometry(f"+{x}+{y}")
            
            main_frame = tk.Frame(root, bg='#1a1a2e', padx=25, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            tk.Label(
                main_frame,
                text="🔋 Battery Status",
                font=("Segoe UI", 16, "bold"),
                fg='#ffffff',
                bg='#1a1a2e'
            ).pack(pady=(0, 15))
            
            # Stats
            info_frame = tk.Frame(main_frame, bg='#16213e', padx=20, pady=15)
            info_frame.pack(fill=tk.X)
            
            stats = [
                ("Battery Level", f"{status.percent}%"),
                ("Status", "Plugged In" if status.is_plugged else "On Battery"),
                ("State", status.charging_state.value.title()),
                ("Time Remaining", format_time(status.time_remaining)),
                ("Threshold", f"{self.config.get('battery_threshold', 95)}%"),
            ]
            
            for label, value in stats:
                row = tk.Frame(info_frame, bg='#16213e')
                row.pack(fill=tk.X, pady=3)
                tk.Label(row, text=label + ":", font=("Segoe UI", 10),
                        fg='#94a3b8', bg='#16213e').pack(side=tk.LEFT)
                tk.Label(row, text=value, font=("Segoe UI", 10, "bold"),
                        fg='#ffffff', bg='#16213e').pack(side=tk.RIGHT)
            
            # Alert status
            if self.alert_manager.is_alerting:
                state = self.alert_manager.current_state
                alert_frame = tk.Frame(main_frame, bg='#dc2626', padx=15, pady=10)
                alert_frame.pack(fill=tk.X, pady=(15, 0))
                tk.Label(
                    alert_frame,
                    text=f"⚠️ Alert Active: Warning {state.warning_count}/10",
                    font=("Segoe UI", 10, "bold"),
                    fg='#ffffff',
                    bg='#dc2626'
                ).pack()
            
            # Close button
            tk.Button(
                main_frame,
                text="Close",
                font=("Segoe UI", 10),
                fg='#ffffff',
                bg='#0f3460',
                activebackground='#16213e',
                relief=tk.FLAT,
                padx=20,
                pady=8,
                command=root.destroy
            ).pack(pady=(20, 0))
            
            root.mainloop()
        
        thread = threading.Thread(target=create_dialog, daemon=True)
        thread.start()
    
    def _show_settings(self, icon=None, item=None) -> None:
        """Show settings dialog."""
        def create_dialog():
            if self._settings_dialog is None:
                self._settings_dialog = SettingsDialog(self.config)
            self._settings_dialog.show()
        
        thread = threading.Thread(target=create_dialog, daemon=True)
        thread.start()
    
    def _check_now(self, icon=None, item=None) -> None:
        """Force immediate battery check."""
        status = self.battery_monitor.get_battery_status()
        if status:
            self._on_battery_status(status)
            threshold = self.config.get('battery_threshold', 95)
            if status.is_plugged and status.percent >= threshold:
                self._on_threshold_reached(status)
        logger.info("Manual battery check performed")
    
    def _snooze(self, icon=None, item=None) -> None:
        """Snooze alerts for 5 minutes."""
        # TODO: Implement snooze functionality
        logger.info("Snooze activated for 5 minutes")
    
    def _show_about(self, icon=None, item=None) -> None:
        """Show about dialog."""
        import tkinter as tk
        
        def create_dialog():
            root = tk.Tk()
            root.title("About Battery Health Guardian")
            root.configure(bg='#1a1a2e')
            root.geometry("400x280")
            root.resizable(False, False)
            
            root.update_idletasks()
            x = (root.winfo_screenwidth() - 400) // 2
            y = (root.winfo_screenheight() - 280) // 2
            root.geometry(f"+{x}+{y}")
            
            main_frame = tk.Frame(root, bg='#1a1a2e', padx=30, pady=25)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(
                main_frame,
                text="🔋 Battery Health Guardian",
                font=("Segoe UI", 18, "bold"),
                fg='#e94560',
                bg='#1a1a2e'
            ).pack(pady=(0, 10))
            
            tk.Label(
                main_frame,
                text="Version 1.0.0",
                font=("Segoe UI", 10),
                fg='#94a3b8',
                bg='#1a1a2e'
            ).pack()
            
            tk.Label(
                main_frame,
                text="\nProtects your laptop battery by enforcing\nunplugging at optimal charge levels.\n\nKeeping battery between 20-80% extends\nits lifespan significantly.",
                font=("Segoe UI", 10),
                fg='#ffffff',
                bg='#1a1a2e',
                justify=tk.CENTER
            ).pack(pady=15)
            
            tk.Button(
                main_frame,
                text="Close",
                font=("Segoe UI", 10),
                fg='#ffffff',
                bg='#0f3460',
                activebackground='#16213e',
                relief=tk.FLAT,
                padx=20,
                pady=8,
                command=root.destroy
            ).pack(pady=(10, 0))
            
            root.mainloop()
        
        thread = threading.Thread(target=create_dialog, daemon=True)
        thread.start()
    
    def _quit_app(self, icon=None, item=None) -> None:
        """Quit the application."""
        logger.info("Application quit requested")
        self.stop()
    
    def start(self) -> None:
        """Start the tray application."""
        if self._running:
            return
        
        self._running = True
        
        # Get initial battery status
        initial_status = self.battery_monitor.get_battery_status()
        if initial_status:
            self._current_status = initial_status
        
        # Create initial icon
        percent = initial_status.percent if initial_status else 50
        is_charging = initial_status.is_plugged if initial_status else False
        
        icon_image = self._create_icon_image(percent, is_charging)
        
        # Create system tray icon
        self._icon = pystray.Icon(
            name="BatteryHealthGuardian",
            icon=icon_image,
            title=f"Battery: {percent}%",
            menu=self._create_menu()
        )
        
        # Start battery monitor
        self.battery_monitor.start()
        
        # Check threshold on startup
        if initial_status:
            threshold = self.config.get('battery_threshold', 95)
            if initial_status.is_plugged and initial_status.percent >= threshold:
                self._on_threshold_reached(initial_status)
        
        logger.info("Battery Health Guardian started")
        
        # Run the icon (this blocks)
        self._icon.run()
    
    def stop(self) -> None:
        """Stop the tray application."""
        self._running = False
        
        # Stop alert manager
        self.alert_manager.force_stop()
        
        # Stop battery monitor
        self.battery_monitor.stop()
        
        # Stop icon
        if self._icon:
            self._icon.stop()
        
        logger.info("Battery Health Guardian stopped")
