"""config.yml の読み込みと最小限のスキーマ検証。"""
from __future__ import annotations

from typing import Any, Dict

import yaml

from . import paths

_DEFAULT_SCROLL = {
    "step_px": 600,
    "wait_ms": 800,
    "settle_ms": 1200,
    "stable_rounds": 6,
    "max_steps": 200,
}
_DEFAULT_BROWSER = {
    "headless": False,
    "viewport": {"width": 1280, "height": 720},
    "user_agent": "",
}


class ConfigError(Exception):
    pass


def _ensure_user_config() -> None:
    """配布時: 実行ファイル隣に config.yml が無ければ、同梱の既定をコピーする。"""
    user = paths.config_path()
    if user.exists():
        return
    bundled = paths.resource_root() / "config.yml"
    if bundled.exists() and bundled.resolve() != user.resolve():
        try:
            user.parent.mkdir(parents=True, exist_ok=True)
            user.write_text(bundled.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass


def load_config() -> Dict[str, Any]:
    _ensure_user_config()
    p = paths.config_path()
    if not p.exists():
        raise ConfigError(f"config.yml が見つかりません: {p}")
    with open(p, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # 既定値で補完
    cfg.setdefault("profile", "account_001")
    cfg.setdefault("tabs", 1)
    cfg.setdefault("parallel", True)
    cfg.setdefault("keep_open", True)
    cfg.setdefault("debug_port", 9333)
    browser = {**_DEFAULT_BROWSER, **(cfg.get("browser") or {})}
    browser["viewport"] = {**_DEFAULT_BROWSER["viewport"], **(browser.get("viewport") or {})}
    cfg["browser"] = browser
    cfg["scroll"] = {**_DEFAULT_SCROLL, **(cfg.get("scroll") or {})}

    # 必須項目の検証
    sites = cfg.get("sites") or {}
    if not sites:
        raise ConfigError("config.yml に sites が定義されていません")
    active = cfg.get("active_site")
    if active not in sites:
        raise ConfigError(f"active_site '{active}' が sites に存在しません")

    site = sites[active]
    for key in ("start_url",):
        if not site.get(key):
            raise ConfigError(f"サイト定義 '{active}' に必須項目 '{key}' がありません")
    site.setdefault("target_url", site["start_url"])
    site.setdefault("login_required_selector", "")
    site.setdefault("login_steps", [])
    site.setdefault("success_selector", "")

    return cfg


def active_site(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg["sites"][cfg["active_site"]]
