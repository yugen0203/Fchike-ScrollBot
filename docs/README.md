# 出品Bot（ListBot）／ScrollBot 使い方ガイド・索引

Fチケ（北海道日本ハムファイターズ シーズンシート）の自動化アプリの説明資料です。
**お使いのパソコンに合わせて**マニュアルを選んでください。

## 📘 操作マニュアル（PDF・初心者向け・画面図つき）

**配布用はPDFです。** お使いのPCに合わせて選んでください。

| あなたのPC | マニュアル(PDF) |
|---|---|
| 🪟 **Windows** | 👉 [出品Bot_使い方_Windows.pdf](pdf/出品Bot_使い方_Windows.pdf) |
| 🍎 **Mac** | 👉 [出品Bot_使い方_Mac.pdf](pdf/出品Bot_使い方_Mac.pdf) |

補足資料(PDF)： 👉 [出品Bot_補足_設定と連番ルール.pdf](pdf/出品Bot_補足_設定と連番ルール.pdf)（連番ルールの詳しい設定・速度調整・安全運用）

> 元になったMarkdownも同梱しています（[Windows](出品Bot_使い方_Windows.md) / [Mac](出品Bot_使い方_Mac.md) / [補足](補足_設定と連番ルール.md)）。PDFはこれを `build/_devtest_md2pdf.py` で生成しています。

## ⬇️ ダウンロード（Windows版）

GitHub Releases から誰でもダウンロードできます。

- **出品Bot（自動出品）**: [ListBot-Windows.zip](https://github.com/yugen0203/Fchike-ScrollBot/releases/download/v2.0.0/ListBot-Windows.zip)
- **ScrollBot（自動スクロール）**: [ScrollBot-Windows.zip](https://github.com/yugen0203/Fchike-ScrollBot/releases/download/v2.0.0/ScrollBot-Windows.zip)
- リリース一覧: https://github.com/yugen0203/Fchike-ScrollBot/releases

> Mac版はソースからビルドします（`bash build/make_listbot_mac.sh` → `dist/出品Bot.app`）。

## 🧭 2つのアプリの違い

| アプリ | できること |
|---|---|
| **ScrollBot** | ログイン → マイシーズンシートを一番下まで自動スクロール（最新試合を表示） |
| **出品Bot（ListBot）** | 指定日付の自席を **最高額で自動出品**（連番ルール・複数日付の並行処理つき） |

## ⚠️ 安全のための最重要ポイント

- 出品Botは **実際にチケットを出品** します。お試しは必ず **「確認モード」ON**（最後のボタン直前で停止）。
- 間違えて出品したら **「出品キャンセル」** で取り消せます（各マニュアル第8章）。
