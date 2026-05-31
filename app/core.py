"""ScrollBot 本体。Playwright(同期API) で
セッション読込 → ログイン判定 → 自動ログイン → 目的ページ遷移 →
汎用スクロール(最下部まで) → セッション保存 を行う。

サイト固有の値（URL/セレクタ/スクロール量）は config から受け取り、
このコードにハードコードしない（別サイト転用可能）。
"""
from __future__ import annotations

import time
from typing import Callable, Dict

from . import paths
from .config_loader import active_site
from .logger import Logger


class LoginError(Exception):
    pass


class ScrollBot:
    def __init__(self, cfg: Dict, creds: Dict[str, str], log: Logger,
                 cancel_check: Callable[[], bool] | None = None):
        self.cfg = cfg
        self.creds = creds
        self.log = log
        self.cancel_check = cancel_check or (lambda: False)

    # ---- 公開API -------------------------------------------------------
    def run(self) -> None:
        # 同梱Chromium を使う設定（import 前に）
        paths.configure_playwright_browsers_path()
        from playwright.sync_api import sync_playwright
        from . import browser_launcher as bl

        site = active_site(self.cfg)
        b = self.cfg["browser"]
        headless = bool(b.get("headless", False))
        # ヘッド表示 & keep_open のときは、操作後もブラウザを残す(独立プロセス)
        detach = (not headless) and bool(self.cfg.get("keep_open", True))
        port = int(self.cfg.get("debug_port", 9333))
        width = int(b["viewport"]["width"])
        height = int(b["viewport"]["height"])

        p = sync_playwright().start()
        proc = None
        browser = None
        try:
            exe = p.chromium.executable_path

            reused = bl.port_alive(port)
            if reused:
                self.log.info("既存ブラウザに接続")
            else:
                self.log.status("ブラウザを起動中")
                proc = bl.launch_detached(exe, port, headless, width, height)
                if not bl.wait_port(port, 30):
                    raise LoginError("ブラウザの起動に失敗しました")

            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            initial_pages = list(context.pages)

            # 1枚目のページ（新規起動時は最初の空タブを使う / 再利用時は新規タブ）
            page = context.new_page()
            self.log.status("ページを開いています")
            self._goto(page, site["start_url"])

            if self._needs_login(page, site):
                self.log.status("ログイン中")
                self._login(page, site)
                self.log.info("ログイン成功（プロファイルに保存）")
            else:
                self.log.info("ログイン済み（セッション再利用）")

            tabs = max(1, int(self.cfg.get("tabs", 1)))
            parallel = bool(self.cfg.get("parallel", True))
            target = site["target_url"]

            # タブを用意（1枚目=page、2枚目以降は新規タブ）
            pages = [page]
            for _ in range(tabs - 1):
                if self.cancel_check():
                    break
                pages.append(context.new_page())
            for idx, pg in enumerate(pages):
                if self._norm(pg.url) != self._norm(target):
                    self.log.status(f"タブ {idx + 1}/{tabs}: ページを開いています")
                    self._goto(pg, target)

            if tabs > 1 and parallel:
                self.log.info(f"並行スクロール開始（{tabs}タブ同時）")
                self._scroll_all_parallel(pages)
            else:
                for idx, pg in enumerate(pages):
                    if self.cancel_check():
                        break
                    self.log.status(f"タブ {idx + 1}/{tabs}: スクロール中")
                    self._scroll_to_bottom(pg)
                    self.log.info(f"タブ {idx + 1}/{tabs}: スクロール完了（最下部で停止）")

            # 新規起動時に残っていた最初の空タブを閉じる
            if not reused:
                for ip in initial_pages:
                    try:
                        ip.close()
                    except Exception:
                        pass

            self.log.info(f"全 {tabs} タブのスクロール完了")
            if detach:
                self.log.status("完了（ブラウザは開いたままです。このアプリを閉じても残ります）")
            else:
                self.log.status("完了")
        finally:
            if detach:
                # CDP接続だけ切る。独立プロセスのChromiumは閉じない。
                try:
                    p.stop()
                except Exception:
                    pass
            else:
                try:
                    if browser is not None:
                        browser.close()
                except Exception:
                    pass
                try:
                    p.stop()
                except Exception:
                    pass
                if proc is not None:
                    try:
                        proc.terminate()
                    except Exception:
                        pass

    # ---- 内部処理 ------------------------------------------------------
    @staticmethod
    def _norm(url: str) -> str:
        return (url or "").rstrip("/")

    def _goto(self, page, url: str, retries: int = 3) -> None:
        last = None
        for i in range(retries):
            if self.cancel_check():
                raise LoginError("ユーザーにより中断されました")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                return
            except Exception as e:  # 通信エラー等は最大3回リトライ
                last = e
                self.log.warn(f"ページ遷移リトライ {i + 1}/{retries}: {e}")
                time.sleep(2)
        self.log.error(f"ページ遷移失敗: {url} ({last})")
        raise LoginError(f"ページ遷移失敗: {url}")

    def _needs_login(self, page, site) -> bool:
        sel = site.get("login_required_selector")
        if not sel:
            return False
        try:
            page.wait_for_selector(sel, timeout=8000, state="visible")
            return True
        except Exception:
            return False

    def _login(self, page, site) -> None:
        steps = site.get("login_steps") or []
        if not steps:
            raise LoginError("login_steps が未定義です")
        if not (self.creds.get("LOGIN_ID") and self.creds.get("LOGIN_PASSWORD")):
            raise LoginError("認証情報(.env)が未設定です。設定画面でID/パスワードを保存してください。")

        for step in steps:
            if self.cancel_check():
                raise LoginError("ユーザーにより中断されました")
            self._do_step(page, step)

        # 成功確認（任意）
        succ = site.get("success_selector")
        if succ:
            try:
                page.wait_for_selector(succ, timeout=20000)
            except Exception:
                raise LoginError("ログインに失敗しました。ID／パスワードをご確認ください。")

    def _do_step(self, page, step: Dict) -> None:
        action = step.get("action")
        sel = step.get("selector", "")
        timeout = int(step.get("timeout_ms", 10000))
        loc = page.locator(sel).first if sel else None

        if action == "click":
            loc.click(timeout=timeout)
        elif action == "fill":
            val = self.creds.get(step.get("value_from", ""), "")
            loc.click(timeout=timeout)
            loc.fill(val, timeout=timeout)
        elif action == "wait_for":
            page.wait_for_selector(sel, timeout=int(step.get("timeout_ms", 15000)))
        elif action == "goto":
            self._goto(page, step["url"])
        else:
            self.log.warn(f"未知のステップ action: {action}")
        time.sleep(0.3)

    def _scroll_to_bottom(self, page) -> None:
        s = self.cfg["scroll"]
        step = int(s["step_px"])
        wait = int(s["wait_ms"]) / 1000.0
        settle = int(s["settle_ms"]) / 1000.0
        stable_target = int(s["stable_rounds"])
        max_steps = int(s["max_steps"])

        self.log.info(
            f"スクロール開始 step={step}px wait={int(wait*1000)}ms "
            f"settle={int(settle*1000)}ms stable={stable_target}"
        )
        same = 0
        prev = -1
        for i in range(max_steps):
            if self.cancel_check():
                self.log.warn("スクロール中断")
                return
            page.evaluate(
                "(d) => { const se = document.scrollingElement; se.scrollTop += d; }", step
            )
            time.sleep(wait)
            at_end = page.evaluate(
                "() => { const se = document.scrollingElement;"
                " return se.scrollTop + window.innerHeight >= se.scrollHeight - 2; }"
            )
            if at_end:
                time.sleep(settle)
            height = page.evaluate("() => document.scrollingElement.scrollHeight")
            if height == prev:
                same += 1
                if same >= stable_target:
                    break
            else:
                same = 0
            prev = height

        # 最後に下端へ吸着
        page.evaluate(
            "() => { const se = document.scrollingElement; se.scrollTop = se.scrollHeight; }"
        )

    def _scroll_all_parallel(self, pages) -> None:
        """複数ページを同時並行でスクロール（1スレッド内で各ページを交互に進める）。"""
        s = self.cfg["scroll"]
        step = int(s["step_px"])
        wait = int(s["wait_ms"]) / 1000.0
        settle = int(s["settle_ms"]) / 1000.0
        stable_target = int(s["stable_rounds"])
        max_steps = int(s["max_steps"])
        n = len(pages)

        state = [{"same": 0, "prev": -1, "done": False} for _ in pages]

        def safe_eval(pg, expr, arg=None):
            try:
                return pg.evaluate(expr, arg) if arg is not None else pg.evaluate(expr)
            except Exception:
                return None  # ページが閉じられた等

        for _ in range(max_steps):
            if self.cancel_check():
                self.log.warn("スクロール中断")
                return
            if all(st["done"] for st in state):
                break

            # 1) 各ページを1ステップ下げる
            for pg, st in zip(pages, state):
                if st["done"]:
                    continue
                safe_eval(pg, "(d) => { const se = document.scrollingElement; se.scrollTop += d; }", step)
            time.sleep(wait)

            # 2) いずれかが末端なら遅延読み込み完了を待つ
            ends = []
            for pg, st in zip(pages, state):
                if st["done"]:
                    ends.append(False)
                    continue
                ends.append(bool(safe_eval(
                    pg,
                    "() => { const se = document.scrollingElement;"
                    " return se.scrollTop + window.innerHeight >= se.scrollHeight - 2; }")))
            if any(ends):
                time.sleep(settle)

            # 3) 高さを測り、各ページの完了判定を更新
            for pg, st in zip(pages, state):
                if st["done"]:
                    continue
                h = safe_eval(pg, "() => document.scrollingElement.scrollHeight")
                if h is None:  # ページ消失 → 完了扱い
                    st["done"] = True
                    continue
                if h == st["prev"]:
                    st["same"] += 1
                    if st["same"] >= stable_target:
                        safe_eval(pg, "() => { const se = document.scrollingElement; se.scrollTop = se.scrollHeight; }")
                        st["done"] = True
                else:
                    st["same"] = 0
                st["prev"] = h

            done_cnt = sum(1 for st in state if st["done"])
            self.log.status(f"並行スクロール中 {done_cnt}/{n} 完了")

        # 念のため全ページ下端へ吸着
        for pg in pages:
            safe_eval(pg, "() => { const se = document.scrollingElement; se.scrollTop = se.scrollHeight; }")

