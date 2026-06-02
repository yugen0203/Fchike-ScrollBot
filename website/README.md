# Rion Lab Japan コーポレートサイト（リニューアル版）

WordPress を使わない、**軽量・高速**なコーポレートサイトです。
**曜日でデザインが切り替わり**（月〜金の5テーマ、土日は金曜を継続）、
コンテンツは **microCMS**、お問い合わせは **PHP + SQLite** の自前フォーム＋管理画面で管理します。

詳細仕様は [`要件定義書.md`](要件定義書.md) を参照してください。

---

## 構成

```
website/
├── index.html / company.html / services.html   … 公開ページ（静的）
├── contact.php                                  … お問い合わせフォーム（PHP）
├── assets/css/{base,themes}.css                 … スタイル（themes=曜日テーマ）
├── assets/js/{theme,cms,main}.js                … 曜日判定 / CMS取得 / UI
├── api/cms.php                                   … microCMS プロキシ
├── admin/                                        … 管理画面（ログイン/一覧/詳細/CSV）
├── lib/db.php                                    … SQLite 接続
└── data/                                         … SQLite 実体（直接アクセス禁止）
```

- フレームワーク・ビルド不要。ファイルをそのままサーバーへ置けば動きます。
- アイコンは Font Awesome（CDN）、フォントは Google Fonts。
- 画像は使わず SVG/CSS で描画（写真を足す場合は `assets/img/README.md`）。

---

## 曜日替わりデザイン

| 曜日 | テーマ | 配色 |
|---|---|---|
| 月 | Fresh Start | ブルー / クリーン |
| 火 | Momentum | コーラル / 動的 |
| 水 | Flow | ティール / 曲線 |
| 木 | Trust | ネイビー＆ゴールド / 端正 |
| 金（＋土日） | Spark | パープル / 華やか |

- 日本時間(JST)の曜日で自動切替。
- 確認用に `?theme=mon|tue|wed|thu|fri` を付けると任意テーマをプレビューできます。
  例: `index.html?theme=thu`

---

## セットアップ（Xサーバー）

### 1. ファイルを設置
`website/` 配下を、公開ディレクトリ（例: `public_html/`）へアップロードします。
（FTP / ファイルマネージャ / `git pull` いずれでも可）

### 2. 管理画面のパスワード設定
```
admin/config.sample.php → admin/config.php にコピー
```
サーバー上でハッシュを生成して `ADMIN_PASS_HASH` に貼り付け:
```bash
php -r "echo password_hash('好きなパスワード', PASSWORD_DEFAULT), PHP_EOL;"
```
`ADMIN_USER` も任意の値に変更してください。

### 3. microCMS 連携（任意・後からでOK）
1. [microCMS](https://microcms.io/) で無料アカウント＆サービスを作成
2. API「news」を作成（フィールド例: `title`(テキスト), `category`(テキスト/セレクト), `url`(任意)）
3. 読み取り用 API キーを取得
4. 設定ファイルを用意:
   ```
   api/cms.config.sample.php → api/cms.config.php にコピーして値を記入
   ```
   未設定でもサイトは内蔵のサンプルお知らせで正常表示されます。

### 4. メール送信
`contact.php` の `ADMIN_MAIL` を受信したいアドレスに変更してください
（既定: `staff@rion-lab-japan.com`）。Xサーバーは `mb_send_mail()` が利用可能です。

### 5. 動作確認
- `https://ドメイン/` … トップ（曜日テーマ）
- `https://ドメイン/contact.php` … 送信→完了表示
- `https://ドメイン/admin/` … ログイン→一覧に反映、CSV出力

---

## ローカル確認

PHPがあれば簡易サーバーで確認できます（フォーム・管理画面も動作）:
```bash
cd website
php -S localhost:8000
# http://localhost:8000/                … トップ
# http://localhost:8000/contact.php      … フォーム
# http://localhost:8000/admin/           … 管理画面（先に admin/config.php を用意）
```
静的ページ（HTML/CSS/JS）だけならファイルを直接ブラウザで開いても確認できます。

---

## セキュリティ要点

- 管理画面はログイン必須・パスワードはハッシュ保存・ログイン試行制限あり。
- フォームは CSRF トークン＋ハニーポット＋サーバー側バリデーション＋簡易レート制限。
- microCMS の API キーは PHP プロキシ側にのみ保持（ブラウザに出さない）。
- `data/`（SQLite）は `.htaccess` で直接アクセス禁止。
- `admin/config.php` と `api/cms.config.php` は `.gitignore` 済み（コミットしない）。

> 推奨: 可能なら `admin/` に Basic 認証（`.htaccess`）を追加し二重化、SQLite を公開ディレクトリ外へ移すとより安全です。

---

## Cloudflare Pages へのプレビューデプロイ（静的のみ）

Cloudflare Pages は **PHPを実行しません**。そのため Pages では
「お問い合わせ／管理画面／CMSプロキシ」は動かず、**見た目（静的ページ）の確認用**になります。
（同梱の `_redirects` で、PHP系パスはソースが見えないよう退避し、`/contact.php` は
`contact-preview.html` を表示します。）

### 方法A: ダッシュボードでGit連携（トークン不要・おすすめ）
1. Cloudflare ダッシュボード → **Workers & Pages → Create → Pages → Connect to Git**
2. リポジトリ `yugen0203/Fchike-ScrollBot` と対象ブランチを選択
3. ビルド設定:
   - Framework preset: **None**
   - Build command: **空欄**
   - Build output directory: **`website`**
4. Save and Deploy → `https://＜project＞.pages.dev` が発行される

### 方法B: CLI（wrangler）でデプロイ
```bash
# 要: Cloudflare APIトークン（権限: Account → Cloudflare Pages: Edit）
export CLOUDFLARE_API_TOKEN=＜トークン＞
export CLOUDFLARE_ACCOUNT_ID=＜アカウントID＞
npx wrangler pages deploy website --project-name=rion-lab-preview --branch=preview
```

> 本番（フォーム・管理画面込み）は Xサーバー（PHP）へ。Pages はあくまで静的プレビュー用です。

---

## 確定情報への差し替え（要対応）

HTML内の `〔要確認〕` は仮の表記です。確定後に差し替えてください。
- 本社・支社の正式住所、電話番号、問い合わせメール
- 代表メッセージ・実績・採用情報 等（microCMS API追加で拡張可）
