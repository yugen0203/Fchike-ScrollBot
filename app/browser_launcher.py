"""同梱Chromium を独立プロセスとして起動し、CDP(リモートデバッグ)で接続するための補助。

ポイント:
- ScrollBot本体(アプリ)とは別プロセスとしてChromiumを起動(start_new_session/DETACHED)。
  → アプリを閉じてもブラウザは開いたまま。
- 永続プロファイル(--user-data-dir)を使うのでログイン状態がディスクに保存される。
- 既に起動済み(同じポートが応答)なら、それに再接続して新規タブを開く。
- ログアウトは保存したPIDでブラウザを終了し、プロファイルを削除する。
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
import urllib.request

from . import paths

PID_FILE = "chrome.pid"


def chrome_profile_dir():
    return paths.data_dir() / "chrome_profile"


def _pid_path():
    return paths.data_dir() / PID_FILE


def port_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def wait_port(port: int, timeout: float = 30.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if port_alive(port):
            return True
        time.sleep(0.3)
    return False


def launch_detached(executable: str, port: int, headless: bool,
                    width: int, height: int) -> subprocess.Popen:
    udir = chrome_profile_dir()
    udir.mkdir(parents=True, exist_ok=True)
    args = [
        executable,
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={udir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate",
        f"--window-size={width},{height}",
    ]
    if headless:
        args.append("--headless=new")

    kwargs = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    if os.name == "nt":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(args, **kwargs)
    try:
        _pid_path().write_text(str(proc.pid), encoding="utf-8")
    except Exception:
        pass
    return proc


def _read_pid():
    try:
        return int(_pid_path().read_text(encoding="utf-8").strip())
    except Exception:
        return None


def kill_running_browser() -> None:
    """保存済みPIDのブラウザを終了する(あれば)。"""
    pid = _read_pid()
    if not pid:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
        time.sleep(1.0)
    except Exception:
        pass
    try:
        _pid_path().unlink()
    except Exception:
        pass


def clear_session() -> None:
    """ログアウト: ブラウザを終了し、プロファイル(ログイン情報)と旧storage_stateを削除。"""
    kill_running_browser()
    # 念のため少し待つ(ファイルロック解放)
    time.sleep(0.5)
    for target in (chrome_profile_dir(),):
        try:
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
        except Exception:
            pass
    # 旧方式の storage_state も掃除
    try:
        prof = paths.profiles_dir()
        if prof.exists():
            for ss in prof.glob("*/storage_state.json"):
                try:
                    ss.unlink()
                except Exception:
                    pass
    except Exception:
        pass
