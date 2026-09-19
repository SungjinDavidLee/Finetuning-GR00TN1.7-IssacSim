#!/usr/bin/env python3
"""Reproduce every statistical test quoted in README.md.

    python3 scripts/stats.py

Two-proportion comparisons use Fisher's exact test; the 95% confidence interval
on the difference uses Newcombe's hybrid score method.
"""

import csv
import math
import os

from scipy.stats import fisher_exact

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def load():
    with open(os.path.join(DATA, "task_summary.csv"), newline="") as fp:
        return list(csv.DictReader(fp))


def wilson(x, n, z=1.96):
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def newcombe(a, na, b, nb):
    l1, u1 = wilson(a, na)
    l2, u2 = wilson(b, nb)
    p1, p2 = a / na, b / nb
    lo = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return 100 * lo, 100 * hi


def compare(label, a, na, b, nb, name_a, name_b):
    _, p = fisher_exact([[a, na - a], [b, nb - b]])
    lo, hi = newcombe(a, na, b, nb)
    print(label)
    print("  %-26s %3d/%-3d  (%.1f%%)" % (name_a, a, na, 100 * a / na))
    print("  %-26s %3d/%-3d  (%.1f%%)" % (name_b, b, nb, 100 * b / nb))
    print("  차이 %+.1f%%p   95%% CI [%+.1f, %+.1f]   Fisher p = %s"
          % (100 * a / na - 100 * b / nb, lo, hi,
             ("%.2e" % p) if p < 0.001 else ("%.3f" % p)))
    print()


def main():
    rows = load()
    n = sum(int(r["n"]) for r in rows)
    ga = sum(int(r["grasp_attempt"]) for r in rows)
    li = sum(int(r["lifted"]) for r in rows)
    pl = sum(int(r["placed"]) for r in rows)
    fk = sum(int(r["franka_placed"]) for r in rows)
    fn = sum(int(r["franka_n"]) for r in rows)

    print("=" * 66)
    print("README 에 인용된 모든 검정값")
    print("=" * 66)
    print()

    print("태스크별")
    print("task   n  파지시도      들기          배치        Franka")
    for r in rows:
        t, m = int(r["task"]), int(r["n"])
        print("%4d %3d  %2d(%3.0f%%)  %2d(%3.0f%%)  %2d(%3.0f%%)   %2d/%d(%3.0f%%)"
              % (t, m, int(r["grasp_attempt"]), 100 * int(r["grasp_attempt"]) / m,
                 int(r["lifted"]), 100 * int(r["lifted"]) / m,
                 int(r["placed"]), 100 * int(r["placed"]) / m,
                 int(r["franka_placed"]), int(r["franka_n"]),
                 100 * int(r["franka_placed"]) / int(r["franka_n"])))
    print()
    print("FR5 합계  n=%d  파지시도 %d (%.1f%%)  들기 %d (%.1f%%)  배치 %d (%.1f%%)"
          % (n, ga, 100 * ga / n, li, 100 * li / n, pl, 100 * pl / n))
    print()

    compare("[1] 로봇 교체 — 전체 10태스크",
            pl, n, fk, fn, "FR5 + AG-95 (6축)", "Franka Panda (7축)")

    ex = [r for r in rows if int(r["task"]) not in (4, 6)]
    compare("[2] task 4·6 제외 8태스크 (사후 선택)",
            sum(int(r["placed"]) for r in ex), sum(int(r["n"]) for r in ex),
            sum(int(r["franka_placed"]) for r in ex),
            sum(int(r["franka_n"]) for r in ex),
            "FR5 + AG-95", "Franka Panda")

    t4 = [r for r in rows if int(r["task"]) == 4][0]
    print("[3] task 4 — 6축 작업공간 한계")
    print("  파지 시도 %s/%s,  들기 %s/%s,  배치 %s/%s"
          % (t4["grasp_attempt"], t4["n"], t4["lifted"], t4["n"],
             t4["placed"], t4["n"]))
    print("  IK 실패 2638~2749 / 2800 행 (94~98%)")
    print("  작업공간 클램프 0/0/0/0 — 명령 위치는 범위 안")
    print()

    t6 = [r for r in rows if int(r["task"]) == 6][0]
    print("[4] task 6 — 이송 거리 최장")
    print("  파지 시도 %s/%s,  들기 %s/%s,  배치 %s/%s"
          % (t6["grasp_attempt"], t6["n"], t6["lifted"], t6["n"],
             t6["placed"], t6["n"]))
    print("  물체-접시 거리 241 mm (task 5 는 143 mm)")
    print("  파지 후 미끄러짐 0.12~0.45 (다른 태스크는 0.10 근처)")
    print()

    print("[5] 물리 발산")
    print("  MAXJ 미적용  48판 중 5건 (10.4%)")
    print("  MAXJ=0.5     498판 중 0건")
    _, p = fisher_exact([[0, 498], [5, 43]])
    print("  Fisher p = %.2e" % p)


if __name__ == "__main__":
    main()
