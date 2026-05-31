"""Tkinter GUI。実行 / 設定 / ログ確認 ボタンとステータス表示。

Playwright 実行はワーカースレッドで行い、queue 経由でステータスを受け取って
メインスレッド(GUI)で描画する（実行中もフリーズしない）。
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from . import credentials, paths
from .config_loader import ConfigError, load_config
from .core import LoginError, ScrollBot
from .logger import Logger


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ScrollBot")
        self.root.geometry("560x320")
        self.root.minsize(560, 320)

        self._status_q: "queue.Queue[str]" = queue.Queue()
        self._worker: threading.Thread | None = None
        self._cancel = False

        self._build_main()
        self.root.after(100, self._poll_status)

        # 初回起動（認証情報なし）は設定画面へ誘導
        if not credentials.has_credentials():
            self.root.after(300, self.open_settings)

    # ---- メイン画面 ----------------------------------------------------
    def _build_main(self) -> None:
        frm = ttk.Frame(self.root, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="ScrollBot", font=("", 18, "bold")).pack(pady=(0, 4))
        ttk.Label(frm, text="最下部まで自動スクロールします").pack(pady=(0, 12))

        # タブ数の選択（実行時に開くタブ数）
        tabrow = ttk.Frame(frm)
        tabrow.pack(pady=(0, 6))
        ttk.Label(tabrow, text="開くタブ数:").grid(row=0, column=0, padx=(0, 6))
        self.tabs_var = tk.IntVar(value=1)
        self.tabs_spin = ttk.Spinbox(
            tabrow, from_=1, to=20, width=5, textvariable=self.tabs_var, state="readonly"
        )
        self.tabs_spin.grid(row=0, column=1)
        ttk.Label(tabrow, text="（1〜20）").grid(row=0, column=2, padx=(6, 0))

        self.parallel_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="タブを同時並行でスクロール", variable=self.parallel_var).pack()

        btns = ttk.Frame(frm)
        btns.pack(pady=4)
        self.run_btn = ttk.Button(btns, text="実行", width=11, command=self.on_run)
        self.run_btn.grid(row=0, column=0, padx=4, pady=2)
        ttk.Button(btns, text="設定", width=11, command=self.open_settings).grid(row=0, column=1, padx=4, pady=2)
        ttk.Button(btns, text="ログ確認", width=11, command=self.open_logs).grid(row=0, column=2, padx=4, pady=2)
        self.logout_btn = ttk.Button(btns, text="ログアウト", width=11, command=self.on_logout)
        self.logout_btn.grid(row=0, column=3, padx=4, pady=2)

        self.status_var = tk.StringVar(value="待機中")
        status = ttk.Label(frm, textvariable=self.status_var, foreground="#0a58ca",
                           font=("", 12), anchor="center")
        status.pack(fill="x", pady=(18, 0))

        self.pb = ttk.Progressbar(frm, mode="indeterminate")
        self.pb.pack(fill="x", pady=(8, 0))

    # ---- 実行 ----------------------------------------------------------
    def on_run(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        if not credentials.has_credentials():
            messagebox.showwarning("設定が必要", "先に[設定]でログインID/パスワードを保存してください。")
            self.open_settings()
            return
        self._cancel = False
        # Tk変数はメインスレッドで読み、ワーカーへ値で渡す
        try:
            self._tabs = max(1, int(self.tabs_var.get()))
        except Exception:
            self._tabs = 1
        self._parallel = bool(self.parallel_var.get())
        self.run_btn.config(state="disabled")
        self.pb.start(12)
        self._set_status(f"開始しています（{self._tabs}タブ）")
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()

    def _run_worker(self) -> None:
        log = Logger(status_cb=lambda m: self._status_q.put(("status", m)))
        try:
            log.info("=== ScrollBot 起動 ===")
            cfg = load_config()
            cfg["tabs"] = getattr(self, "_tabs", 1)  # GUIで選んだタブ数で上書き
            cfg["parallel"] = getattr(self, "_parallel", True)  # 並行/順次
            creds = credentials.load_credentials()
            bot = ScrollBot(cfg, creds, log, cancel_check=lambda: self._cancel)
            bot.run()
            self._status_q.put(("done", "完了しました"))
        except ConfigError as e:
            log.error(f"設定エラー: {e}")
            self._status_q.put(("error", f"設定エラー: {e}"))
        except LoginError as e:
            log.error(f"ログイン/実行エラー: {e}")
            self._status_q.put(("error", str(e)))
        except Exception as e:  # 予期しない例外
            log.error(f"予期しないエラー: {e!r}")
            self._status_q.put(("error", f"予期しないエラー: {e}"))

    # ---- ステータス受信（メインスレッド）------------------------------
    def _poll_status(self) -> None:
        try:
            while True:
                kind, msg = self._status_q.get_nowait()
                if kind == "status":
                    self._set_status(msg)
                elif kind == "done":
                    self._finish()
                    self._set_status("完了")
                elif kind == "error":
                    self._finish()
                    self.logout_btn.config(state="normal")
                    self._set_status("エラー")
                    messagebox.showerror("エラー", msg)
                elif kind == "logout_done":
                    self.pb.stop()
                    self.logout_btn.config(state="normal")
                    self._set_status(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_status)

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    def _finish(self) -> None:
        self.pb.stop()
        self.run_btn.config(state="normal")

    # ---- ログアウト ----------------------------------------------------
    def on_logout(self) -> None:
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("実行中", "処理の完了後にログアウトしてください。")
            return
        if not messagebox.askyesno(
            "ログアウト",
            "ブラウザを閉じてログイン情報を消去します。\n次回[実行]時はログインからやり直します。\nよろしいですか？",
        ):
            return
        self.logout_btn.config(state="disabled")
        self._set_status("ログアウト中")
        self.pb.start(12)

        def worker():
            try:
                from . import browser_launcher
                browser_launcher.clear_session()
                self._status_q.put(("logout_done", "ログアウトしました（次回実行時にログイン）"))
            except Exception as e:
                self._status_q.put(("error", f"ログアウト失敗: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    # ---- 設定画面 ------------------------------------------------------
    def open_settings(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("設定")
        win.geometry("460x250")
        win.minsize(460, 250)
        win.transient(self.root)
        win.grab_set()

        cur = credentials.load_credentials()
        frm = ttk.Frame(win, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="ログインID（お客様コード）").pack(anchor="w")
        id_var = tk.StringVar(value=cur.get("LOGIN_ID", ""))
        ttk.Entry(frm, textvariable=id_var, width=40).pack(fill="x", pady=(0, 8))

        ttk.Label(frm, text="パスワード").pack(anchor="w")
        pw_var = tk.StringVar(value=cur.get("LOGIN_PASSWORD", ""))
        pw_entry = ttk.Entry(frm, textvariable=pw_var, width=40, show="*")
        pw_entry.pack(fill="x", pady=(0, 4))

        show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frm, text="パスワードを表示", variable=show_var,
            command=lambda: pw_entry.config(show="" if show_var.get() else "*"),
        ).pack(anchor="w", pady=(0, 10))

        btns = ttk.Frame(frm)
        btns.pack(fill="x")

        def do_save():
            if not id_var.get().strip() or not pw_var.get():
                messagebox.showwarning("入力不足", "IDとパスワードを入力してください。", parent=win)
                return
            try:
                credentials.save_credentials(id_var.get().strip(), pw_var.get())
            except Exception as e:
                messagebox.showerror("保存エラー", f"保存に失敗しました:\n{e}", parent=win)
                return
            if not credentials.has_credentials():
                messagebox.showerror(
                    "保存エラー",
                    f"保存後に読み込めませんでした。保存先:\n{paths.env_path()}",
                    parent=win,
                )
                return
            messagebox.showinfo("保存しました", f"保存先:\n{paths.env_path()}", parent=win)
            win.destroy()

        ttk.Button(btns, text="保存", command=do_save).pack(side="left")
        ttk.Button(btns, text="テストログイン", command=self.on_run).pack(side="left", padx=8)
        ttk.Button(btns, text="閉じる", command=win.destroy).pack(side="right")

    # ---- ログ確認 ------------------------------------------------------
    def open_logs(self) -> None:
        import datetime as _dt

        logf = paths.logs_dir() / (_dt.date.today().strftime("%Y-%m-%d") + ".log")
        win = tk.Toplevel(self.root)
        win.title(f"ログ: {logf.name}")
        win.geometry("640x420")
        txt = scrolledtext.ScrolledText(win, wrap="word", font=("Menlo", 11))
        txt.pack(fill="both", expand=True)
        try:
            content = logf.read_text(encoding="utf-8") if logf.exists() else "（ログはまだありません）"
        except Exception as e:
            content = f"ログ読み込みエラー: {e}"
        txt.insert("1.0", content)
        txt.config(state="disabled")
        txt.see("end")


def launch() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
