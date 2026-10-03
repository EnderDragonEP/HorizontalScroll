"""Notification-area icon with a Fluent menu."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon
from qfluentwidgets import Action, CheckableSystemTrayMenu, FluentIcon as FIF, MenuIndicatorType, qconfig

from . import APP_NAME, icons
from .config import cfg


class Tray(QSystemTrayIcon):
    settingsRequested = pyqtSignal()
    exitRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._latched = False

        self.enabledAction = self._checkable("Horizontal scrolling", cfg.enabled)
        self.toggleAction = self._checkable("Toggle mode", cfg.toggleMode)
        self.settingsAction = Action(FIF.SETTING, "Settings", triggered=lambda: self.settingsRequested.emit())
        self.exitAction = Action(FIF.CLOSE, "Exit", triggered=lambda: self.exitRequested.emit())

        self.menu = CheckableSystemTrayMenu(indicatorType=MenuIndicatorType.CHECK)
        self.menu.addActions([self.enabledAction, self.toggleAction])
        self.menu.addSeparator()
        self.menu.addActions([self.settingsAction, self.exitAction])
        self.setContextMenu(self.menu)

        self.activated.connect(self._onActivated)
        cfg.enabled.valueChanged.connect(self.refresh)
        self.refresh()

    def setLatched(self, on: bool):
        self._latched = on
        self.refresh()

    def refresh(self, *_):
        if not cfg.enabled.value:
            state, tip = "off", "Off"
        elif self._latched:
            state, tip = "latched", "Horizontal scrolling on"
        else:
            state, tip = "on", "On"
        self.setIcon(icons.tray_icon(state, qconfig.get(qconfig.themeColor)))
        self.setToolTip(f"{APP_NAME} – {tip}")

    def _checkable(self, text, item) -> Action:
        action = Action(text, checkable=True, checked=item.value)
        action.toggled.connect(lambda on: qconfig.set(item, on))
        item.valueChanged.connect(action.setChecked)
        return action

    def _onActivated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.settingsRequested.emit()
