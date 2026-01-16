#!/usr/bin/env python
"""
Installation script for Battery Health Guardian.
Sets up dependencies and configures Windows startup.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    
    requirements_file = Path(__file__).parent / "battery_guardian" / "requirements.txt"
    
    if requirements_file.exists():
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
    else:
        # Install individually
        packages = ["psutil", "pystray", "Pillow", "winotify"]
        for package in packages:
            print(f"Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
    
    print("Dependencies installed successfully!")


def add_to_startup():
    """Add application to Windows startup."""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        
        script_path = Path(__file__).parent / "run_guardian.pyw"
        value = f'pythonw "{script_path}"'
        
        winreg.SetValueEx(key, "BatteryHealthGuardian", 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        
        print(f"Added to Windows startup: {value}")
        return True
        
    except Exception as e:
        print(f"Failed to add to startup: {e}")
        return False


def remove_from_startup():
    """Remove application from Windows startup."""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        
        try:
            winreg.DeleteValue(key, "BatteryHealthGuardian")
            print("Removed from Windows startup")
        except WindowsError:
            print("Not in Windows startup")
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        print(f"Failed to remove from startup: {e}")
        return False


def create_shortcut():
    """Create desktop shortcut."""
    try:
        import winreg
        
        # Get desktop path
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
        
        # Create .bat file as simple shortcut
        shortcut_path = Path(desktop_path) / "Battery Health Guardian.bat"
        script_path = Path(__file__).parent / "run_guardian.pyw"
        
        with open(shortcut_path, 'w') as f:
            f.write(f'@echo off\nstart "" pythonw "{script_path}"\n')
        
        print(f"Desktop shortcut created: {shortcut_path}")
        return True
        
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
        return False


def main():
    """Main installation function."""
    print("=" * 50)
    print("Battery Health Guardian - Installation")
    print("=" * 50)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required!")
        sys.exit(1)
    
    print(f"Python version: {sys.version}")
    print()
    
    # Install dependencies
    try:
        install_dependencies()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)
    
    print()
    
    # Ask about startup
    response = input("Add to Windows startup? (y/n): ").strip().lower()
    if response == 'y':
        add_to_startup()
    
    print()
    
    # Ask about desktop shortcut
    response = input("Create desktop shortcut? (y/n): ").strip().lower()
    if response == 'y':
        create_shortcut()
    
    print()
    print("=" * 50)
    print("Installation complete!")
    print()
    print("To start the application:")
    print("  - Run: python run_guardian.py")
    print("  - Or double-click run_guardian.pyw (no console)")
    print()
    print("To uninstall:")
    print("  - Run: python install.py --uninstall")
    print("=" * 50)


def uninstall():
    """Uninstall the application."""
    print("=" * 50)
    print("Battery Health Guardian - Uninstallation")
    print("=" * 50)
    print()
    
    remove_from_startup()
    
    # Remove scheduled task
    try:
        subprocess.run(
            'schtasks /delete /tn "BatteryHealthGuardian" /f',
            shell=True, capture_output=True
        )
        print("Removed scheduled task")
    except:
        pass
    
    # Remove config directory
    try:
        import shutil
        config_dir = Path(os.environ.get('APPDATA', '')) / 'BatteryHealthGuardian'
        if config_dir.exists():
            response = input(f"Remove config directory ({config_dir})? (y/n): ").strip().lower()
            if response == 'y':
                shutil.rmtree(config_dir)
                print("Config directory removed")
    except Exception as e:
        print(f"Failed to remove config: {e}")
    
    print()
    print("Uninstallation complete!")


if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        main()
