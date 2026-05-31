# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec（onedir 形式・Chromium 同梱）
# 使い方:
#   1) PLAYWRIGHT_BROWSERS_PATH=./build/browser python -m playwright install chromium
#   2) pyinstaller build/ScrollBot.spec   （プロジェクトルートで実行）
# 生成物: dist/ScrollBot/ （フォルダごと配布）

import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

# 注意: 同梱Chromium(build/browser)は datas に含めない。
# PyInstaller が Chromium.app 内の Mach-O を署名処理しようとして失敗するため、
# ビルド後に実行ファイル隣へコピーする（build/make_mac.sh / make_win.bat 参照）。
datas = [
    (str(ROOT / "config.yml"), "."),       # 既定config（初回に実行ファイル隣へコピーされる）
]

block_cipher = None

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT / "app"), str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["playwright", "playwright.sync_api"],
    hookspath=[str(ROOT / "build" / "hooks")],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ScrollBot",
    console=False,            # GUIアプリ（コンソール非表示）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    name="ScrollBot",
)

# macOS: .app バンドルも生成
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="ScrollBot.app",
        icon=None,
        bundle_identifier="jp.local.scrollbot",
        info_plist={
            "CFBundleName": "ScrollBot",
            "NSHighResolutionCapable": True,
        },
    )
