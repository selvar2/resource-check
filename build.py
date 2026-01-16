#!/usr/bin/env python
"""
Build script for Battery Health Guardian.
Creates standalone executable using PyInstaller.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def build_executable():
    """Build the standalone executable."""
    print("=" * 50)
    print("Building Battery Health Guardian Executable")
    print("=" * 50)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check if icon exists
    icon_path = Path('battery_guardian/icon.ico')
    icon_setting = f"icon='{icon_path}'," if icon_path.exists() else "icon=None,"
    
    # Create spec file content
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_guardian.pyw'],
    pathex=[],
    binaries=[],
    datas=[
        ('battery_guardian/config.json', 'battery_guardian'),
    ],
    hiddenimports=[
        'pystray._win32',
        'PIL._tkinter_finder',
        'winotify',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BatteryHealthGuardian',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_setting}
)
'''
    
    # Write spec file
    spec_path = Path("BatteryHealthGuardian.spec")
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print("Building executable...")
    
    # Run PyInstaller
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        str(spec_path)
    ], capture_output=False)
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("Build successful!")
        print()
        print("Executable location: dist/BatteryHealthGuardian.exe")
        print("=" * 50)
    else:
        print()
        print("Build failed!")
        sys.exit(1)
    
    # Clean up
    spec_path.unlink(missing_ok=True)


def clean():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.spec']
    
    for d in dirs_to_remove:
        path = Path(d)
        if path.exists():
            shutil.rmtree(path)
            print(f"Removed: {d}")
    
    for pattern in files_to_remove:
        for f in Path('.').glob(pattern):
            f.unlink()
            print(f"Removed: {f}")
    
    # Clean pycache in subdirectories
    for pycache in Path('.').rglob('__pycache__'):
        shutil.rmtree(pycache)
        print(f"Removed: {pycache}")
    
    print("Clean complete!")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    else:
        build_executable()
