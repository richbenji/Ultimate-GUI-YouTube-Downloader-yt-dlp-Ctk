# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

if IS_WINDOWS:
    icon_file = "GOD/assets/logos/GOD.ico"
elif IS_MAC:
    icon_file = "GOD/assets/logos/GOD.icns"
else:
    icon_file = "GOD/assets/logos/GOD.png"

a = Analysis(
    ['GOD/main.py'],
    pathex=['GOD'],
    binaries=[],
    datas=[
        ('GOD/assets', 'assets'),
        ('GOD/fonts', 'fonts'),
    ],
    hiddenimports=[
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'customtkinter',
        'yt_dlp',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GOD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if IS_MAC:
    app = BUNDLE(
        exe,
        name='GOD.app',
        icon=icon_file,
        bundle_identifier='com.yourname.god',
    )
