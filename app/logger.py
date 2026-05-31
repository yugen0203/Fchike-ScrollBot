"""ログ出力。logs/YYYY-MM-DD.log に時刻付きで追記する。"""
from __future__ import annotations

import datetime as _dt

from . import paths


class Logger:
    def __init__(self, status_cb=None):
        # status_cb: GUI へステータス文字列を渡すコールバック（任意）
        self._status_cb = status_cb
        self._dir = paths.logs_dir()
        self._dir.mkdir(parents=True, exist_ok=True)

    def _logfile(self):
        name = _dt.date.today().strftime("%Y-%m-%d") + ".log"
        return self._dir / name

    def _write(self, level: str, msg: str) -> None:
        ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {level:<5} {msg}\n"
        try:
            with open(self._logfile(), "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            # ログ書き込み失敗でアプリを止めない
            pass
        # コンソールにも出す（開発時）
        print(line, end="")

    def info(self, msg: str) -> None:
        self._write("INFO", msg)

    def warn(self, msg: str) -> None:
        self._write("WARN", msg)

    def error(self, msg: str) -> None:
        self._write("ERROR", msg)

    def status(self, msg: str) -> None:
        """ステータス更新（ログにも残しGUIにも通知）。"""
        self._write("INFO", f"STATUS: {msg}")
        if self._status_cb:
            try:
                self._status_cb(msg)
            except Exception:
                pass
