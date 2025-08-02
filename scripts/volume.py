#!/usr/bin/env python3
"""
Volume Control Wrapper for AutoPR Engine

Simple wrapper to use the HiFi-style volume control system.
"""

import sys
import os
from pathlib import Path

# Add the volume-control directory to the path
volume_control_path = Path(__file__).parent / "volume-control"
sys.path.insert(0, str(volume_control_path))

# Import and run the main volume control
from main import main

if __name__ == "__main__":
    main() 