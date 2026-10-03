# Horizontal Scroll

A small Windows tray app: hold **Mouse Back** or **Mouse Forward** and roll the wheel to scroll sideways.
The settings window follows the Fluent Design System: Mica background, light/dark mode and your accent color.

## How it works

| You do | It does |
| --- | --- |
| Hold Back/Forward and roll the wheel | Scrolls horizontally. Wheel down scrolls right, the same as Shift+wheel. |
| Click Back/Forward without scrolling | Normal Back/Forward. The click is replayed when you release the button. |
| **Toggle mode** on, click Back/Forward | Locks horizontal scrolling on until you click again. A small pill at the bottom of the screen shows On/Off. |
| Use a full-screen app (game, F11, video) | With **Disable in full-screen apps** on (the default), the buttons and wheel work normally. |

More settings: which button triggers it (Back or Forward / Back / Forward), scroll speed (0.5×–3.0×), reverse direction, and start with Windows.
Closing the window keeps the app running in the notification area. Right-click the tray icon to turn it off or exit.

## Run

- **Exe:** download `HorizontalScroll.exe` from the [Releases](../../releases) page, or build it yourself (see below). It's a single file, and Python isn't needed. Start it with `--tray` to start hidden.
- **From source:**

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\python -m pip install -r requirements.txt
  .\.venv\Scripts\pythonw main.py
  ```

Settings are saved to `%APPDATA%\HorizontalScroll\config.json`, and errors are logged to `error.log` in the same folder.

## Build the exe

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

The script creates `.venv`, installs the requirements plus PyInstaller, and writes `dist\HorizontalScroll.exe` (about 24 MB).

## Tests

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## Limitations

- It doesn't work over windows of apps running as administrator unless Horizontal Scroll also runs as administrator. Windows blocks this.
- Apps without horizontal-scroll support won't scroll sideways.
- If mouse software (for example Logitech Options+) remaps Back/Forward to keystrokes, the app never sees the buttons.
- In hold mode, Back/Forward fires on button release, a moment later than usual.
- Single-file PyInstaller exes are sometimes flagged by antivirus heuristics. If that happens, build a one-folder version instead by moving `a.binaries`/`a.datas` into a `COLLECT` step in the spec.

## Layout

```text
main.py              entry point: single instance, wires config, hook and UI
hscroll/engine.py    scroll/toggle/full-screen decisions (pure, unit-tested)
hscroll/hook.py      low-level mouse hook thread + SendInput injector thread
hscroll/winapi.py    ctypes bindings, input injection, full-screen detection
hscroll/config.py    settings (qfluentwidgets QConfig) and the Run-key autostart
hscroll/accent.py    Windows accent shades + watcher for accent changes
hscroll/window.py    Fluent settings window
hscroll/tray.py      tray icon and menu
hscroll/osd.py       toggle-mode on/off pill
hscroll/icons.py     icons drawn in code + .ico writer for the build
```

## License

Copyright (C) 2026 Ender Yang.

Horizontal Scroll is free software, released under the [GNU General Public License v3.0](LICENSE.md).
You may use, change and share it, even sell it, as long as you share your version's source code under the same license.
It comes with no warranty.

It is built with these open-source libraries:

| Library | License |
| --- | --- |
| [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) | GPL-3.0 |
| [PyQt6-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) | GPL-3.0 |
| [PyQt6-Frameless-Window](https://github.com/zhiyiYo/PyQt-Frameless-Window) | GPL-3.0 |
| [darkdetect](https://github.com/albertosottile/darkdetect) | BSD-3-Clause |
| [pywin32](https://github.com/mhammond/pywin32) | PSF |

The exe also contains Python (PSF License) and the Qt libraries that ship with PyQt6 (LGPL-3.0).
