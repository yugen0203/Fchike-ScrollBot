# スニペット01：マイシーズンシート 全試合データ一括取得（方法A）

- 目的: スクロールせずに全48試合のデータを取得し、コンソールに表で表示
- 実行場所: `https://ticket.fighters.co.jp/ticket/season`（ログイン済み）の DevTools Console
- 所要: 約15秒（1回のAPIコール）
- 注意: これは**データ取得のみ**。実画面（UI）は下まで表示されない（画面を下まで出すなら スニペット02）

## 使い方
1. シーズンシートのページを開く（ログイン済み）
2. F12 → Console
3. 下のコードを貼り付け → Enter
   - 貼り付けがブロックされたら、一度 `allow pasting` と入力して Enter → 再度貼り付け

## スニペット（1行・async IIFE）
```js
(async()=>{const t=localStorage.getItem(Object.keys(localStorage).find(k=>k.endsWith('.idToken')));const r=await fetch('https://ap.ticket.fighters.co.jp/pack/myseat?offset=0&limit=1000',{headers:{Authorization:'Bearer '+t},credentials:'include'}).then(r=>r.json());console.log('全'+r.eventTotalCnt+'試合');console.table(r.eventList.map(e=>({日時:new Date(e.startTime*1000).toLocaleString('ja-JP'),対戦:e.opponent.shortName,券数:(e.ticketList||[]).length})));})()
```

## 仕組みメモ
- API: `GET https://ap.ticket.fighters.co.jp/pack/myseat?offset=0&limit=1000`
- 認証: `Authorization: Bearer <idToken>`（localStorage の `...idToken` キー）
- レスポンス: `{ eventTotalCnt, cnt, eventList[] }`
- 取得結果: 全48試合（2026/5/31〜2026/9/24）
