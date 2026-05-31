# Fチケ マイシーズンシート 操作記録（task.md）

最終更新: 2026-05-31
対象サイト: https://ticket.fighters.co.jp/ticket/season （マイシーズンシート）
アカウント: シーズンシート会員（お客様コード＝ログインID）。※実際の認証情報は .env / chrome_profile に保存し、本リポジトリには記載しない

---

## 1. 背景・目的
- マイシーズンシートはスクロール連動の**遅延読み込み（無限スクロール）**で、10件ずつ追加表示される。
- ソースにクラス/IDが付いておらず、最後（9月の最終試合）まで見るには本来スクロールが必要。
- 「もっと速く」「画面を一番下まで」確実に到達する方法を検証・確立した。

## 2. 判明した仕組み（DevTools 調査結果）
- データ取得API:
  `GET https://ap.ticket.fighters.co.jp/pack/myseat?offset=0&limit=10`
  → スクロールで `offset=10,20,30,40 …` と 10件ずつ呼ばれる。
- 認証: リクエストヘッダ `Authorization: Bearer <JWT>`
  - JWT は **AWS Cognito の idToken**。
  - 保存場所: `localStorage` のキー `CognitoIdentityServiceProvider.<clientId>.<user>.idToken`
  - Cookie だけ（Bearer なし）だと 400「アクセスできません」。
- レスポンス構造: `{ result, eventTotalCnt, cnt, eventList[] }`
  - `eventList[].startTime`(UNIX秒), `opponent.shortName`, `ticketList[]`（座席・分配）など。
- 認証ガード以外に、難読化された長い POST（Akamai系WAF/ボット検知ビーコンとみられる）あり。データ取得には不要。

## 3. 全シーズン試合数
- **全 48 試合**（`eventTotalCnt = 48`）
- 期間: **2026/5/31（vs 読売）〜 2026/9/24（vs 東北楽天）**

## 4. 確立した2つの方法

### 方法A：データを最速で一括取得（スクロール不要・約15秒）
- API を `limit=1000` で1回叩くだけ。全48件取得。
- ⚠️ これは**データ取得のみ**。実画面（UI）は変わらない。
- スニペット → `snippets/01_myseat-fetch-all.{md,txt}`

### 方法B：実画面を一番下（9/24）まで描画（約17〜18秒）
- 遅延読み込みを発火させ続ける自動スクロール。
- 「少しずつ下げて移動イベントを出す＋各回ローディング完了を待つ」のがコツ。
  - 単純な `scrollTo(bottom)` の連打＋短い待機だと、ローディング(API 0.7〜1.3秒)前に「最下部」と誤判定して途中で止まる。
- 最後に下端へ吸着させて完了。
- スニペット → `snippets/02_myseat-autoscroll.{md,txt}`

## 5. 新規タブでの再現について
- 新規タブで「貼り付けるだけ」で 9/24 まで展開**可能**。実測 約18秒。
- 条件:
  1. タブが `ticket.fighters.co.jp/ticket/season` を開いている（空の chrome://newtab では不可）。
  2. ログイン済み（Cookie はタブ間共有、別タブでもログイン維持）。
  3. 新規タブは毎回「最上部・10件」から始まるため、**タブごとに1回**実行が必要。
- 「1つのスニペットで “新規タブを開く＋URL遷移＋スクロール” まで全部」は**不可**
  （ページ遷移で実行コンテキストがリセットされスクリプトが止まるため）。
  → URLを開くまでは手動 or ブックマーク、スクロールはスニペット、の分担。
- 補足: 方法Bをブックマークレット化すれば「1クリック」で最下部まで展開できる（未作成）。

## 6. コンソールで「実行できない」時の対処
- Chrome の貼り付けガード: 警告が出たら一度 `allow pasting` と入力して Enter → 再度貼り付け。
- 複数行コードで Enter が改行になる問題 → **1行版（IIFE）**を使う（保存済みスニペットは1行版）。
- 同じ `const` 再宣言エラー回避のため IIFE 形式 `(async()=>{ ... })()` にしてある。

## 7. 成果物（このフォルダ内）
- `task.md` … 本ファイル
- `snippets/01_myseat-fetch-all.md` / `.txt` … 方法A（全件データ取得）
- `snippets/02_myseat-autoscroll.md` / `.txt` … 方法B（画面を最下部まで）
- `マイシーズンシート_スクロール再現.mp4` … スクロール動作の再現動画（14.2秒）

## 8. 次の候補（未実施）
- `ticketList` を展開して「席種・座席番号・分配状況」まで一覧化
- CSV / スプレッドシート貼り付け用に出力
- 方法B のブックマークレット化

---

# Phase 1.1：ScrollBot デスクトップアプリ（完了・動作確認済み 2026-05-31）

Phase 1 のスクロール処理を、一般事務スタッフがダブルクリックで使える配布アプリ化したもの。
要件定義は `README.md` / 設計は plans の承認済みプラン参照。

## 技術スタック / 構成
- Python 3.12目標（開発検証は 3.13）、GUI=Tkinter、ブラウザ操作=Playwright(同梱Chromium)、配布=PyInstaller
- コード: `app/`（main/gui/core/config_loader/credentials/logger/paths/browser_launcher）
- 設定: `config.yml`（URL/セレクタ/スクロール量/タブ数/並行/keep_open/debug_port）。サイト固有値はここに集約しコードにハードコードしない
- 認証情報: `.env`（平文・要件通り）。GUI設定画面で保存
- 配布: `dist/ScrollBot.app`（Mac） / `dist/ScrollBot/`（onedir, Win同等）。ビルドは `bash build/make_mac.sh`

## 確定した重要仕様
- **データ保存先**: 配布時は書き込み可能なユーザー領域に保存（Mac: `~/Library/Application Support/ScrollBot/`、Win: `%APPDATA%\ScrollBot\`）。
  理由: macOS App Translocation でアプリ本体が読み取り専用になり、本体隣に保存すると失敗するため（→ 旧版の「保存できない無限ループ」の原因）。同梱Chromiumは読み取りのみなので本体内でOK。
- **ブラウザは独立プロセス**: 同梱Chromiumをリモートデバッグ(CDP)付きで別プロセス起動し、CDP接続で操作 → 操作後は**接続だけ切る**。
  → **ScrollBotアプリを閉じてもブラウザは残る**。ログイン状態はChromium永続プロファイル(`<データ領域>/chrome_profile`)に保存。
  → 既にブラウザ起動中(ポート応答)なら再接続して新規タブを追加。
- **ログインフロー(Fチケ シーズンシート)**: 未ログイン時は最初からモーダル表示。手順=
  `button:text-is('シーズンシート')` クリック → お客様コード `input:not([type=password]):visible` → パスワード `input[type=password]:visible` → `button:text-is('ログイン')` → 成功確認 `text=さん`。
  注意: お客様コード欄は type属性が無い(既定text)ため `input[type=text]` では取れない。判定は完全一致(text-is)必須（ログイン後に「マイシーズンシート」等があるため）。
- **スクロール完了判定**: `scrollHeight` が連続 `stable_rounds` 回不変で最下部（サイト非依存・特定日付ハードコード無し）。末端で `settle_ms` 追加待機。
- **複数タブ**: GUIで1〜20選択。**並行(parallel)**=全タブ同時スクロール（既定オン・速い）／オフ=順次。
- **ログアウト**ボタン: ブラウザ終了＋プロファイル削除（ログインからの再テスト用）。

## 動作確認済み（2026-05-31）
- 開発実行/パッケージ版とも GUI起動・設定保存(.env)・ログイン・最下部到達
- パッケージ版を Python無しクリーン環境で実行 → 同梱Chromiumで完走
- **実ログイン→スクロール完走（保存済み認証で成功）**
- 並行3タブ 約18秒（順次比 約1/5）
- アプリ停止後もブラウザ生存 / 再接続 / ログアウトでブラウザ終了
- 認証保存先 = Application Support（writable: True）で無限ループ解消

## 解決した不具合の履歴
1. 認証が保存できず無限ループ → データ保存先をユーザー領域へ（App Translocation対策）
2. ログイン時「シーズンシート」タブでタイムアウト → モーダルは初めから開いている＋セレクタ修正（text-is / type属性無し対応）
3. 処理後にブラウザが全部閉じる → 独立プロセス+CDPで接続だけ切る方式に変更（閉じない）
4. 完了後もスピナーが回り続ける → ワーカーが完了するようになり停止
5. 設定画面のボタン見切れ → ウィンドウ幅拡大

## ビルド/検証コマンド
- ビルド: `bash build/make_mac.sh`
- 保存先確認: `dist/ScrollBot.app/Contents/MacOS/ScrollBot --paths`
- 自己診断: `... --selftest [--tabs N]`（ヘッドレスで1回実行）
- CLI認証保存: `... --set-cred <ID> <PW>`

## Phase 1.2 以降（未実装）
複数アカウント切替UI / スケジュール実行 / プロキシ・VPN / 出品ボタン自動クリック /
ランダム待機 / 自動更新 / 認証情報の暗号化 / Windows実機ビルド・コード署名・公証。
