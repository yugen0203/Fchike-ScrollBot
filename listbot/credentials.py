"""認証情報（.env.listbot）の読み書き（ListBot 用）。要件により平文保存。

ScrollBot とは別ファイルに保存する（アプリが独立しているため）。
将来の暗号化対応はここを差し替えるだけで済むよう、読み書きを集約する。
"""
from __future__ import annotations

from typing import Dict

from dotenv import dotenv_values

from . import paths

_KEY_ID = "LOGIN_ID"
_KEY_PW = "LOGIN_PASSWORD"


def load_credentials() -> Dict[str, str]:
    """.env.listbot から認証情報を読む。無ければ空文字。"""
    p = paths.env_path()
    if not p.exists():
        return {_KEY_ID: "", _KEY_PW: ""}
    vals = dotenv_values(p)
    return {
        _KEY_ID: vals.get(_KEY_ID, "") or "",
        _KEY_PW: vals.get(_KEY_PW, "") or "",
    }


def has_credentials() -> bool:
    c = load_credentials()
    return bool(c.get(_KEY_ID) and c.get(_KEY_PW))


def save_credentials(login_id: str, password: str) -> None:
    """.env.listbot を生成/更新（平文）。"""
    p = paths.env_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ListBot 認証情報（自動生成）。手動編集も可。",
        f"{_KEY_ID}={login_id}",
        f"{_KEY_PW}={password}",
        "",
    ]
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
