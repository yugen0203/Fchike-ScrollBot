"""出品Bot（ListBot）GUI。

セットアップ:
  - 出品する試合の日付範囲（例 9/17〜9/20）
  - 連番グルーピングのルール（まとめる / 最大席数で分割 / 端数の扱い）
  - 並行タブ数
  - 確認モード（最終「出品する」直前で停止）
  - ログインID/パスワード（設定）

Playwright 実行はワーカースレッドで行い、queue でステータスを受け取り描画する。
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from . import credentials, paths
from .config_loader import ConfigError, load_config
from .core import LoginError
from .logger import Logger
from .runner import ListingRunner, parse_date_range


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("出品Bot（ListBot）")
        self.root.geometry("640x560")
        self.root.minsize(640, 560)

        self._status_q: "queue.Queue" = queue.Queue()
        self._worker: threading.Thread | None = None
        self._cancel = False

        self._build_main()
        self.root.after(100, self._poll_status)

        if not credentials.has_credentials():
            self.root.after(300, self.open_settings)

    # ---- メイン画面 ----------------------------------------------------
    def _build_main(self) -> None:
        frm = ttk.Frame(self.root, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="出品Bot", font=("", 18, "bold")).pack(pady=(0, 2))
        ttk.Label(frm, text="シーズンシートを最高額で自動出品します").pack(pady=(0, 4))
        warn = ttk.Label(frm, text="⚠️ 既定はフル自動（実際に出品が確定）。テストは『確認モード』をON",
                         foreground="#b02a37")
        warn.pack(pady=(0, 10))

        # 日付範囲
        daterow = ttk.LabelFrame(frm, text="出品する試合の日付", padding=8)
        daterow.pack(fill="x", pady=(0, 8))
        ttk.Label(daterow, text="開始 (例 9/17):").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.from_var = tk.StringVar(value="")
        ttk.Entry(daterow, textvariable=self.from_var, width=12).grid(row=0, column=1, padx=(0, 12))
        ttk.Label(daterow, text="終了 (例 9/20):").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.to_var = tk.StringVar(value="")
        ttk.Entry(daterow, textvariable=self.to_var, width=12).grid(row=0, column=3)
        ttk.Label(daterow, text="※同じ日付なら開始＝終了でOK（1試合のみ）",
                  foreground="#666").grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # 連番ルール
        grp = ttk.LabelFrame(frm, text="連番（連続席）の出品ルール", padding=8)
        grp.pack(fill="x", pady=(0, 8))
        self.mode_var = tk.StringVar(value="together")
        ttk.Radiobutton(grp, text="連続席はまとめて連番出品（例 5,6,7,8→4連番）",
                        variable=self.mode_var, value="together",
                        command=self._sync_mode_state).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Radiobutton(grp, text="最大席数で分割する",
                        variable=self.mode_var, value="max_size",
                        command=self._sync_mode_state).grid(row=1, column=0, columnspan=4, sticky="w")
        ttk.Label(grp, text="　最大席数:").grid(row=2, column=0, sticky="w", padx=(16, 0))
        self.maxsize_var = tk.IntVar(value=2)
        self.maxsize_spin = ttk.Spinbox(grp, from_=1, to=8, width=4, textvariable=self.maxsize_var,
                                        state="disabled")
        self.maxsize_spin.grid(row=2, column=1, sticky="w")
        ttk.Label(grp, text="端数:").grid(row=2, column=2, sticky="e")
        self.remainder_var = tk.StringVar(value="single")
        self.remainder_combo = ttk.Combobox(grp, textvariable=self.remainder_var, width=20,
                                            state="disabled",
                                            values=["single（端数は単独出品）",
                                                    "merge（端数は直前に足し3連番化）"])
        self.remainder_combo.grid(row=2, column=3, sticky="w")
        self.remainder_combo.set("single（端数は単独出品）")

        # 並行
        par = ttk.LabelFrame(frm, text="並行処理", padding=8)
        par.pack(fill="x", pady=(0, 8))
        self.parallel_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(par, text="複数日付を複数タブで同時出品（ログイン共有）",
                        variable=self.parallel_var).grid(row=0, column=0, sticky="w")
        ttk.Label(par, text="最大タブ数:").grid(row=0, column=1, padx=(12, 4))
        self.tabs_var = tk.IntVar(value=5)
        ttk.Spinbox(par, from_=1, to=10, width=4, textvariable=self.tabs_var,
                    state="readonly").grid(row=0, column=2)

        # 実行モード
        self.confirm_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="確認モード：最終「出品する」ボタンの直前で停止する（人が最終確認）",
                        variable=self.confirm_var).pack(anchor="w", pady=(0, 8))

        # ボタン
        btns = ttk.Frame(frm)
        btns.pack(pady=4)
        self.run_btn = ttk.Button(btns, text="出品開始", width=12, command=self.on_run)
        self.run_btn.grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="設定", width=10, command=self.open_settings).grid(row=0, column=1, padx=4)
        ttk.Button(btns, text="ログ確認", width=10, command=self.open_logs).grid(row=0, column=2, padx=4)
        self.logout_btn = ttk.Button(btns, text="ログアウト", width=10, command=self.on_logout)
        self.logout_btn.grid(row=0, column=3, padx=4)

        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(frm, textvariable=self.status_var, foreground="#0a58ca",
                  font=("", 12), anchor="center").pack(fill="x", pady=(14, 0))
        self.pb = ttk.Progressbar(frm, mode="indeterminate")
        self.pb.pack(fill="x", pady=(8, 0))

    def _sync_mode_state(self):
        on = self.mode_var.get() == "max_size"
        self.maxsize_spin.config(state="readonly" if on else "disabled")
        self.remainder_combo.config(state="readonly" if on else "disabled")

    # ---- 実行 ----------------------------------------------------------
    def on_run(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        if not credentials.has_credentials():
            messagebox.showwarning("設定が必要", "先に[設定]でログインID/パスワードを保存してください。")
            self.open_settings()
            return
        df, dt = self.from_var.get().strip(), self.to_var.get().strip()
        if not df or not dt:
            messagebox.showwarning("入力不足", "出品する試合の日付（開始・終了）を入力してください。")
            return
        try:
            preview = parse_date_range(df, dt)
        except Exception as e:
            messagebox.showerror("日付エラー", f"日付の形式を確認してください。\n{e}")
            return

        confirm = self.confirm_var.get()
        mode_label = "確認モード（最終出品ボタン直前で停止）" if confirm else "フル自動（最終出品まで実行）"
        if not messagebox.askyesno(
            "出品の確認",
            f"対象日付: {df}〜{dt}（{len(preview)}日分）\n"
            f"実行モード: {mode_label}\n\n"
            + ("" if confirm else "⚠️ フル自動です。実際に出品が確定します。\n")
            + "実行してよろしいですか？",
        ):
            return

        self._cancel = False
        self._df, self._dt = df, dt
        self._grouping = self._collect_grouping()
        self._parallel = bool(self.parallel_var.get())
        self._max_tabs = int(self.tabs_var.get())
        self._confirm = confirm

        self.run_btn.config(state="disabled")
        self.pb.start(12)
        self._set_status(f"開始しています（{df}〜{dt}）")
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()

    def _collect_grouping(self) -> dict:
        rem = "merge" if self.remainder_var.get().startswith("merge") else "single"
        return {
            "mode": self.mode_var.get(),
            "max_group_size": int(self.maxsize_var.get()),
            "remainder": rem,
            "single_as_bara_ok": True,
        }

    def _run_worker(self) -> None:
        log = Logger(status_cb=lambda m: self._status_q.put(("status", m)))
        try:
            log.info("=== 出品Bot 起動 ===")
            cfg = load_config()
            cfg["parallel"] = self._parallel
            cfg["max_parallel_tabs"] = self._max_tabs
            cfg["grouping"] = {**cfg.get("grouping", {}), **self._grouping}
            cfg["listing"] = {**cfg.get("listing", {}), "confirm_mode": self._confirm}
            creds = credentials.load_credentials()
            runner = ListingRunner(cfg, creds, log, cancel_check=lambda: self._cancel)
            summary = runner.run(self._df, self._dt)
            self._status_q.put(("done", summary))
        except ConfigError as e:
            log.error(f"設定エラー: {e}")
            self._status_q.put(("error", f"設定エラー: {e}"))
        except LoginError as e:
            log.error(f"ログイン/実行エラー: {e}")
            self._status_q.put(("error", str(e)))
        except Exception as e:
            log.error(f"予期しないエラー: {e!r}")
            self._status_q.put(("error", f"予期しないエラー: {e}"))

    # ---- ステータス受信 ------------------------------------------------
    def _poll_status(self) -> None:
        try:
            while True:
                kind, payload = self._status_q.get_nowait()
                if kind == "status":
                    self._set_status(payload)
                elif kind == "done":
                    self._finish()
                    s = payload
                    if s.get("stopped_for_confirm"):
                        self._set_status("確認モードで停止（画面で最終確認してください）")
                        messagebox.showinfo(
                            "確認モード",
                            "最終「出品する」ボタンの直前で停止しました。\n"
                            "ブラウザ画面で内容を確認し、問題なければ手動で「出品する」を押してください。")
                    else:
                        self._set_status(
                            f"完了: {s.get('listed_groups', 0)} グループ出品 / "
                            f"スキップ {len(s.get('skipped', []))} / エラー {len(s.get('errors', []))}")
                        messagebox.showinfo(
                            "完了",
                            f"出品: {s.get('listed_groups', 0)} グループ\n"
                            f"スキップ: {s.get('skipped', [])}\n"
                            f"エラー: {len(s.get('errors', []))} 件（詳細はログ確認）")
                elif kind == "error":
                    self._finish()
                    self.logout_btn.config(state="normal")
                    self._set_status("エラー")
                    messagebox.showerror("エラー", payload)
                elif kind == "logout_done":
                    self.pb.stop()
                    self.logout_btn.config(state="normal")
                    self._set_status(payload)
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
            "ブラウザを閉じてログイン情報を消去します。\n次回[出品開始]時はログインからやり直します。\nよろしいですか？",
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
            messagebox.showinfo("保存しました", f"保存先:\n{paths.env_path()}", parent=win)
            win.destroy()

        ttk.Button(btns, text="保存", command=do_save).pack(side="left")
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
