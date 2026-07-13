/* =====================================================================
   cms.js — microCMS（お知らせ）取得
   PHPプロキシ api/cms.php 経由で取得し、APIキーをブラウザに晒さない。
   取得に失敗した場合は内蔵フォールバックで必ず表示する。
   ===================================================================== */
(function () {
  "use strict";

  // CMS未設定でも表示できるフォールバック（microCMS連携後は自動で上書き）
  var FALLBACK = [
    { date: "2026-05-20", category: "お知らせ", title: "コーポレートサイトをリニューアルしました" },
    { date: "2026-04-10", category: "実績",     title: "製造業向け在庫管理アプリの開発支援を開始" },
    { date: "2026-03-01", category: "DX研修",   title: "DX研修ラボ 新カリキュラム『生成AI活用』を公開" },
    { date: "2026-02-12", category: "お知らせ", title: "ベトナム・ダナン開発拠点のエンジニアを増員" }
  ];

  function fmtDate(s) {
    var d = new Date(s);
    if (isNaN(d)) return s;
    return d.getFullYear() + "." +
      String(d.getMonth() + 1).padStart(2, "0") + "." +
      String(d.getDate()).padStart(2, "0");
  }

  function render(list, mount) {
    mount.innerHTML = list.slice(0, 5).map(function (n) {
      return '<a class="news__item" href="' + (n.url || "#") + '">' +
        '<span class="news__date">' + fmtDate(n.date || n.publishedAt) + '</span>' +
        '<span class="news__tag">' + (n.category || "お知らせ") + '</span>' +
        '<span class="news__title">' + escapeHtml(n.title || "") + '</span>' +
        '</a>';
    }).join("");
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var mount = document.querySelector("[data-news]");
    if (!mount) return;

    fetch("api/cms.php?endpoint=news&limit=5", { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error("cms " + r.status); return r.json(); })
      .then(function (data) {
        var list = (data && data.contents) ? data.contents : (Array.isArray(data) ? data : null);
        render(list && list.length ? list : FALLBACK, mount);
      })
      .catch(function () { render(FALLBACK, mount); });
  });
})();
