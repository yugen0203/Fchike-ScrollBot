"""出品の全体オーケストレーション（ListBot 用）。

  ログイン(1回) → 最下部までスクロール → 試合日付を発見 → 対象期間と突合
  → 各日付を出品（順次 or 複数タブ並行）

並行は「1ブラウザ・複数タブ（ログイン共有）」。Playwright 同期APIはスレッド毎に
独立した接続が必要なため、各タブ用スレッドが同じ CDP ブラウザへ connect_over_cdp する。
セッション(Cookie)はブラウザ共有なのでログインは最初の1回で済む。
"""
from __future__ import annotations

import datetime as _dt
import re
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

from .config_loader import active_site
from .core import LoginError, Session
from .listing import ListingBot, ListingResult
from .logger import Logger

Date = Tuple[int, int]  # (month, day)


def parse_date_range(date_from: str, date_to: str) -> List[Date]:
    """'2026-09-17' / '9/17' / '9-17' 形式の from..to を (month,day) リストに展開。

    年は無視して month/day のみ扱う（同一シーズン想定）。
    """
    f = _parse_md(date_from)
    t = _parse_md(date_to)
    if not f or not t:
        raise ValueError("日付の形式が不正です（例: 2026-09-17 / 9/17）")
    # 年をまたがない前提。datetime で日付列を作るため便宜上 2000 年を使う
    y = 2000
    d0 = _dt.date(y, f[0], f[1])
    d1 = _dt.date(y, t[0], t[1])
    if d1 < d0:
        d0, d1 = d1, d0
    out: List[Date] = []
    d = d0
    while d <= d1:
        out.append((d.month, d.day))
        d += _dt.timedelta(days=1)
    return out


def _parse_md(s: str) -> Optional[Date]:
    if not s:
        return None
    s = s.strip()
    m = re.search(r"(?:\d{4}[-/])?(\d{1,2})[-/月](\d{1,2})", s)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


class ListingRunner:
    def __init__(self, cfg: Dict, creds: Dict[str, str], log: Logger,
                 cancel_check: Callable[[], bool] | None = None):
        self.cfg = cfg
        self.creds = creds
        self.log = log
        self.cancel_check = cancel_check or (lambda: False)
        self.site = active_site(cfg)

    def run(self, date_from: str, date_to: str) -> Dict:
        targets = parse_date_range(date_from, date_to)
        self.log.info(f"出品対象期間: {date_from}〜{date_to} → {len(targets)}日 {targets}")

        sess = Session(self.cfg, self.creds, self.log, self.cancel_check)
        sess.open()
        summary = {"listed_groups": 0, "skipped": [], "errors": [], "stopped_for_confirm": False}
        try:
            ctx = sess.context
            page0 = ctx.new_page()
            self.log.status("ログイン確認中")
            sess.ensure_login(page0)
            sess.close_initial_blank_tabs()

            self.log.status("最下部まで読み込み中")
            sess.scroll_to_bottom(page0)

            available = self._discover_dates(page0)
            self.log.info(f"出品可能な試合日付: {sorted(available)}")
            todo = [d for d in targets if d in available]
            if not todo:
                self.log.warn("対象期間に出品可能な試合がありませんでした")
                summary["skipped"].append("対象期間に試合なし")
                return summary

            self.log.info(f"出品実行: {todo}")
            parallel = bool(self.cfg.get("parallel", True)) and len(todo) > 1
            max_tabs = max(1, int(self.cfg.get("max_parallel_tabs", 5)))

            if parallel:
                self._run_parallel(todo, max_tabs, summary)
            else:
                bot = ListingBot(self.cfg, self.log, self.cancel_check,
                                 scroll_fn=sess.scroll_to_bottom)
                for (mo, da) in todo:
                    if self.cancel_check():
                        break
                    res = ListingResult()
                    bot.list_date(page0, mo, da, res)
                    self._merge(summary, res)
                    if res.stopped_for_confirm:
                        break
                    # 次の日付のためトップに戻す
                    self._reset_to_top(sess, page0)

            self.log.info(
                f"出品完了サマリ: 出品 {summary['listed_groups']} グループ / "
                f"スキップ {summary['skipped']} / エラー {len(summary['errors'])}"
            )
            return summary
        finally:
            sess.close()

    # ---- 日付の発見 -----------------------------------------------------
    def _discover_dates(self, page) -> set:
        """シーズンページ上の試合カードの日付(month,day)を収集する。"""
        lsel = self.site.get("listing") or {}
        item_sel = lsel.get("game_item", "li.UITicketSliderPc_List_Item")
        date_sel = lsel.get("game_date_text", ".UITicketAccordion_Button_Date_Day")
        found = set()
        days = page.locator(f"{item_sel} {date_sel}")
        for i in range(days.count()):
            try:
                text = days.nth(i).inner_text(timeout=1500)
            except Exception:
                continue
            md = _parse_md(text.replace(" ", ""))
            if md:
                found.add(md)
        return found

    def _reset_to_top(self, sess: Session, page):
        try:
            page.goto(self.site["start_url"], wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        sess.scroll_to_bottom(page)

    # ---- 並行（複数タブ）------------------------------------------------
    def _run_parallel(self, todo: List[Date], max_tabs: int, summary: Dict):
        """各日付を別タブ・別スレッドで同時出品する（ログインはブラウザ共有）。"""
        port = int(self.cfg.get("debug_port", 9344))
        batches = todo[:max_tabs]  # 最初の max_tabs 日付を同時に
        remaining = todo[max_tabs:]
        if remaining:
            self.log.info(f"同時 {len(batches)} タブで処理。残り {len(remaining)} 日付は後続バッチで処理")

        lock = threading.Lock()

        def worker(date: Date):
            mo, da = date
            from playwright.sync_api import sync_playwright
            from . import paths
            paths.configure_playwright_browsers_path()
            p = sync_playwright().start()
            try:
                browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                ctx = browser.contexts[0] if browser.contexts else browser.new_context()
                page = ctx.new_page()
                page.goto(self.site["start_url"], wait_until="domcontentloaded", timeout=30000)
                sess = Session(self.cfg, self.creds, self.log, self.cancel_check)
                # スクロールだけ流用（このタブは既にログイン済みセッション共有）
                sess.scroll_to_bottom(page)
                bot = ListingBot(self.cfg, self.log, self.cancel_check,
                                 scroll_fn=sess.scroll_to_bottom)
                res = ListingResult()
                bot.list_date(page, mo, da, res)
                with lock:
                    self._merge(summary, res)
            except Exception as e:
                with lock:
                    summary["errors"].append(f"{mo}/{da} タブ処理失敗: {e}")
                self.log.error(f"{mo}/{da} タブ処理失敗: {e}")
            finally:
                try:
                    p.stop()
                except Exception:
                    pass

        def run_batch(batch: List[Date]):
            threads = [threading.Thread(target=worker, args=(d,), daemon=True) for d in batch]
            for t in threads:
                t.start()
                time.sleep(0.8)  # タブ生成を少しずらす
            for t in threads:
                t.join()

        run_batch(batches)
        # 後続バッチ（max_tabs を超える分）
        idx = 0
        while remaining and not self.cancel_check():
            nxt = remaining[:max_tabs]
            remaining = remaining[max_tabs:]
            idx += 1
            self.log.status(f"後続バッチ {idx} を処理中（{len(nxt)}日付）")
            run_batch(nxt)

    # ---- 集計 -----------------------------------------------------------
    @staticmethod
    def _merge(summary: Dict, res: ListingResult):
        summary["listed_groups"] += res.listed_groups
        summary["skipped"].extend(res.skipped)
        summary["errors"].extend(res.errors)
        if res.stopped_for_confirm:
            summary["stopped_for_confirm"] = True
