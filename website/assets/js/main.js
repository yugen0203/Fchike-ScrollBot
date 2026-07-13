/* =====================================================================
   main.js — ナビ開閉・スクロール演出・フォームの簡易バリデーション補助
   ===================================================================== */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    /* モバイルナビ */
    var toggle = document.querySelector(".nav__toggle");
    var links = document.querySelector(".nav__links");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        var open = links.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      links.querySelectorAll("a").forEach(function (a) {
        a.addEventListener("click", function () { links.classList.remove("open"); });
      });
    }

    /* スクロールで出現 */
    var reveals = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window && reveals.length) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
        });
      }, { threshold: 0.12 });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      reveals.forEach(function (el) { el.classList.add("in"); });
    }

    /* 数値カウントアップ */
    var nums = document.querySelectorAll("[data-count]");
    if ("IntersectionObserver" in window && nums.length) {
      var io2 = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          var el = e.target, target = parseFloat(el.dataset.count), suffix = el.dataset.suffix || "";
          var start = performance.now(), dur = 1200;
          function step(now) {
            var p = Math.min((now - start) / dur, 1);
            var val = Math.floor((1 - Math.pow(1 - p, 3)) * target);
            el.textContent = val + suffix;
            if (p < 1) requestAnimationFrame(step);
          }
          requestAnimationFrame(step);
          io2.unobserve(el);
        });
      }, { threshold: 0.5 });
      nums.forEach(function (el) { io2.observe(el); });
    }
  });
})();
