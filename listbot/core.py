"""ブラウザセッション基盤（ListBot 用）。

ScrollBot の core.py からログイン・スクロール・遷移を流用。
ブラウザの起動/接続・ログイン・目的ページ遷移・汎用スクロールを提供し、
出品フロー本体（listing.py）から利用する。

サイト固有値（URL/セレクタ/スクロール量）は config から受け取り、
このコードにハードコードしない。
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List

from . import paths
from .config_loader import active_site
from .logger import Logger


class LoginError(Exception):
    pass


class Session:
    """Playwright(同期API) のブラウザセッション。

    使い方:
        sess = Session(cfg, creds, log, cancel_check)
        ctx = sess.open()           # ブラウザ起動/接続 → context を返す
        page = ctx.new_page()
        sess.ensure_login(page)     # 未ログインなら自動ログイン
        sess.scroll_to_bottom(page) # 最下部まで（遅延読込対応）
        ...
        sess.close()                # detach なら接続だけ切る（ブラウザは残す）
    """

    def __init__(self, cfg: Dict, creds: Dict[str, str], log: Logger,
                 cancel_check: Callable[[], bool] | None = None):
        self.cfg = cfg
        self.creds = creds
        self.log = log
        self.cancel_check = cancel_check or (lambda: False)
        self._p = None
        self._proc = None
        self._browser = None
        self._context = None
        self._reused = False
        self._detach = False
        self.initial_pages: List = []

    # ---- セッション管理 -------------------------------------------------
    def open(self):
        paths.configure_playwright_browsers_path()
        from playwright.sync_api import sync_playwright
        from . import browser_launcher as bl

        b = self.cfg["browser"]
        headless = bool(b.get("headless", False))
        self._detach = (not headless) and bool(self.cfg.get("keep_open", True))
        port = int(self.cfg.get("debug_port", 9344))
        width = int(b["viewport"]["width"])
        height = int(b["viewport"]["height"])

        try:
            self._p = sync_playwright().start()
        except Exception as e:
            raise LoginError(paths.diagnose_playwright(e))
        exe = self._p.chromium.executable_path

        self._reused = bl.port_alive(port)
        if self._reused:
            self.log.info("既存ブラウザに接続")
        else:
            self.log.status("ブラウザを起動中")
            self._proc = bl.launch_detached(exe, port, headless, width, height)
            if not bl.wait_port(port, 30):
                raise LoginError("ブラウザの起動に失敗しました")

        self._browser = self._p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        self._context = (self._browser.contexts[0]
                         if self._browser.contexts else self._browser.new_context())
        self.initial_pages = list(self._context.pages)
        return self._context

    def close(self):
        if self._detach:
            try:
                self._p.stop()
            except Exception:
                pass
        else:
            try:
                if self._browser is not None:
                    self._browser.close()
            except Exception:
                pass
            try:
                self._p.stop()
            except Exception:
                pass
            if self._proc is not None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass

    def close_initial_blank_tabs(self):
        """新規起動時に残っていた最初の空タブを閉じる。"""
        if self._reused:
            return
        for ip in self.initial_pages:
            try:
                ip.close()
            except Exception:
                pass

    @property
    def context(self):
        return self._context

    @property
    def detach(self) -> bool:
        return self._detach

    # ---- ナビゲーション -------------------------------------------------
    @staticmethod
    def _norm(url: str) -> str:
        return (url or "").rstrip("/")

    def goto(self, page, url: str, retries: int = 3) -> None:
        last = None
        for i in range(retries):
            if self.cancel_check():
                raise LoginError("ユーザーにより中断されました")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                return
            except Exception as e:
                last = e
                self.log.warn(f"ページ遷移リトライ {i + 1}/{retries}: {e}")
                time.sleep(2)
        self.log.error(f"ページ遷移失敗: {url} ({last})")
        raise LoginError(f"ページ遷移失敗: {url}")

    # ---- ログイン -------------------------------------------------------
    def needs_login(self, page) -> bool:
        site = active_site(self.cfg)
        sel = site.get("login_required_selector")
        if not sel:
            return False
        try:
            page.wait_for_selector(sel, timeout=8000, state="visible")
            return True
        except Exception:
            return False

    def ensure_login(self, page) -> None:
        site = active_site(self.cfg)
        self.goto(page, site["start_url"])
        if self.needs_login(page):
            self.log.status("ログイン中")
            self._login(page, site)
            self.log.info("ログイン成功（プロファイルに保存）")
        else:
            self.log.info("ログイン済み（セッション再利用）")

    def _login(self, page, site) -> None:
        steps = site.get("login_steps") or []
        if not steps:
            raise LoginError("login_steps が未定義です")
        if not (self.creds.get("LOGIN_ID") and self.creds.get("LOGIN_PASSWORD")):
            raise LoginError("認証情報(.env.listbot)が未設定です。設定画面でID/パスワードを保存してください。")

        for step in steps:
            if self.cancel_check():
                raise LoginError("ユーザーにより中断されました")
            self._do_step(page, step)

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
            self.goto(page, step["url"])
        else:
            self.log.warn(f"未知のステップ action: {action}")
        time.sleep(0.3)

    # ---- スクロール（最下部まで・遅延読込対応）-------------------------
    def scroll_to_bottom(self, page) -> None:
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
        for _ in range(max_steps):
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

        page.evaluate(
            "() => { const se = document.scrollingElement; se.scrollTop = se.scrollHeight; }"
        )
