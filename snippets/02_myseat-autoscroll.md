# スニペット02：マイシーズンシート 画面を一番下まで自動スクロール（方法B）

- 目的: 実画面（UI）を遅延読み込みさせ、最終試合 9/24 まで描画する
- 実行場所: `https://ticket.fighters.co.jp/ticket/season`（ログイン済み）の DevTools Console
- 所要: 約17〜18秒
- 新規タブでも「貼り付けるだけ」で 9/24 まで展開可能（タブごとに1回実行）

## 使い方
1. シーズンシートのページを開く（ログイン済み・最上部の状態でOK）
2. F12 → Console
3. 下のコードを貼り付け → Enter
   - 貼り付けがブロックされたら、一度 `allow pasting` と入力して Enter → 再度貼り付け
4. `✅ 9/24まで表示完了` がコンソールに出れば完了

## スニペット（1行・async IIFE / 最後に下端へ吸着）
```js
(async()=>{const se=document.scrollingElement,sleep=ms=>new Promise(r=>setTimeout(r,ms));let same=0,prevH=0;for(let i=0;i<150;i++){se.scrollTop+=600;await sleep(700);const end=se.scrollTop+innerHeight>=se.scrollHeight-2;if(end)await sleep(1000);if(se.scrollHeight===prevH){if(++same>=8)break}else same=0;prevH=se.scrollHeight;if(document.body.innerText.includes('9/24')&&end)break}se.scrollTop=se.scrollHeight;console.log('✅ 9/24まで表示完了 高さ='+se.scrollHeight)})()
```

## 調整ポイント
- 途中で止まる場合は待ち時間 `700` / `1000`（ミリ秒）を増やす（回線が遅い時）。
- 別シーズン等で最終日が変わる場合は、判定の `'9/24'` を最終試合日に変更。

## 仕組みメモ
- 「少しずつ下げて移動イベントを発火（scrollTop+=600）＋末端ではローディング完了を待機」で確実に読み込む。
- 単純な scrollTo(bottom) 連打＋短い待機だと、API(0.7〜1.3秒)完了前に「最下部」と誤判定し途中で止まる。
