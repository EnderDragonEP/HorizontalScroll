"""Notification-area icon with a Fluent menu: a status header, quick actions and app commands."""
from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QVBoxLayout, QWidget
from qfluentwidgets import (Action, BodyLabel, CaptionLabel, FluentIcon as FIF, StrongBodyLabel, SystemTrayMenu,
                            qconfig, setFont, themeColor)

from . import APP_NAME, icons
from .config import TRIGGER_TEXTS, cfg

_SECONDARY = (QColor(96, 96, 96), QColor(206, 206, 206))  # light, dark


class StatusHeader(QWidget):
    """Three lines at the top of the menu: state, how to use it right now, and the main settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = StrongBodyLabel(self)
        self.detail = BodyLabel(self)
        setFont(self.detail, 16)
        self.caption = CaptionLabel(self)
        self.caption.setTextColor(*_SECONDARY)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 8, 16, 8)  # text lines up with the menu icons
        layout.setSpacing(2)
        for label in (self.title, self.detail, self.caption):
            layout.addWidget(label)

    def setStatus(self, title: str, detail: str, caption: str, active: bool):
        self.title.setText(title)
        self.detail.setText(detail)
        if active:
            self.detail.setTextColor(themeColor(), themeColor())
        else:
            self.detail.setTextColor(*_SECONDARY)
        self.caption.setText(caption)


class Tray(QSystemTrayIcon):
    settingsRequested = pyqtSignal()
    updateCheckRequested = pyqtSignal()
    exitRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._latched = False

        self.header = StatusHeader()
        self.pauseAction = Action(FIF.PAUSE, "Pause horizontal scrolling",
                                  triggered=lambda: qconfig.set(cfg.enabled, not cfg.enabled.value))
        self.modeAction = Action(FIF.PIN, "Switch to toggle mode",
                                 triggered=lambda: qconfig.set(cfg.toggleMode, not cfg.toggleMode.value))
        self.settingsAction = Action(FIF.SETTING, "Settings", triggered=lambda: self.settingsRequested.emit())
        self.updateAction = Action(FIF.UPDATE, "Check for updates",
                                   triggered=lambda: self.updateCheckRequested.emit())
        self.quitAction = Action(FIF.POWER_BUTTON, "Quit", triggered=lambda: self.exitRequested.emit())

        self.menu = SystemTrayMenu()
        self.menu.addWidget(self.header, selectable=False)
        self.menu.addSeparator()
        self.menu.addActions([self.pauseAction, self.modeAction])
        self.menu.addSeparator()
        self.menu.addActions([self.settingsAction, self.updateAction])
        self.menu.addSeparator()
        self.menu.addAction(self.quitAction)
        self.setContextMenu(self.menu)

        self.activated.connect(self._onActivated)
        for item in (cfg.enabled, cfg.toggleMode, cfg.trigger, cfg.speed, cfg.reverse):
            item.valueChanged.connect(self.refresh)
        self.refresh()

    def setLatched(self, on: bool):
        self._latched = on
        self.refresh()

    def refresh(self, *_):
        enabled, toggle = cfg.enabled.value, cfg.toggleMode.value
        trigger = TRIGGER_TEXTS[cfg.trigger.value]
        if not enabled:
            state, tip, title, detail = "off", "Off", "Horizontal scrolling off", "Paused"
        elif self._latched:
            state, tip = "latched", "Locked on"
            title, detail = "Horizontal scrolling locked on", f"Click {trigger} to release"
        elif toggle:
            state, tip, title, detail = "on", "On", "Horizontal scrolling on", f"Click {trigger} to lock"
        else:
            state, tip, title, detail = "on", "On", "Horizontal scrolling on", f"Hold {trigger} + wheel"
        caption = [
            "Toggle mode" if toggle else "Hold mode",
            f"{cfg.speed.value / 10:.1f}× speed",
        ] + (["reversed"] if cfg.reverse.value else [])

        self.setIcon(icons.tray_icon(state))
        self.setToolTip(f"{APP_NAME} – {tip}")
        self.header.setStatus(title, detail, " · ".join(caption), active=enabled)
        self._fitHeader()
        self.pauseAction.setText("Pause horizontal scrolling" if enabled else "Resume horizontal scrolling")
        self.pauseAction.setIcon(FIF.PAUSE if enabled else FIF.PLAY)
        self.modeAction.setText("Switch to hold mode" if toggle else "Switch to toggle mode")
        self.modeAction.setIcon(FIF.UNPIN if toggle else FIF.PIN)

    def _fitHeader(self):
        """The header is the menu's first item; resize that item when the text changes."""
        view = self.menu.view
        # The menu style insets every item by 6 px margin + 10 px padding on each side.
        view.item(0).setSizeHint(self.header.sizeHint() + QSize(32, 0))
        # Separators keep the menu width from when they were added, which would stop
        # the menu from shrinking; give them no width of their own so they follow it.
        for i in range(1, view.count()):
            item = view.item(i)
            if not item.text():
                item.setSizeHint(QSize(0, item.sizeHint().height()))
        view.setMinimumWidth(0)  # adjustSize() never shrinks below the last fixed width
        view.adjustSize()
        self.menu.adjustSize()

    def _onActivated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.settingsRequested.emit()
