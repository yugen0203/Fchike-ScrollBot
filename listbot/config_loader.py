"""config_listbot.yml の読み込みと最小限のスキーマ検証（ListBot 用）。

ScrollBot の config_loader と同方針。出品フロー・連番ルール・価格ルール・
並行設定を追加で保持する。サイト固有値はすべてここに集約しコードにハードコードしない。
"""
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
_DEFAULT_GROUPING = {
    "mode": "together",
    "max_group_size": 2,
    "remainder": "single",
    "partition_overrides": {},
    "single_as_bara_ok": True,
}
_DEFAULT_LISTING = {
    "price_strategy": "max",      # 価格戦略（max=最高額。要件固定だが将来拡張用に明示）
    "confirm_mode": False,         # True=最終「出品する」直前で停止（既定はフル自動）
    "between_actions_ms": 400,     # 各操作間の待機（ms）
}


class ConfigError(Exception):
    pass


def _ensure_user_config() -> None:
    """配布時: 実行ファイル隣に config_listbot.yml が無ければ、同梱の既定をコピーする。"""
    user = paths.config_path()
    if user.exists():
        return
    bundled = paths.resource_root() / paths.CONFIG_NAME
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
        raise ConfigError(f"{paths.CONFIG_NAME} が見つかりません: {p}")
    with open(p, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # 既定値で補完
    cfg.setdefault("profile", "account_001")
    cfg.setdefault("parallel", True)
    cfg.setdefault("max_parallel_tabs", 5)
    cfg.setdefault("keep_open", True)
    cfg.setdefault("debug_port", 9344)  # ScrollBot(9333)と別ポート
    browser = {**_DEFAULT_BROWSER, **(cfg.get("browser") or {})}
    browser["viewport"] = {**_DEFAULT_BROWSER["viewport"], **(browser.get("viewport") or {})}
    cfg["browser"] = browser
    cfg["scroll"] = {**_DEFAULT_SCROLL, **(cfg.get("scroll") or {})}
    cfg["grouping"] = {**_DEFAULT_GROUPING, **(cfg.get("grouping") or {})}
    cfg["listing"] = {**_DEFAULT_LISTING, **(cfg.get("listing") or {})}

    # 必須項目の検証
    sites = cfg.get("sites") or {}
    if not sites:
        raise ConfigError(f"{paths.CONFIG_NAME} に sites が定義されていません")
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
    site.setdefault("listing", {})  # 出品フローのセレクタ群（live capture で確定）

    return cfg


def active_site(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg["sites"][cfg["active_site"]]
