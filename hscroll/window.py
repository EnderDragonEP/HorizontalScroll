"""Settings window, built with PyQt6-Fluent-Widgets (Fluent Design, Mica on Windows 11)."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QGuiApplication
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (BodyLabel, ComboBoxSettingCard, ExpandLayout, FluentIcon as FIF, FluentWidget, InfoBar,
                            InfoBarPosition, RangeSettingCard, ScrollArea, SettingCardGroup, SwitchSettingCard,
                            TitleLabel, setFont)

from . import APP_NAME, config, icons
from .config import cfg

TRIGGER_TEXTS = {"either": "Back or Forward", "back": "Back", "forward": "Forward"}


class Group(SettingCardGroup):
    """Setting card group with a Windows 11 Settings style header (14 px semibold)."""

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        setFont(self.titleLabel, 14, QFont.Weight.DemiBold)
        self.titleLabel.adjustSize()

    def adjustSize(self):
        h = self.cardLayout.heightForWidth(self.width()) + self.titleLabel.height() + 12
        return self.resize(self.width(), h)


class SpeedCard(RangeSettingCard):
    """Slider card that shows the speed as a multiplier (stored in tenths)."""

    def __init__(self, parent=None):
        super().__init__(cfg.speed, FIF.SPEED_HIGH, "Scroll speed", "Distance per wheel step", parent)
        self.slider.setMinimumWidth(180)
        self._show(cfg.speed.value)

    def setValue(self, value):
        super().setValue(value)
        self._show(value)

    def _show(self, value):
        self.valueLabel.setText(f"{value / 10:.1f}×")
        self.valueLabel.adjustSize()


class SettingsPage(ScrollArea):
    """Fixed page header (title + hint) above scrolling setting cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget()
        self.expand = ExpandLayout(self.view)
        self.title = TitleLabel(APP_NAME, self)
        self.hint = BodyLabel(self)
        self.hint.setWordWrap(True)
        self.hint.setTextColor(QColor(96, 96, 96), QColor(206, 206, 206))

        self.enableCard = SwitchSettingCard(
            icons.glyph_icon(), "Horizontal scrolling", "Turn the whole feature on or off", cfg.enabled, self.view)

        self.activation = Group("Activation", self.view)
        self.triggerCard = ComboBoxSettingCard(
            cfg.trigger, FIF.RETURN, "Trigger button", "The mouse button that turns the wheel sideways",
            texts=list(TRIGGER_TEXTS.values()), parent=self.activation)
        self.toggleCard = SwitchSettingCard(
            FIF.PIN, "Toggle mode", "Click the trigger to turn horizontal scrolling on, click again to turn it off",
            cfg.toggleMode, self.activation)
        self.activation.addSettingCards([self.triggerCard, self.toggleCard])

        self.scrolling = Group("Scrolling", self.view)
        self.speedCard = SpeedCard(self.scrolling)
        self.reverseCard = SwitchSettingCard(
            FIF.SYNC, "Reverse direction", "Wheel down scrolls left instead of right", cfg.reverse, self.scrolling)
        self.scrolling.addSettingCards([self.speedCard, self.reverseCard])

        self.general = Group("General", self.view)
        self.fullscreenCard = SwitchSettingCard(
            FIF.FULL_SCREEN, "Disable in full-screen apps",
            "Games and full-screen videos keep the normal Back and Forward buttons",
            cfg.disableInFullscreen, self.general)
        self.startupCard = SwitchSettingCard(
            FIF.POWER_BUTTON, "Start with Windows", "Start in the notification area when you sign in",
            parent=self.general)
        self.general.addSettingCards([self.fullscreenCard, self.startupCard])

        self.expand.setSpacing(28)
        self.expand.setContentsMargins(36, 0, 36, 36)
        for widget in (self.enableCard, self.activation, self.scrolling, self.general):
            self.expand.addWidget(widget)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

    def setHint(self, text: str):
        self.hint.setText(text)
        self._layoutHeader()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._layoutHeader()

    def _layoutHeader(self):
        width = max(self.width() - 72, 100)
        self.title.move(36, 12)
        self.hint.resize(width, self.hint.heightForWidth(width))
        self.hint.move(36, self.title.geometry().bottom() + 6)
        self.setViewportMargins(0, self.hint.geometry().bottom() + 24, 0, 0)


class SettingsWindow(FluentWidget):
    hiddenToTray = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(icons.app_icon())
        self.page = SettingsPage(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        layout.addWidget(self.page)
        self.titleBar.raise_()

        self.setMinimumWidth(520)
        self._placed = False

        self.page.startupCard.setChecked(config.is_autostart())
        self.page.startupCard.checkedChanged.connect(self._setAutostart)
        cfg.trigger.valueChanged.connect(self._updateHint)
        cfg.toggleMode.valueChanged.connect(self._updateHint)
        self._updateHint()

    def present(self):
        if not self._placed:
            # Size on first show: the frameless base class's own initial resize
            # can arrive late and override a size set while the window is hidden.
            self._placed = True
            area = QGuiApplication.primaryScreen().availableGeometry()
            self.resize(640, min(880, area.height() - 48))
            self.move(area.center() - self.rect().center())
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self.hiddenToTray.emit()

    def _updateHint(self, *_):
        trigger = TRIGGER_TEXTS[cfg.trigger.value]
        if cfg.toggleMode.value:
            text = f"Click {trigger} to turn horizontal scrolling on or off. You can also hold it while rolling the wheel."
        else:
            text = f"Hold {trigger} and roll the wheel to scroll sideways. A quick click still works as usual."
        self.page.setHint(text)

    def _setAutostart(self, on: bool):
        try:
            config.set_autostart(on)
        except OSError as e:
            card = self.page.startupCard
            card.switchButton.blockSignals(True)
            card.setChecked(not on)
            card.switchButton.blockSignals(False)
            InfoBar.error("Couldn't change the startup setting", str(e), orient=Qt.Orientation.Horizontal,
                          isClosable=True, position=InfoBarPosition.TOP, duration=5000, parent=self)
