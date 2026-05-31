#!/usr/bin/env bash
# macOS 用ビルドスクリプト。プロジェクトルートで実行する。
#   bash build/make_mac.sh
# 前提: .venv 作成済み・依存インストール済み・build/browser に Chromium DL 済み
#   python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
#   PLAYWRIGHT_BROWSERS_PATH="$PWD/build/browser" python -m playwright install chromium
set -euo pipefail
cd "$(dirname "$0")/.."

. .venv/bin/activate

echo "==> PyInstaller ビルド（Chromium除く）"
rm -rf dist build/_pyi_work build/ScrollBot
pyinstaller --noconfirm --distpath dist --workpath build/_pyi_work build/ScrollBot.spec

echo "==> 同梱Chromium を実行ファイル隣へコピー（onedir と .app 両方）"
# onedir 版: dist/ScrollBot/ （Windows同等レイアウト）
cp -R build/browser dist/ScrollBot/browser
# .app 版: Contents/MacOS/ の隣
APP_MACOS="dist/ScrollBot.app/Contents/MacOS"
cp -R build/browser "$APP_MACOS/browser"
cp config.yml "$APP_MACOS/config.yml"

echo "==> 完了"
echo "  onedir : dist/ScrollBot/ScrollBot"
echo "  app    : dist/ScrollBot.app"
echo ""
echo "自己診断(任意・保存済みセッションが必要):"
echo "  dist/ScrollBot/ScrollBot --selftest"
