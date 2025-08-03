#!/usr/bin/env python3

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'volume-control'))

from config_loader import VolumeConfigLoader

def main():
    loader = VolumeConfigLoader()
    volume_settings = loader.get_settings_for_volume(200)
    print('Settings applied at volume 200:')
    print(json.dumps(volume_settings, indent=2))

if __name__ == "__main__":
    main()
