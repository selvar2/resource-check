# 🔋 Battery Health Guardian

A Windows system tray application that monitors your laptop battery and enforces unplugging at 95% charge to extend battery lifespan.

## ✨ Features

- **Real-time Battery Monitoring** - Continuously tracks battery percentage and charging state
- **Multi-Stage Alert System** - Escalating warnings from gentle notifications to system shutdown
- **System Tray Integration** - Runs quietly in the background with battery status icon
- **Configurable Settings** - Customize thresholds, timing, and behavior
- **Auto-Start** - Optionally starts with Windows
- **Persistence** - Restarts automatically if terminated

## 🚀 Quick Start

### Prerequisites

- Windows 10 or 11
- Python 3.8 or higher

### Installation

1. **Clone or download** this repository

2. **Install dependencies:**
   ```powershell
   cd battery-health-guardian
   python install.py
   ```

3. **Run the application:**
   ```powershell
   # With console (for debugging)
   python run_guardian.py
   
   # Without console (recommended)
   pythonw run_guardian.pyw
   ```

### Building Executable (Optional)

To create a standalone `.exe` file:

```powershell
python build.py
```

The executable will be created at `dist/BatteryHealthGuardian.exe`

## 📋 How It Works

### Alert Stages

| Stage | Trigger | Action |
|-------|---------|--------|
| **Stage 1** | Initial detection at 95% | Toast notification |
| **Stage 2** | Warnings 1-5 | Popup dialog every 30s (can dismiss) |
| **Stage 3** | Warnings 6-10 | Modal dialog (cannot close) |
| **Stage 4** | After 10 warnings OR 5 minutes | System shutdown with 60s countdown |

### Flow

```
[Start App] → [System Tray] → [Monitor Every 30s]
                                    ↓
                         [Battery ≥ 95% + Charging?]
                                    ↓ YES
                         [Start Warning Sequence]
                                    ↓
                         [User Unplugged?] → YES → [Reset & Continue]
                                    ↓ NO
                         [Max Warnings OR Time?]
                                    ↓ YES
                         [Shutdown System]
```

## ⚙️ Configuration

Settings are stored in `%APPDATA%\BatteryHealthGuardian\config.json`:

```json
{
    "battery_threshold": 95,
    "check_interval_seconds": 30,
    "warning_interval_seconds": 30,
    "max_warnings": 10,
    "max_time_minutes": 5,
    "shutdown_countdown_seconds": 60,
    "auto_start_with_windows": true,
    "enable_sounds": true
}
```

Access settings via the system tray menu: **Right-click → Settings**

## 🖥️ System Tray Features

- **Icon** - Shows battery percentage with color coding:
  - 🟢 Green: Normal (20-94%)
  - 🟠 Orange: High (95%+)
  - 🔴 Red: Alert active
  - ⚡ Lightning bolt: Charging

- **Right-click Menu:**
  - 📊 Battery Status - View current stats
  - ⚙️ Settings - Configure the app
  - 🔄 Check Now - Force immediate check
  - ⏸️ Snooze - Pause alerts (5 min)
  - ℹ️ About - App information
  - ❌ Exit - Close the app

- **Double-click** - Show battery statistics

## 🔧 Windows Startup

### Add to Startup

**Option 1: Via Settings**
- Right-click tray icon → Settings → Check "Start with Windows"

**Option 2: Manual**
```powershell
# Using the installer
python install.py
# Select 'y' when asked about Windows startup
```

**Option 3: Registry**
- Press `Win+R`, type `shell:startup`
- Create shortcut to `run_guardian.pyw`

### Remove from Startup

```powershell
python install.py --uninstall
```

Or manually:
1. Press `Win+R`, type `regedit`
2. Navigate to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
3. Delete `BatteryHealthGuardian`

## 📁 Project Structure

```
battery-health-guardian/
├── battery_guardian/
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration management
│   ├── battery_monitor.py  # Battery status monitoring
│   ├── alert_manager.py    # Warning escalation logic
│   ├── dialogs.py          # Warning dialog windows
│   ├── tray_app.py         # System tray application
│   ├── settings_dialog.py  # Settings UI
│   ├── watchdog.py         # Auto-restart service
│   ├── main.py             # Application entry point
│   ├── config.json         # Default configuration
│   └── requirements.txt    # Python dependencies
├── run_guardian.py         # Launcher (with console)
├── run_guardian.pyw        # Launcher (no console)
├── watchdog_service.pyw    # Watchdog background service
├── install.py              # Installation script
├── build.py                # Executable builder
└── README.md               # This file
```

## 🔒 Enforcement Mechanisms

The app uses several mechanisms to ensure battery protection:

1. **Modal Dialogs** - Cannot be closed in later stages
2. **Always-on-Top** - Warning windows stay visible
3. **Auto-Restart** - Watchdog restarts the app if killed
4. **System Shutdown** - Ultimate enforcement after max warnings

## 🐛 Troubleshooting

### App won't start
- Ensure Python 3.8+ is installed
- Run `pip install -r battery_guardian/requirements.txt`
- Check logs at `%APPDATA%\BatteryHealthGuardian\battery_guardian.log`

### No battery detected
- This app requires a laptop with battery
- Desktop computers will show a warning

### Notifications not showing
- Check Windows notification settings
- Ensure `winotify` is installed: `pip install winotify`

### High CPU usage
- Increase `check_interval_seconds` in settings
- Default 30 seconds should use < 1% CPU

## 📝 Logs

Logs are stored at:
```
%APPDATA%\BatteryHealthGuardian\battery_guardian.log
```

## 🤝 Why 95%?

Lithium-ion batteries last longer when not kept at 100% charge. Keeping your battery between 20-80% can significantly extend its lifespan. The 95% threshold provides a buffer while maximizing usable capacity.

**Battery Health Tips:**
- Avoid leaving laptop plugged in at 100%
- Try to keep charge between 20-80%
- Avoid complete discharges
- Store at 40-50% for extended periods

## 📄 License

MIT License - Feel free to use and modify!

## 🙏 Acknowledgments

- [psutil](https://github.com/giampaolo/psutil) - Battery monitoring
- [pystray](https://github.com/moses-palmer/pystray) - System tray
- [Pillow](https://python-pillow.org/) - Icon generation
- [winotify](https://github.com/versa-syahptr/winotify) - Windows notifications
