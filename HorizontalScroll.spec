# PyInstaller spec: one small windowed HorizontalScroll.exe.  Build with .\build.ps1
from pathlib import PurePath

EXCLUDES = [
    # large packages that might be installed but are never used
    "numpy", "PIL", "scipy", "colorthief", "tkinter",
    # optional parts of the UI libraries
    "qfluentwidgets.multimedia", "qframelesswindow.webengine",
    "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets", "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtQuick", "PyQt6.QtQml", "PyQt6.QtPdf", "PyQt6.QtOpenGL", "PyQt6.QtOpenGLWidgets",
    # pywin32's MFC UI and COM code generator (pulled in via win32com, never used)
    "win32ui", "pywin", "win32com.client.makepy",
    # OpenSSL: no network use; hashlib falls back to its built-in hashes
    "ssl", "_ssl", "_hashlib",
]

# Qt files a widgets-only English app never loads.
DROP_FILES = {"opengl32sw.dll", "d3dcompiler_47.dll", "qt6pdf.dll"}
DROP_PLUGIN_DIRS = {"tls", "networkinformation"}
DROP_IMAGE_PLUGINS = {"qgif", "qjpeg", "qtiff", "qwebp", "qicns", "qtga", "qwbmp", "qpdf"}


def keep(entry):
    dest = PurePath(entry[0])
    if dest.name.lower() in DROP_FILES or "translations" in dest.parts:
        return False
    if dest.parent.name in DROP_PLUGIN_DIRS:
        return False
    return not (dest.parent.name == "imageformats" and dest.stem.lower() in DROP_IMAGE_PLUGINS)


a = Analysis(["main.py"], excludes=EXCLUDES)
a.binaries = [b for b in a.binaries if keep(b)]
a.datas = [d for d in a.datas if keep(d)]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HorizontalScroll",
    console=False,
    icon="build/app.ico",
    upx=False,
)
