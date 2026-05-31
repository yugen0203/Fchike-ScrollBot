"""パス解決ユーティリティ。

重要: 配布された .app は macOS の App Translocation により読み取り専用の
ランダムな場所から実行されるため、ユーザーデータ（.env / profiles / logs /
config.yml）は「実行ファイルの隣」ではなく、ユーザーの書き込み可能領域に保存する。

- データ保存先(data_dir):
    開発時 : プロジェクトルート
    配布時 : ~/Library/Application Support/ScrollBot (mac)
             %APPDATA%/ScrollBot (Windows)
             ~/.local/share/ScrollBot (Linux)
- 同梱Chromium(browser_dir): 読み取り専用なので実行ファイルの隣 or _MEIPASS。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "ScrollBot"


def is_frozen() -> bool:
    """PyInstaller でパッケージ化された状態か。"""
    return getattr(sys, "frozen", False)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def exe_dir() -> Path:
    """実行ファイルが置かれたディレクトリ（読み取り専用かもしれない）。"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return _project_root()


def resource_root() -> Path:
    """同梱された読み取り専用リソースの基準（_MEIPASS など）。"""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", exe_dir()))
    return _project_root()


def data_dir() -> Path:
    """ユーザーデータの保存先（書き込み可能）。無ければ作成する。"""
    if not is_frozen():
        return _project_root()  # 開発時はプロジェクト直下

    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---- ユーザーデータ（書き込み可能領域）-------------------------------
def config_path() -> Path:
    return data_dir() / "config.yml"


def env_path() -> Path:
    return data_dir() / ".env"


def profiles_dir() -> Path:
    return data_dir() / "profiles"


def profile_dir(name: str) -> Path:
    return profiles_dir() / name


def logs_dir() -> Path:
    return data_dir() / "logs"


# ---- 同梱リソース（読み取り専用）------------------------------------
def browser_dir() -> Path:
    """同梱Chromium の場所。配布時は実行ファイル隣 → _MEIPASS の順、開発時は build/browser。"""
    if is_frozen():
        for cand in (exe_dir() / "browser", resource_root() / "browser"):
            if cand.exists():
                return cand
        return exe_dir() / "browser"
    return _project_root() / "build" / "browser"


def configure_playwright_browsers_path() -> None:
    """同梱Chromium を使うよう環境変数を設定。Playwright import/起動より前に呼ぶこと。"""
    bdir = browser_dir()
    if bdir.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bdir)
