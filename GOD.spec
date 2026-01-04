# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    icon_file = os.path.join("GOD", "assets", "logos", "GOD.ico")
elif IS_MAC:
    icon_file = os.path.join("GOD", "assets", "logos", "GOD.icns")
else:
    icon_file = os.path.join("GOD", "assets", "logos", "GOD.png")

datas = (
    collect_data_files("PIL")
    + [
        ("GOD/assets", "assets"),
        ("GOD/fonts", "fonts"),
    ]
)

a = Analysis(
    ["GOD/main.py"],
    pathex=["GOD"],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PIL.Image",
        "PIL.ImageTk",
        "PIL._tkinter_finder",
        "tkinter",
        "tkinter.filedialog",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    #optimize=0,
    #noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    a.pure,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GOD",
    console=False,
    icon=icon_file,
)

# Pour macOS uniquement
if IS_MAC:
    app = BUNDLE(
        exe,
        name='GOD.app',
        icon=icon_file,
        bundle_identifier='com.yourname.god',
    )
