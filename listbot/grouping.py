"""連番（連続席）のグルーピング・ロジック（純粋関数・設定可能）。

ブラウザ操作とは独立した純粋ロジックなので単体テスト可能。

座席は最低限 section（Sec）/ row（列）/ num（席番号:int）を持つ dict として扱う。
同じ section かつ同じ row で、num が連続していれば「連番」とみなす。

グルーピング設定（rule, config_listbot.yml の grouping: 配下）:
  mode: "together" | "max_size"
    - together  : 連続Nをそのまま1グループ（既定。例 5,6→[2] / 5,6,7,8→[4]）
    - max_size  : max_group_size 席で分割（例 max=2 なら 4→2+2 / 5→2+2+1 or 2+3）
  max_group_size: int           # max_size モードのグループ最大席数（既定2）
  remainder: "single" | "merge" # 端数の扱い（max_size モード時）
    - single : 余りはそのまま小グループ（1席なら単独出品）
    - merge  : 余りを直前グループに足す（例 3→[3], 5→[2,3]）
  partition_overrides: { N: [sizes...] }  # 連番数Nごとの明示指定（任意・最優先）
  single_as_bara_ok: bool       # 1席グループを「バラ売り可」で出品するか（既定True）

戻り値: グループのリスト。各グループは座席 dict のリスト。
出品方法（バラ売り可/不可）は decide_bara_ok() で判定する。
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

DEFAULT_RULE: Dict[str, Any] = {
    "mode": "together",
    "max_group_size": 2,
    "remainder": "single",
    "partition_overrides": {},
    "single_as_bara_ok": True,
}


def _seat_key(seat: Dict[str, Any]):
    """連番判定のためのソートキー（section, row, num）。"""
    return (str(seat.get("section", "")), str(seat.get("row", "")), int(seat.get("num", 0)))


def find_consecutive_runs(seats: Sequence[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """同 section・同 row で num が連続する座席を「連番ラン」にまとめる。

    非連続な席は長さ1のランになる。
    """
    if not seats:
        return []
    ordered = sorted(seats, key=_seat_key)
    runs: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = [ordered[0]]
    for prev, s in zip(ordered, ordered[1:]):
        same_block = (str(prev.get("section", "")) == str(s.get("section", ""))
                      and str(prev.get("row", "")) == str(s.get("row", "")))
        consecutive = int(s.get("num", 0)) == int(prev.get("num", 0)) + 1
        if same_block and consecutive:
            cur.append(s)
        else:
            runs.append(cur)
            cur = [s]
    runs.append(cur)
    return runs


def partition_sizes(n: int, rule: Dict[str, Any]) -> List[int]:
    """連番数 n を、ルールに従ってグループサイズの列に分割する。

    返すサイズの合計は必ず n になる。
    """
    if n <= 0:
        return []
    overrides = rule.get("partition_overrides") or {}
    # キーは int でも str でも受ける
    for key in (n, str(n)):
        if key in overrides:
            sizes = [int(x) for x in overrides[key]]
            if sum(sizes) == n and all(x > 0 for x in sizes):
                return sizes
            # 不正な override は無視してデフォルトへフォールバック
            break

    mode = rule.get("mode", "together")
    if mode == "together" or n == 1:
        return [n]

    if mode == "max_size":
        size = max(1, int(rule.get("max_group_size", 2)))
        if n <= size:
            return [n]
        full = n // size
        rem = n % size
        sizes = [size] * full
        if rem:
            if rule.get("remainder", "single") == "merge" and sizes:
                sizes[-1] += rem  # 端数を直前グループに足す（例 5,max2→[2,3]）
            else:
                sizes.append(rem)  # 端数はそのまま小グループ（1席なら単独）
        return sizes

    # 未知モードは together 扱い
    return [n]


def _split_run(run: List[Dict[str, Any]], rule: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
    sizes = partition_sizes(len(run), rule)
    groups: List[List[Dict[str, Any]]] = []
    i = 0
    for sz in sizes:
        groups.append(run[i:i + sz])
        i += sz
    return groups


def group_seats(seats: Sequence[Dict[str, Any]], rule: Dict[str, Any] | None = None
                ) -> List[List[Dict[str, Any]]]:
    """座席リストを出品グループのリストに変換する。

    1) 連番ランに分ける → 2) 各ランをルールで分割 → 3) グループ列を返す。
    """
    r = {**DEFAULT_RULE, **(rule or {})}
    groups: List[List[Dict[str, Any]]] = []
    for run in find_consecutive_runs(seats):
        groups.extend(_split_run(run, r))
    return groups


def decide_bara_ok(group: Sequence[Dict[str, Any]], rule: Dict[str, Any] | None = None) -> bool:
    """このグループを「バラ売り可」で出品するか。

    - 2席以上（連番）→ False（バラ売り不可＝まとめ売り）
    - 1席（単独）→ single_as_bara_ok 設定に従う（既定True＝バラ売り可）
    """
    r = {**DEFAULT_RULE, **(rule or {})}
    if len(group) >= 2:
        return False
    return bool(r.get("single_as_bara_ok", True))


def describe_groups(groups: Sequence[Sequence[Dict[str, Any]]]) -> str:
    """グループ構成を人間可読な文字列にする（ログ・確認用）。"""
    parts = []
    for g in groups:
        nums = ",".join(str(s.get("num", "?")) for s in g)
        kind = f"{len(g)}連番" if len(g) >= 2 else "単独"
        parts.append(f"[{kind}:{nums}]")
    return " ".join(parts) if parts else "(なし)"
