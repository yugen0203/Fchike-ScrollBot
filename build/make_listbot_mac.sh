#!/usr/bin/env bash
# macOS 用ビルドスクリプト（出品Bot / ListBot）。プロジェクトルートで実行する。
#   bash build/make_listbot_mac.sh
# ScrollBot の dist は消さない（ListBot 分だけビルド）。
# 前提: .venv 作成済み・依存インストール済み・build/browser に Chromium DL 済み
set -euo pipefail
cd "$(dirname "$0")/.."

. .venv/bin/activate

echo "==> PyInstaller ビルド（出品Bot・Chromium除く）"
rm -rf "dist/ListBot" "dist/出品Bot.app" build/_pyi_work_listbot
pyinstaller --noconfirm --distpath dist --workpath build/_pyi_work_listbot build/ListBot.spec

echo "==> 同梱Chromium を実行ファイル隣へコピー（onedir と .app 両方）"
cp -R build/browser dist/ListBot/browser
APP_MACOS="dist/出品Bot.app/Contents/MacOS"
cp -R build/browser "$APP_MACOS/browser"
cp config_listbot.yml "$APP_MACOS/config_listbot.yml"

echo "==> 完了"
echo "  onedir : dist/ListBot/ListBot"
echo "  app    : dist/出品Bot.app"
echo ""
echo "診断:    dist/ListBot/ListBot --paths"
echo "グループ確認: dist/ListBot/ListBot --group 5,6,7,8 --mode max_size --max 2"
