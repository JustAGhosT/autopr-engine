#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "scripts", "volume-control"))

from config_loader import VolumeConfigLoader


def main():
    loader = VolumeConfigLoader()
    loader.get_active_tools(200)


if __name__ == "__main__":
    main()
