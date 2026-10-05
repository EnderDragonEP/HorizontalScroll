"""Settings (auto-saved JSON via qfluentwidgets' QConfig) and the "Start with Windows" entry."""
import shlex
import sys
import winreg
from pathlib import Path

from qfluentwidgets import (BoolValidator, ConfigItem, OptionsConfigItem, OptionsValidator, QConfig,
                            RangeConfigItem, RangeValidator, qconfig)

from . import APP_ID, CONFIG_FILE
from .engine import BACK, FORWARD, Settings

TRIGGERS = {
    "either": frozenset({BACK, FORWARD}),
    "back": frozenset({BACK}),
    "forward": frozenset({FORWARD}),
}
TRIGGER_TEXTS = {"either": "Back or Forward", "back": "Back", "forward": "Forward"}


class Config(QConfig):
    enabled = ConfigItem("General", "Enabled", True, BoolValidator())
    trigger = OptionsConfigItem("General", "Trigger", "either", OptionsValidator(list(TRIGGERS)))
    toggleMode = ConfigItem("General", "ToggleMode", False, BoolValidator())
    disableInFullscreen = ConfigItem("General", "DisableInFullscreen", True, BoolValidator())
    reverse = ConfigItem("Scrolling", "Reverse", False, BoolValidator())
    speed = RangeConfigItem("Scrolling", "Speed", 10, RangeValidator(5, 30))  # tenths: 10 = 1.0x
    trayHintShown = ConfigItem("General", "TrayHintShown", False, BoolValidator())


cfg = Config()


def load():
    qconfig.load(CONFIG_FILE, cfg)


def to_settings() -> Settings:
    return Settings(
        buttons=TRIGGERS[cfg.trigger.value],
        toggle_mode=cfg.toggleMode.value,
        skip_fullscreen=cfg.disableInFullscreen.value,
        reverse=cfg.reverse.value,
        speed=cfg.speed.value / 10,
    )


# -- Start with Windows (HKCU Run key, no admin rights needed) ---------------

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --tray'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    main = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{pythonw}" "{main}" --tray'


def _run_value():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            return winreg.QueryValueEx(key, APP_ID)[0]
    except OSError:
        return None


def is_autostart() -> bool:
    return _run_value() is not None


def set_autostart(on: bool):
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if on:
            winreg.SetValueEx(key, APP_ID, 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(key, APP_ID)
            except FileNotFoundError:
                pass


def refresh_autostart():
    """Re-point the entry at this copy if the program it names no longer exists."""
    value = _run_value()
    if not value:
        return
    try:
        target = shlex.split(value, posix=False)[0].strip('"')
    except ValueError:
        target = ""
    if not Path(target).exists():
        try:
            set_autostart(True)
        except OSError:
            pass
