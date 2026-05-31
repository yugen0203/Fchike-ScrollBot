"""価格テキストの解析（純粋関数・テスト可能）。

出品ページの価格欄は「¥3,600〜¥6,900」のような範囲表示。
ここから最高額（max）を取り出す。要件: 必ず最高額で出品する。
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple


def extract_prices(text: str) -> List[int]:
    """文字列中の金額（¥や,を無視した整数）を出現順に返す。"""
    if not text:
        return []
    # 「¥3,600〜¥6,900」「3600円」「3,600 - 6,900」等に対応
    nums = re.findall(r"[¥￥]?\s*([0-9][0-9,]*)\s*(?:円)?", text)
    out: List[int] = []
    for n in nums:
        digits = n.replace(",", "").strip()
        if digits.isdigit():
            out.append(int(digits))
    return out


def parse_price_range(text: str) -> Optional[Tuple[int, int]]:
    """範囲テキストから (min, max) を返す。数値が1つなら (v, v)。無ければ None。"""
    prices = extract_prices(text)
    if not prices:
        return None
    return (min(prices), max(prices))


def max_price(text: str) -> Optional[int]:
    """範囲テキストの最高額を返す。無ければ None。"""
    pr = parse_price_range(text)
    return pr[1] if pr else None
