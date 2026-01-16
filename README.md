# 🔋 Battery Health Guardian

A Windows system tray application that monitors your laptop battery and enforces unplugging at 95% charge to extend battery lifespan.

---

## 🚀 Quick Start (Zero Installation Required!)

### Option 1: One-Click Run (Recommended)
```bash
# Clone the repository
git clone https://github.com/user/battery-health-guardian.git
cd battery-health-guardian

# Run immediately - no pip install needed!
run.bat
```

### Option 2: Pre-built Executable
Download `BatteryHealthGuardian.exe` from [Releases](releases/) and run directly.

### Option 3: PowerShell
```powershell
.\run.ps1
```

**That's it!** No pip install, no Python setup, no configuration needed.

---

## 📦 What's Included

| Component | Status | Description |
|-----------|--------|-------------|
| ✅ Vendored Dependencies | Bundled | All packages in `vendor/` folder |
| ✅ Launcher Scripts | Included | `run.bat`, `run.ps1` |
| ✅ Pre-built Executable | Available | `releases/BatteryHealthGuardian.exe` |
| ⚡ Embedded Python | Optional | Run `download-python.bat` to add |

---

## ✨ Features

- **Real-time Battery Monitoring** - Continuously tracks battery percentage and charging state
- **Multi-Stage Alert System** - Escalating warnings from gentle notifications to system shutdown
- **System Tray Integration** - Runs quietly in the background with battery status icon
- **Configurable Settings** - Customize thresholds, timing, and behavior
- **Auto-Start** - Optionally starts with Windows
- **Persistence** - Restarts automatically if terminated

---

## ⚠️ Alert Stages

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

---

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

---

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

---

## 📁 Repository Structure

```
battery-health-guardian/
├── .github/
│   └── workflows/
│       └── build.yml           # CI/CD pipeline
├── battery_guardian/           # Source code
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── battery_monitor.py      # Battery monitoring
│   ├── alert_manager.py        # Alert system
│   ├── dialogs.py              # Warning dialogs
│   ├── tray_app.py             # System tray
│   ├── settings_dialog.py      # Settings UI
│   ├── watchdog.py             # Auto-restart
│   ├── config.py               # Configuration
│   ├── config.json             # Default config
│   └── requirements.txt        # Dependencies list
├── vendor/                     # 📦 Pre-installed dependencies
│   ├── psutil/
│   ├── pystray/
│   ├── PIL/
│   └── winotify/
├── releases/                   # Pre-built executables
│   └── BatteryHealthGuardian.exe
├── python-embedded/            # (Optional) Portable Python
├── run.bat                     # ⭐ One-click launcher
├── run.ps1                     # PowerShell launcher
├── run-debug.bat               # Debug launcher (with console)
├── setup.bat                   # Verify installation
├── build.bat                   # Build executable
├── install-dev.bat             # Rebuild vendor folder
├── download-python.bat         # Download embedded Python
├── .gitattributes
├── .gitignore
└── README.md
```

---

## 🔧 For Developers

### Running from Source (with vendored deps)
```bash
# Dependencies are already in vendor/ - just run:
run.bat

# Or with debug output:
run-debug.bat
```

### Rebuilding Vendor Dependencies
```bash
# Only if you need to update packages:
install-dev.bat
```

### Building Standalone Executable
```bash
build.bat
# Output: releases/BatteryHealthGuardian.exe
```

### Adding Embedded Python (Optional)
```bash
# Downloads portable Python - makes truly zero-dependency:
download-python.bat
```

---

## 🚀 Windows Startup

### Add to Startup

**Option 1: Via Settings**
- Right-click tray icon → Settings → Check "Start with Windows"

**Option 2: Manual**
1. Press `Win+R`, type `shell:startup`
2. Create shortcut to `run.bat`

### Remove from Startup
- Right-click tray icon → Settings → Uncheck "Start with Windows"

---

## 🐛 Troubleshooting

### App won't start
1. Run `setup.bat` to verify installation
2. Try `run-debug.bat` to see error messages
3. Check logs at `%APPDATA%\BatteryHealthGuardian\battery_guardian.log`

### No battery detected
- This app requires a laptop with battery
- Desktop computers will show a warning

### Notifications not showing
- Check Windows notification settings
- Focus Assist may be blocking notifications

---

## 📝 Logs

Logs are stored at:
```
%APPDATA%\BatteryHealthGuardian\battery_guardian.log
```

---

## 🤝 Why 95%?

Lithium-ion batteries last longer when not kept at 100% charge. Keeping your battery between 20-80% can significantly extend its lifespan. The 95% threshold provides a buffer while maximizing usable capacity.

**Battery Health Tips:**
- Avoid leaving laptop plugged in at 100%
- Try to keep charge between 20-80%
- Avoid complete discharges
- Store at 40-50% for extended periods

---

## 📄 License

MIT License - Feel free to use and modify!

---

## 🙏 Acknowledgments

- [psutil](https://github.com/giampaolo/psutil) - Battery monitoring
- [pystray](https://github.com/moses-palmer/pystray) - System tray
- [Pillow](https://python-pillow.org/) - Icon generation
- [winotify](https://github.com/versa-syahptr/winotify) - Windows notifications
