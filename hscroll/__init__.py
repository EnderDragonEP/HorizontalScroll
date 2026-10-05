"""Horizontal Scroll - hold Mouse Back/Forward and roll the wheel to scroll sideways."""
import os
from pathlib import Path

APP_NAME = "Horizontal Scroll"
APP_ID = "HorizontalScroll"
__version__ = "1.0.2"
__author__ = "Ender Yang"
REPO_URL = "https://github.com/EnderDragonEP/HorizontalScroll"  # "View source" and the update check

DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_ID
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = DATA_DIR / "error.log"
