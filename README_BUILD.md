# ScrollBot 開発・ビルド手順（開発者向け）

## 1. 環境準備（初回のみ）
```bash
# Python 3.12 推奨（無ければ 3.13 でも可。Tk が必要）
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# macOS で Tk が無い場合（Homebrew Python）
#   brew install python-tk@3.13

# 同梱用 Chromium をプロジェクト内へDL
PLAYWRIGHT_BROWSERS_PATH="$PWD/build/browser" python -m playwright install chromium
```

## 2. 開発実行（パッケージ化せず動作確認）
```bash
source .venv/bin/activate
PLAYWRIGHT_BROWSERS_PATH="$PWD/build/browser" python -m app.main
```
- GUI が起動。`設定` で ID/パスワードを保存（`.env` 生成）→ `実行`。
- GUIなしの自己診断: `python -m app.main --selftest`（保存済みセッションでスクロールのみ確認）

## 3. ビルド

### macOS
```bash
bash build/make_mac.sh
# 生成物:
#   dist/ScrollBot/        ← onedir（Windows同等レイアウト）
#   dist/ScrollBot.app     ← Mac アプリ
```
`make_mac.sh` は PyInstaller 実行後に `build/browser` を実行ファイル隣へコピーする
（PyInstaller が Chromium 内部バイナリの署名処理で失敗するため、同梱は datas ではなく後コピー）。

### Windows
```bat
:: Windows 実機で（PyInstaller はクロスビルド不可）
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
set PLAYWRIGHT_BROWSERS_PATH=%CD%\build\browser
python -m playwright install chromium
pyinstaller --noconfirm --distpath dist --workpath build\_pyi_work build\ScrollBot.spec
:: 生成後、build\browser を dist\ScrollBot\browser へコピー
xcopy /E /I build\browser dist\ScrollBot\browser
```
配布は `dist\ScrollBot\` フォルダごと（中に ScrollBot.exe / config.yml / browser/）。

## 4. パッケージ版の動作確認
```bash
# onedir（クリーン環境シミュレート）
env -i HOME="$HOME" PATH="/usr/bin:/bin" ./dist/ScrollBot/ScrollBot --selftest
# .app
"./dist/ScrollBot.app/Contents/MacOS/ScrollBot" --selftest
```
`SELFTEST: OK` が出れば、Python非導入PCでも同梱Chromiumで動作する。

## 5. 配布時の注意
- **macOS 未署名**: 初回は Gatekeeper でブロックされる。利用者は
  「右クリック → 開く」 もしくは `xattr -dr com.apple.quarantine ScrollBot.app` で許可。
  正式配布には Developer ID 署名＋公証（notarization）が必要（Phase 1.2 以降）。
- 配布フォルダには `config.yml` を実行ファイル隣に同梱（初回起動時に自動生成もされる）。
- `profiles/` `logs/` `.env` は初回利用時に実行ファイル隣へ自動生成される。

## 6. 開発専用ファイル（配布に含めない）
- `build/_devtest_scroll.py` … セッション再利用＋スクロールの単体検証
- `build/browser/` … 同梱用 Chromium（巨大・約450MB）
- `dist/` `build/_pyi_work/` … ビルド生成物
