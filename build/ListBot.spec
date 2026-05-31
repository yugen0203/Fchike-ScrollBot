# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec（出品Bot / ListBot・onedir 形式・Chromium 同梱）
# 使い方:
#   1) PLAYWRIGHT_BROWSERS_PATH=./build/browser python -m playwright install chromium
#   2) pyinstaller build/ListBot.spec   （プロジェクトルートで実行）
# 生成物: dist/ListBot/ （フォルダごと配布） / dist/出品Bot.app（mac）

import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

# 同梱Chromium(build/browser)は datas に含めない（署名処理で失敗するため）。
# ビルド後に実行ファイル隣へコピーする（make_listbot_mac.sh / CI 参照）。
datas = [
    (str(ROOT / "config_listbot.yml"), "."),   # 既定config（初回に実行ファイル隣へコピー）
]

block_cipher = None

a = Analysis(
    [str(ROOT / "listbot" / "main.py")],
    pathex=[str(ROOT / "listbot"), str(ROOT)],
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
    name="ListBot",
    console=False,            # GUIアプリ（コンソール非表示）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    name="ListBot",
)

# macOS: .app バンドルも生成（表示名は「出品Bot」）
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="出品Bot.app",
        icon=None,
        bundle_identifier="jp.local.listbot",
        info_plist={
            "CFBundleName": "ListBot",
            "CFBundleDisplayName": "出品Bot",
            "NSHighResolutionCapable": True,
        },
    )
