/* =====================================================================
   theme.js — 曜日替わりテーマ
   日本時間(JST)の曜日で data-theme を切替。土日は金曜を継続。
   ?theme=mon|tue|wed|thu|fri でプレビュー可。
   テーマごとに異なるヒーローSVGアートと曜日バッジも描画する。
   ===================================================================== */
(function () {
  "use strict";

  var THEMES = ["mon", "tue", "wed", "thu", "fri"];
  var META = {
    mon: { label: "Monday",    jp: "月曜",  concept: "Fresh Start" },
    tue: { label: "Tuesday",   jp: "火曜",  concept: "Momentum" },
    wed: { label: "Wednesday", jp: "水曜",  concept: "Flow" },
    thu: { label: "Thursday",  jp: "木曜",  concept: "Trust" },
    fri: { label: "Friday",    jp: "金曜",  concept: "Spark" }
  };

  /* JSTの曜日(0=日〜6=土)を取得 */
  function jstDay() {
    var parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Tokyo", weekday: "short"
    }).format(new Date());
    var map = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
    return map[parts];
  }

  function themeForDay(d) {
    switch (d) {
      case 1: return "mon";
      case 2: return "tue";
      case 3: return "wed";
      case 4: return "thu";
      case 5: return "fri";
      default: return "fri"; // 土(6)・日(0) は金曜を継続
    }
  }

  /* テーマ別ヒーローSVGアート（軽量インラインSVG） */
  function heroArt(theme) {
    var g = 'url(#g)';
    var head =
      '<svg viewBox="0 0 400 400" role="img" aria-label="Rion Lab Japan key visual" xmlns="http://www.w3.org/2000/svg">' +
      '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">' + gradStops(theme) +
      '</linearGradient></defs>';
    var body = {
      mon:
        '<rect x="40" y="40" width="320" height="320" rx="10" fill="none" stroke="' + g + '" stroke-width="2" opacity=".5"/>' +
        '<g fill="' + g + '">' +
        '<rect x="70" y="70" width="120" height="120" rx="8"/>' +
        '<rect x="210" y="70" width="120" height="120" rx="8" opacity=".55"/>' +
        '<rect x="70" y="210" width="120" height="120" rx="8" opacity=".35"/>' +
        '<circle cx="270" cy="270" r="60"/></g>' +
        '<line x1="70" y1="200" x2="330" y2="200" stroke="' + g + '" stroke-width="2" opacity=".4"/>',
      tue:
        '<g fill="' + g + '">' +
        '<polygon points="60,340 200,60 240,80 100,360"/>' +
        '<polygon points="160,340 300,60 340,80 200,360" opacity=".55"/>' +
        '<circle cx="300" cy="120" r="44" opacity=".8"/></g>' +
        '<g stroke="' + g + '" stroke-width="3" opacity=".5">' +
        '<line x1="40" y1="120" x2="120" y2="120"/><line x1="40" y1="150" x2="95" y2="150"/></g>',
      wed:
        '<g fill="none" stroke="' + g + '" stroke-width="3">' +
        '<path d="M40 140 Q120 80 200 140 T360 140" opacity=".7"/>' +
        '<path d="M40 200 Q120 140 200 200 T360 200" opacity=".5"/>' +
        '<path d="M40 260 Q120 200 200 260 T360 260" opacity=".35"/></g>' +
        '<circle cx="200" cy="200" r="90" fill="' + g + '" opacity=".18"/>' +
        '<circle cx="200" cy="200" r="46" fill="' + g + '"/>',
      thu:
        '<g stroke="' + g + '" stroke-width="1.5" opacity=".5">' +
        '<line x1="100" y1="40" x2="100" y2="360"/><line x1="200" y1="40" x2="200" y2="360"/>' +
        '<line x1="300" y1="40" x2="300" y2="360"/><line x1="40" y1="120" x2="360" y2="120"/>' +
        '<line x1="40" y1="240" x2="360" y2="240"/></g>' +
        '<rect x="120" y="140" width="160" height="120" fill="none" stroke="' + g + '" stroke-width="3"/>' +
        '<circle cx="200" cy="200" r="34" fill="' + g + '"/>' +
        '<rect x="150" y="290" width="100" height="6" fill="' + g + '"/>',
      fri:
        '<g fill="' + g + '">' +
        '<circle cx="150" cy="150" r="90"/>' +
        '<circle cx="270" cy="250" r="60" opacity=".6"/></g>' +
        '<polygon points="260,60 340,60 300,140" fill="' + g + '" opacity=".7"/>' +
        '<g fill="none" stroke="' + g + '" stroke-width="3" opacity=".55">' +
        '<circle cx="150" cy="150" r="120"/><circle cx="270" cy="250" r="100"/></g>'
    };
    return head + (body[theme] || body.mon) + '</svg>';
  }

  function gradStops(theme) {
    var c = {
      mon: ["#1f6dff", "#36c6ff"],
      tue: ["#ff7a18", "#ff3d6e"],
      wed: ["#11b58c", "#7fe3c0"],
      thu: ["#1b2c4d", "#b8893b"],
      fri: ["#7b2ff7", "#ff7eb3"]
    }[theme] || ["#1f6dff", "#36c6ff"];
    return '<stop offset="0" stop-color="' + c[0] + '"/><stop offset="1" stop-color="' + c[1] + '"/>';
  }

  /* 適用 */
  var qs = new URLSearchParams(location.search);
  var override = qs.get("theme");
  var theme = (THEMES.indexOf(override) >= 0) ? override : themeForDay(jstDay());

  document.documentElement.setAttribute("data-theme", theme);

  document.addEventListener("DOMContentLoaded", function () {
    // ヒーローアート
    document.querySelectorAll("[data-hero-art]").forEach(function (el) {
      el.innerHTML = heroArt(theme);
    });
    // 曜日バッジ
    var badge = document.querySelector("[data-day-badge]");
    if (badge) {
      var m = META[theme];
      badge.innerHTML =
        '<span class="day-badge__dot"></span>' +
        '<span>' + m.label + ' <small>/ ' + m.concept + '</small></span>';
      badge.setAttribute("title", "本日のテーマ：" + m.jp + "（" + m.concept + "）");
    }
  });

  // 他スクリプトから参照できるよう公開
  window.RION_THEME = theme;
})();
