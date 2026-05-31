# Fチケ自動スクロール プロジェクト

北海道日本ハムファイターズ「Fチケ（ticket.fighters.co.jp）」マイシーズンシートを、
最新試合（最下部の出品ボタン位置）まで自動でスクロールするための仕組み。

開発は2フェーズ：

- **Phase 1** … ブラウザのコンソールに貼るだけのスニペット（手動運用）
- **Phase 1.1** … 一般事務スタッフがダブルクリックで使えるデスクトップアプリ「ScrollBot」

---

## Phase 1：コンソール用スニペット（手動）

詳細は `task.md` と `snippets/` を参照。

| ファイル | 役割 |
|----------|------|
| `snippets/01_myseat-fetch-all.{md,txt}` | API一括取得（全48試合データを約15秒で取得・データのみ） |
| `snippets/02_myseat-autoscroll.{md,txt}` | 画面を最下部(9/24)まで自動スクロール（約17秒） |
| `マイシーズンシート_スクロール再現.mp4` | スクロール動作の再現動画 |

**使い方**：Fチケのマイシーズンシートを開き（ログイン済み）、Chrome の検証ツール →
Console に `snippets/02_…txt` の中身を貼り付けて Enter。
（貼り付けがブロックされたら一度 `allow pasting` と入力 → 再度貼り付け）

**判明した仕組み**：遅延読み込みは `pack/myseat?offset=N&limit=10` のページングAPI。
認証は localStorage の Cognito idToken（`Authorization: Bearer`）。

---

## Phase 1.1：ScrollBot（デスクトップアプリ）

### 何ができる
ログイン → マイシーズンシートへ遷移 → **最下部まで自動スクロールして停止**
（最新試合の「出品」ボタンが見える状態）。Python/Chrome/ターミナル不要。

### 利用者向け（配布後）
1. 配布フォルダ内の **ScrollBot.app（Mac） / ScrollBot.exe（Win）** をダブルクリック
   - ※Mac初回は「右クリック →  開く」（未署名のため）
2. 初回のみ `設定` で **ログインID（お客様コード）／パスワード** を入力して保存
3. **開くタブ数（1〜20）** を選ぶ／必要なら「**タブを同時並行でスクロール**」をオン（既定オン）
4. `実行` を押す → ブラウザが開き、自動でログイン → 指定タブ数ぶん最下部までスクロール
   - ログインは最初の1回のみ（同一ブラウザ＝セッション共有）
   - **並行オン**: 全タブを開いて同時にスクロール（速い）／**オフ**: 1タブずつ順次
5. **処理後もブラウザは開いたまま**（最新試合の出品ボタンを確認・操作できる）。
   ブラウザは**独立プロセス**なので、**このScrollBotアプリを閉じてもブラウザは残る**。
   不要になったらブラウザのウィンドウを自分で閉じる
6. **ログアウト**ボタン: ブラウザを閉じてログイン情報を消去（次回[実行]時にログインからやり直し → ログインのテストに使える）
7. うまくいかない時は `ログ確認`

> 仕組み: 同梱Chromium をリモートデバッグ(CDP)付きの独立プロセスとして起動し、操作後は接続だけ切る。
> ログイン状態は Chromium の永続プロファイル（`<データ領域>/chrome_profile`）に保存。
> 既定値は `config.yml` の `tabs:` / `parallel:` / `keep_open:` / `debug_port:` で変更可（GUIの選択が優先）。

### 開発者向け
- 実行: `python -m app.main`（詳細・ビルドは `README_BUILD.md`）
- 設定: サイト固有情報は **`config.yml`**（URL/セレクタ/スクロール量）。コード修正なしで別サイト転用可
- 認証情報: **`.env`**（平文・要件通り）／ ログインセッション: `profiles/<name>/storage_state.json`
- ログ: `logs/YYYY-MM-DD.log`
- **データ保存先**: 開発時はプロジェクト直下。**配布時は書き込み可能なユーザー領域**
  （mac: `~/Library/Application Support/ScrollBot/`、Win: `%APPDATA%\ScrollBot\`）。
  ※ macOS の App Translocation でアプリ本体が読み取り専用になるため、`.env`/`profiles`/`logs`/`config.yml`
  はここに保存する（同梱Chromium はアプリ本体内・読み取りのみ）。診断: `ScrollBot --paths`

### 構成
```
app/
  main.py          エントリ（GUI起動 / --selftest）
  gui.py           Tkinter GUI（実行/設定/ログ確認・ステータス）
  core.py          Playwright制御（ログイン/遷移/汎用スクロール/セッション保存）
  config_loader.py config.yml 読み込み・検証
  credentials.py   .env 読み書き
  logger.py        ログ出力
  paths.py         開発/同梱のパス解決・同梱Chromium指定
config.yml         サイト定義（既定: Fチケ）
build/             PyInstaller spec・ビルドスクリプト・同梱Chromium
```

### スクロール完了判定（Phase 1 からの改良）
固定px/固定待機ではなく、**`scrollHeight` が連続 N 回不変なら最下部**と判定（遅延読み込み対応）。
末端到達時は追加待機（`settle_ms`）でAPI完了を待つ。特定日付のハードコードは持たない（サイト非依存）。

### 検証済み（2026-05-31）
- 開発実行で GUI 起動・設定保存（.env）・最下部(9/24)到達
- **パッケージ版（.app / onedir）をクリーン環境（Python無し）で実行 → 同梱Chromiumで最下部到達（`SELFTEST: OK`）**
- 実ログイン（ID/PW入力）の最終確認は、利用者が本物の認証情報を入力して実施

### Phase 1.2 以降（未実装）
複数アカウント切替 / スケジュール実行 / プロキシ・VPN / 出品ボタン自動クリック /
ランダム待機 / 自動更新 / 認証情報の暗号化 / Windows実機ビルド・コード署名・公証。
