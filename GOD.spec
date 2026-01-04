# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin")
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
        # Ajout pour yt-dlp
        "yt_dlp",
        "yt_dlp.extractor",
        "customtkinter",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,  # 👈 CORRECTION ICI : utilise pyz au lieu de a.pure
    a.scripts,
    a.binaries,
    a.zipfiles,  # 👈 AJOUT
    a.datas,
    [],
    name="GOD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False pour GUI, True pour debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
