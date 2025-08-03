#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'volume-control'))

from config_loader import VolumeConfigLoader
import json

def main():
    loader = VolumeConfigLoader()
    summary = loader.get_activation_summary(200)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
