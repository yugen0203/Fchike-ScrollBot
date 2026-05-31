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

---

# Phase 2：出品Bot（ListBot）＝ 別アプリ（開発中 2026-05-31〜）

要件定義は README.md「Phase 2」節。ScrollBot を残し、`listbot/` に別アプリとして新規作成。

## 確認した出品フロー（画面収録 2026-05-31 19.44.15.mov）
1. シーズンページ → 試合カードをクリック → 座席カードの「出品する」
2. 出品登録 STEP1: 各座席の鉛筆 → 価格範囲(¥min〜¥max)の**最高額**を入力 → 次へ
3. STEP2: バラ売り可/不可（連番=不可でまとめ売り）→ 次へ
4. STEP3: 確認（販売価格合計・振込予定）→「出品する」→ 出品完了
   - URL: /resale/regista/ticket/... → /resale/regista/ticket/complete

## ユーザー確定事項（2026-05-31）
- 連番分割: 既定=連続席はまとめて連番出品（5,6→2連番 / 5,6,7,8→4連番）。ケース別分割も設定可。
- 並行: 1ブラウザ・複数タブ（ログイン共有）。
- 出品確定: フル自動（最終出品まで）。※安全のため確認モードもトグルで用意。
- 構成: 同一リポジトリ内に別アプリ（listbot/）。

## 実装済み（雛形・テスト済みの純粋ロジック）
- listbot/ 一式: paths(APP_NAME=ListBot, config_listbot.yml, port 9344) / logger / credentials(.env.listbot)
  / browser_launcher(chrome_profile_listbot) / config_loader / core(ログイン+スクロール流用)
  / grouping(連番グルーピング・設定可) / pricing(最高額解析) / listing(出品オーケストレーション)
  / runner(複数日付・並行タブ) / gui(セットアップGUI) / main(CLI: --paths/--set-cred/--group/--capture)
- 単体テスト: test_grouping.py 全PASS。日付範囲/座席ラベル/価格パースも動作確認済み。
- config_listbot.yml: ログインはScrollBot流用。出品セレクタはテキスト一致系を推定済み。

## 未確定（実DOM捕捉が必要 / TODO in config_listbot.yml の sites.fchike.listing）
- game_card / game_date_text（試合カードと日付）
- seat_row / seat_label_text / price_range_text / price_edit_button(鉛筆) / price_input（STEP1）
- seat_checkbox（要確認）
- 推定済み: list_button, next_button, bara_ok/ng_radio(text), submit_button, complete_marker
- 捕捉手段: `python -m listbot.main --capture [--date 9/17]`（ログイン→スクロール→HTML/スクショ保存。出品はしない）
  ※ ListBot は独立ログイン（.env.listbot未設定）。捕捉には認証情報が必要。

## 実DOM確定（2026-05-31 捕捉済み）
出品登録は【1ページ順次展開】: STEP1価格→次へ→STEP2バラ売り→次へ→STEP3確認→出品する。
- 試合カード: `li.UITicketSliderPc_List_Item` / 日付 `.UITicketAccordion_Button_Date_Day`(例 9/17)
- 展開: `button.UITicketAccordion_Button` / 未出品ボタン: role=button name=出品する (`UIAppButton _small _none`)
- 座席行: `.UIResaleTicketCheckBox.PageResaleRegister_Step_Ticket_Item`
- チェック: `button.UIResaleTicketCheckBox_Check`(_checked) / 座席名: `.UISeatPrice_Name`
- 価格範囲: `.UIPriceEditor_Left_Note`(¥3,600〜¥6,900) / 入力: `input.UIPriceEditor_Right_Input`
  ★入力後 **Tab(blur)で確定**しないと「次へ」が有効化されない
- 操作ボタン: `#PageResaleRegisterTranslateBtn`（ラベルが 次へ→出品する に変化。最終は class `_danger`）
- バラ売り: radio name=isPackage、`text=バラ売り不可`/`バラ売り可` で選択
- 完了: text「出品完了」、URL /resale/register/complete

## 検証済み（2026-05-31〜06-01）
- 確認モードで 9/17 の全フロー（5,6番→[2連番]→¥6,900→バラ売り不可→STEP3）動作
- **本番フロー：実際に「出品する」→出品完了まで成功**（9/17 5,6番 ¥6,900 連番、振込¥13,140）→ ユーザーが手動キャンセル済み
- grouping/pricing/date 単体テスト 全PASS

## 検証済み（追記 2026-06-01）
- 並行2タブ（6/12 & 9/17 同時）動作。6/12=6席を `[5,6][8,9][5,6]` の3グループへ正しく分割、座席別最高額(¥8,400/¥6,900)を検出。
- ビルド完了: `bash build/make_listbot_mac.sh` → dist/ListBot/(onedir) + dist/出品Bot.app。
  パッケージ版 --paths/--group 動作確認（独立データ領域 ~/Library/Application Support/ListBot/）。
- Windows CI: .github/workflows/windows-build.yml に build-listbot-windows ジョブ追加（ListBot-Windows.zip）。

## Phase 2 ステータス: 機能実装・検証完了。残は任意（アイコン/コード署名/公証、スケジュール実行等）。
ビルド: mac=`bash build/make_listbot_mac.sh` / Win=GitHub Actions。
開発実行: `python -m listbot.main`。CLI: --paths/--set-cred/--group/--capture。

---

# Phase 2 完了サマリ（2026-06-01）

## リポジトリ / コミット
- GitHub: https://github.com/yugen0203/Fchike-ScrollBot （PUBLIC）
- コミット: `6d4a81c Phase 2: 出品Bot（ListBot）`（21ファイル/+2,357行）→ main に push 済み

## 実用テスト結果（製品コード ListingRunner・並行・確認モード）
- 範囲 9/15〜9/20 を解析 → 対象 [9/15,9/17,9/19,9/20] を 4タブ並行
- 9/15・9/19・9/20=未出品席なしでスキップ / 9/17=未出品2席 → [2連番:5,6]→¥6,900→バラ売り不可→STEP3停止
- 誤出品なし（確認モード）

## 配布物
- Windows: GitHub Actions「Build Windows EXE」の Artifacts → `ScrollBot-Windows.zip` / `ListBot-Windows.zip`
  - Actions: https://github.com/yugen0203/Fchike-ScrollBot/actions/workflows/windows-build.yml
  - （安定リンク用に Release も作成。Releases: https://github.com/yugen0203/Fchike-ScrollBot/releases ）
- mac: `dist/出品Bot.app` / `dist/ListBot/`（`bash build/make_listbot_mac.sh`）

## 連番ルールの設定場所
- GUI: 「連続席はまとめて連番出品」/「最大席数で分割」+最大席数+端数
- config_listbot.yml の `grouping:`（mode / max_group_size / remainder / partition_overrides / single_as_bara_ok）

## 安全運用メモ
- 既定フル自動＝実出品確定。テストは確認モードON、または出品後に手動キャンセル（テスト可: 9/17 18:00）。
- サイトUI変更時は config_listbot.yml の sites.fchike.listing を修正（`--capture` で実DOM再取得）。
