#!/usr/bin/env python
"""
Battery Health Guardian Launcher (with console)
Run this file to start the application with visible console for debugging.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from battery_guardian.main import main

if __name__ == "__main__":
    main()
