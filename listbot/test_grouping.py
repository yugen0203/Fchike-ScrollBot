"""grouping.py の単体テスト（ブラウザ不要）。

実行: python -m listbot.test_grouping
"""
from __future__ import annotations

from .grouping import (decide_bara_ok, describe_groups, find_consecutive_runs,
                       group_seats, partition_sizes)


def _seats(*nums, section="103", row="11"):
    return [{"section": section, "row": row, "num": n, "label": f"Sec.{section} {row}列 {n}番"}
            for n in nums]


def _sizes(groups):
    return [len(g) for g in groups]


def run() -> int:
    fails = 0

    def check(name, got, want):
        nonlocal fails
        ok = got == want
        if not ok:
            fails += 1
        print(f"{'OK ' if ok else 'NG '} {name}: got={got} want={want}")

    # --- partition_sizes ---
    together = {"mode": "together"}
    check("together 2", partition_sizes(2, together), [2])
    check("together 4", partition_sizes(4, together), [4])
    check("together 8", partition_sizes(8, together), [8])
    check("together 1", partition_sizes(1, together), [1])

    max2_single = {"mode": "max_size", "max_group_size": 2, "remainder": "single"}
    check("max2 single 4", partition_sizes(4, max2_single), [2, 2])
    check("max2 single 5", partition_sizes(5, max2_single), [2, 2, 1])
    check("max2 single 6", partition_sizes(6, max2_single), [2, 2, 2])
    check("max2 single 3", partition_sizes(3, max2_single), [2, 1])

    max2_merge = {"mode": "max_size", "max_group_size": 2, "remainder": "merge"}
    check("max2 merge 3", partition_sizes(3, max2_merge), [3])
    check("max2 merge 5", partition_sizes(5, max2_merge), [2, 3])
    check("max2 merge 4", partition_sizes(4, max2_merge), [2, 2])

    overrides = {"mode": "max_size", "max_group_size": 2,
                 "partition_overrides": {3: [2, 1], 4: [2, 2], 8: [4, 4]}}
    check("override 3", partition_sizes(3, overrides), [2, 1])
    check("override 8", partition_sizes(8, overrides), [4, 4])

    # --- find_consecutive_runs ---
    runs = find_consecutive_runs(_seats(5, 6, 7, 8))
    check("one run of 4", [_sizes([r]) for r in [runs]][0] if False else len(runs), 1)
    check("run len 4", len(runs[0]), 4)

    # 非連続: 5,6 と 10,11 は別ラン
    runs2 = find_consecutive_runs(_seats(5, 6, 10, 11))
    check("two runs", len(runs2), 2)
    check("run sizes", _sizes(runs2), [2, 2])

    # 別の列は連番にしない
    mixed = _seats(5, 6, row="11") + _seats(7, row="12")
    runs3 = find_consecutive_runs(mixed)
    check("row boundary", len(runs3), 2)

    # --- group_seats（既定=together）---
    g = group_seats(_seats(5, 6, 7, 8))
    check("default together 4 -> 1 group", _sizes(g), [4])

    g2 = group_seats(_seats(5, 6))
    check("default together 5,6 -> [2]", _sizes(g2), [2])

    # max_size 分割
    g3 = group_seats(_seats(5, 6, 7, 8), {"mode": "max_size", "max_group_size": 2})
    check("max2 4 -> [2,2]", _sizes(g3), [2, 2])

    # 非連続 + 連番混在
    g4 = group_seats(_seats(5, 6, 10))
    check("5,6,10 -> [2,1]", _sizes(g4), [2, 1])

    # --- decide_bara_ok ---
    check("2連番 -> bara不可(False)", decide_bara_ok(_seats(5, 6)), False)
    check("単独 -> bara可(True)", decide_bara_ok(_seats(5)), True)
    check("単独 single_as_bara_ok=False -> False",
          decide_bara_ok(_seats(5), {"single_as_bara_ok": False}), False)

    print("\n" + describe_groups(group_seats(_seats(5, 6, 7, 8, 10))))
    print("partition examples: 3=%s 5=%s 7=%s" % (
        partition_sizes(3, max2_single), partition_sizes(5, max2_single),
        partition_sizes(7, max2_single)))

    print(f"\n{'ALL PASS' if fails == 0 else str(fails) + ' FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    sys.exit(run())
