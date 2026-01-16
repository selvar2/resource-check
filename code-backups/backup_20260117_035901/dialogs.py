"""
Warning dialogs for Battery Health Guardian.
Implements multi-stage warning system with increasing urgency.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
import subprocess
import sys
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class WarningStage(Enum):
    """Warning escalation stages."""
    TOAST = 1        # Stage 1: Simple notification
    POPUP = 2        # Stage 2: Dismissible popup (warnings 1-5)
    MODAL = 3        # Stage 3: Always-on-top modal (warnings 6-10)
    SHUTDOWN = 4     # Stage 4: Shutdown countdown


class Colors:
    """UI color scheme - modern dark theme with amber accents."""
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#16213e"
    BG_LIGHT = "#0f3460"
    ACCENT = "#e94560"
    ACCENT_WARN = "#ff9f1c"
    ACCENT_DANGER = "#dc2626"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#94a3b8"
    SUCCESS = "#10b981"
    BORDER = "#334155"


class WarningDialog:
    """
    Warning dialog that escalates based on warning count.
    Cannot be closed in final stages - only unplugging cancels it.
    """
    
    def __init__(self):
        self._window: Optional[tk.Tk] = None
        self._shutdown_window: Optional[tk.Tk] = None
        self._is_showing = False
        self._shutdown_countdown = 0
        self._countdown_thread: Optional[threading.Thread] = None
        self._on_shutdown_callback: Optional[Callable] = None
        self._on_cancel_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        
    def show_warning(self, battery_percent: int, warning_count: int, 
                     time_remaining_seconds: int, stage: WarningStage,
                     on_dismiss: Optional[Callable] = None) -> None:
        """Show warning dialog appropriate for the current stage."""
        
        if stage == WarningStage.TOAST:
            self._show_toast(battery_percent)
        elif stage == WarningStage.POPUP:
            self._show_popup(battery_percent, warning_count, time_remaining_seconds, 
                           can_dismiss=True, on_dismiss=on_dismiss)
        elif stage == WarningStage.MODAL:
            self._show_popup(battery_percent, warning_count, time_remaining_seconds,
                           can_dismiss=False, on_dismiss=None)
    
    def _show_toast(self, battery_percent: int) -> None:
        """Show Windows toast notification."""
        try:
            from winotify import Notification, audio
            
            toast = Notification(
                app_id="Battery Health Guardian",
                title="🔋 Battery Health Alert",
                msg=f"Battery at {battery_percent}%. Unplug charger to extend battery lifespan.",
                duration="long"
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            logger.info(f"Toast notification shown for {battery_percent}%")
        except Exception as e:
            logger.error(f"Failed to show toast notification: {e}")
            # Fallback to popup if toast fails
            self._show_popup(battery_percent, 1, 300, can_dismiss=True)
    
    def _show_popup(self, battery_percent: int, warning_count: int,
                    time_remaining_seconds: int, can_dismiss: bool,
                    on_dismiss: Optional[Callable] = None) -> None:
        """Show popup warning dialog in a separate thread."""
        
        def create_window():
            with self._lock:
                if self._is_showing:
                    return
                self._is_showing = True
            
            try:
                self._window = tk.Tk()
                self._window.title("⚠️ BATTERY PROTECTION ALERT")
                self._window.configure(bg=Colors.BG_DARK)
                
                # Window settings
                window_width = 450
                window_height = 380
                
                # Center on screen
                screen_width = self._window.winfo_screenwidth()
                screen_height = self._window.winfo_screenheight()
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                self._window.geometry(f"{window_width}x{window_height}+{x}+{y}")
                
                # Always on top for modal stage
                if not can_dismiss:
                    self._window.attributes('-topmost', True)
                    self._window.overrideredirect(False)
                    self._window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close
                else:
                    self._window.attributes('-topmost', True)
                    self._window.protocol("WM_DELETE_WINDOW", lambda: self._close_warning(on_dismiss))
                
                self._window.resizable(False, False)
                
                # Main container
                main_frame = tk.Frame(self._window, bg=Colors.BG_DARK, padx=25, pady=20)
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Header
                header_frame = tk.Frame(main_frame, bg=Colors.BG_MEDIUM, pady=12)
                header_frame.pack(fill=tk.X, pady=(0, 15))
                
                stage_text = "MODAL WARNING" if not can_dismiss else "WARNING"
                header_color = Colors.ACCENT_DANGER if not can_dismiss else Colors.ACCENT_WARN
                
                tk.Label(
                    header_frame,
                    text=f"⚠️  BATTERY PROTECTION ALERT",
                    font=("Segoe UI", 14, "bold"),
                    fg=header_color,
                    bg=Colors.BG_MEDIUM
                ).pack()
                
                # Battery level with progress bar
                level_frame = tk.Frame(main_frame, bg=Colors.BG_DARK)
                level_frame.pack(fill=tk.X, pady=10)
                
                tk.Label(
                    level_frame,
                    text=f"Battery Level: {battery_percent}%",
                    font=("Segoe UI", 12),
                    fg=Colors.TEXT_PRIMARY,
                    bg=Colors.BG_DARK
                ).pack(anchor=tk.W)
                
                # Custom progress bar
                progress_frame = tk.Frame(level_frame, bg=Colors.BORDER, height=24)
                progress_frame.pack(fill=tk.X, pady=8)
                progress_frame.pack_propagate(False)
                
                progress_width = int((battery_percent / 100) * (window_width - 60))
                progress_color = Colors.ACCENT_DANGER if battery_percent >= 95 else Colors.SUCCESS
                
                progress_bar = tk.Frame(progress_frame, bg=progress_color, width=progress_width)
                progress_bar.pack(side=tk.LEFT, fill=tk.Y)
                
                tk.Label(
                    progress_frame,
                    text=f" {battery_percent}%",
                    font=("Segoe UI", 10, "bold"),
                    fg=Colors.TEXT_PRIMARY,
                    bg=progress_color if battery_percent > 10 else Colors.BORDER
                ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                
                # Status
                tk.Label(
                    main_frame,
                    text="Status: CHARGING (Unplug Required)",
                    font=("Segoe UI", 11, "bold"),
                    fg=Colors.ACCENT,
                    bg=Colors.BG_DARK
                ).pack(pady=5)
                
                # Warning counter and time
                info_frame = tk.Frame(main_frame, bg=Colors.BG_LIGHT, padx=15, pady=12)
                info_frame.pack(fill=tk.X, pady=10)
                
                tk.Label(
                    info_frame,
                    text=f"Warning: {warning_count} of 10",
                    font=("Segoe UI", 11),
                    fg=Colors.TEXT_PRIMARY,
                    bg=Colors.BG_LIGHT
                ).pack(anchor=tk.W)
                
                minutes = time_remaining_seconds // 60
                seconds = time_remaining_seconds % 60
                tk.Label(
                    info_frame,
                    text=f"Time until shutdown: {minutes}:{seconds:02d}",
                    font=("Segoe UI", 11),
                    fg=Colors.ACCENT_WARN,
                    bg=Colors.BG_LIGHT
                ).pack(anchor=tk.W, pady=(5, 0))
                
                # Message
                msg_frame = tk.Frame(main_frame, bg=Colors.BG_DARK)
                msg_frame.pack(fill=tk.X, pady=15)
                
                tk.Label(
                    msg_frame,
                    text="Continuous charging above 95% degrades\nbattery health. Please unplug now.",
                    font=("Segoe UI", 10),
                    fg=Colors.TEXT_SECONDARY,
                    bg=Colors.BG_DARK,
                    justify=tk.CENTER
                ).pack()
                
                # Action instruction
                action_frame = tk.Frame(main_frame, bg=Colors.BG_MEDIUM, pady=10)
                action_frame.pack(fill=tk.X, pady=(10, 0))
                
                action_text = "Unplug charger to dismiss this alert" if can_dismiss else "UNPLUG CHARGER NOW - Cannot dismiss"
                action_color = Colors.SUCCESS if can_dismiss else Colors.ACCENT_DANGER
                
                tk.Label(
                    action_frame,
                    text=f"[ {action_text} ]",
                    font=("Segoe UI", 10, "bold"),
                    fg=action_color,
                    bg=Colors.BG_MEDIUM
                ).pack()
                
                # Dismiss button (only for early stages)
                if can_dismiss:
                    dismiss_btn = tk.Button(
                        main_frame,
                        text="Dismiss (I'll unplug soon)",
                        font=("Segoe UI", 10),
                        fg=Colors.TEXT_PRIMARY,
                        bg=Colors.BG_LIGHT,
                        activebackground=Colors.BG_MEDIUM,
                        activeforeground=Colors.TEXT_PRIMARY,
                        relief=tk.FLAT,
                        cursor="hand2",
                        padx=20,
                        pady=8,
                        command=lambda: self._close_warning(on_dismiss)
                    )
                    dismiss_btn.pack(pady=(15, 0))
                
                self._window.mainloop()
                
            except Exception as e:
                logger.error(f"Error showing popup: {e}")
            finally:
                with self._lock:
                    self._is_showing = False
                    self._window = None
        
        thread = threading.Thread(target=create_window, daemon=True)
        thread.start()
    
    def _close_warning(self, callback: Optional[Callable] = None) -> None:
        """Close the warning dialog."""
        with self._lock:
            if self._window:
                try:
                    self._window.quit()
                    self._window.destroy()
                except:
                    pass
                self._window = None
            self._is_showing = False
        
        if callback:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in dismiss callback: {e}")
    
    def close_all(self) -> None:
        """Close all open dialogs."""
        self._close_warning()
        self.cancel_shutdown()
    
    def show_shutdown_warning(self, countdown_seconds: int,
                              on_shutdown: Callable,
                              on_cancel: Callable) -> None:
        """Show final shutdown countdown dialog."""
        self._shutdown_countdown = countdown_seconds
        self._on_shutdown_callback = on_shutdown
        self._on_cancel_callback = on_cancel
        
        def create_shutdown_window():
            try:
                self._shutdown_window = tk.Tk()
                self._shutdown_window.title("🛑 SYSTEM SHUTDOWN IMMINENT")
                self._shutdown_window.configure(bg=Colors.BG_DARK)
                
                # Window settings - larger and more prominent
                window_width = 500
                window_height = 300
                
                screen_width = self._shutdown_window.winfo_screenwidth()
                screen_height = self._shutdown_window.winfo_screenheight()
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                self._shutdown_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
                
                # Always on top, cannot close
                self._shutdown_window.attributes('-topmost', True)
                self._shutdown_window.overrideredirect(False)
                self._shutdown_window.protocol("WM_DELETE_WINDOW", lambda: None)
                self._shutdown_window.resizable(False, False)
                
                # Try to focus and bring to front
                self._shutdown_window.focus_force()
                self._shutdown_window.lift()
                
                # Main container
                main_frame = tk.Frame(self._shutdown_window, bg=Colors.BG_DARK, padx=30, pady=25)
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Danger header
                header_frame = tk.Frame(main_frame, bg=Colors.ACCENT_DANGER, pady=15)
                header_frame.pack(fill=tk.X, pady=(0, 20))
                
                tk.Label(
                    header_frame,
                    text="🛑  SYSTEM SHUTDOWN IMMINENT",
                    font=("Segoe UI", 16, "bold"),
                    fg=Colors.TEXT_PRIMARY,
                    bg=Colors.ACCENT_DANGER
                ).pack()
                
                # Countdown display
                self._countdown_label = tk.Label(
                    main_frame,
                    text=f"System will shutdown in: {countdown_seconds:02d}",
                    font=("Segoe UI", 24, "bold"),
                    fg=Colors.ACCENT_WARN,
                    bg=Colors.BG_DARK
                )
                self._countdown_label.pack(pady=20)
                
                # Instructions
                tk.Label(
                    main_frame,
                    text="UNPLUG CHARGER NOW TO CANCEL",
                    font=("Segoe UI", 14, "bold"),
                    fg=Colors.SUCCESS,
                    bg=Colors.BG_DARK
                ).pack(pady=10)
                
                tk.Label(
                    main_frame,
                    text="This protects your battery health.",
                    font=("Segoe UI", 11),
                    fg=Colors.TEXT_SECONDARY,
                    bg=Colors.BG_DARK
                ).pack(pady=5)
                
                # Start countdown
                self._countdown_thread = threading.Thread(
                    target=self._countdown_loop,
                    daemon=True
                )
                self._countdown_thread.start()
                
                self._shutdown_window.mainloop()
                
            except Exception as e:
                logger.error(f"Error showing shutdown window: {e}")
        
        thread = threading.Thread(target=create_shutdown_window, daemon=True)
        thread.start()
    
    def _countdown_loop(self) -> None:
        """Countdown timer for shutdown."""
        while self._shutdown_countdown > 0 and self._shutdown_window:
            time.sleep(1)
            self._shutdown_countdown -= 1
            
            try:
                if self._shutdown_window and self._countdown_label:
                    self._countdown_label.configure(
                        text=f"System will shutdown in: {self._shutdown_countdown:02d}"
                    )
            except:
                pass
        
        # Time's up - trigger shutdown
        if self._shutdown_countdown <= 0 and self._on_shutdown_callback:
            try:
                self._on_shutdown_callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback: {e}")
    
    def cancel_shutdown(self) -> None:
        """Cancel the shutdown countdown and close dialog."""
        self._shutdown_countdown = -1  # Stop countdown
        
        if self._shutdown_window:
            try:
                self._shutdown_window.quit()
                self._shutdown_window.destroy()
            except:
                pass
            self._shutdown_window = None
        
        if self._on_cancel_callback:
            try:
                self._on_cancel_callback()
            except Exception as e:
                logger.error(f"Error in cancel callback: {e}")
    
    @property
    def is_showing(self) -> bool:
        """Check if any dialog is currently showing."""
        return self._is_showing or self._shutdown_window is not None


def trigger_system_shutdown(countdown: int = 60, message: str = "Battery protection shutdown") -> bool:
    """Trigger Windows system shutdown."""
    try:
        # Windows shutdown command
        cmd = f'shutdown /s /t {countdown} /c "{message}"'
        subprocess.run(cmd, shell=True, check=True)
        logger.warning(f"System shutdown initiated with {countdown}s countdown")
        return True
    except Exception as e:
        logger.error(f"Failed to initiate shutdown: {e}")
        return False


def cancel_system_shutdown() -> bool:
    """Cancel a pending Windows system shutdown."""
    try:
        subprocess.run('shutdown /a', shell=True, check=True)
        logger.info("System shutdown cancelled")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel shutdown: {e}")
        return False
