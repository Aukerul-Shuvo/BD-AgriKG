"""Paired template-clustered bootstrap CI for the EN-BN strict gap,
before and after one execution-feedback repair turn."""
import json
import re
from pathlib import Path

import numpy as np

import os

ROOT = Path(__file__).resolve().parents[1]
# RESULTS_DIR selects the re-scored copies (eval/results/camera)
RES = Path(os.environ.get("RESULTS_DIR") or ROOT / "eval/results")
gold = {json.loads(l)["id"]: json.loads(l)["template_id"]
        for l in open(ROOT / "benchmark/v1/benchmark.jsonl", encoding="utf-8")}


def outcomes(tag, lang):
    first = {json.loads(l)["id"]: bool(json.loads(l).get("ok"))
             for l in open(RES / f"bedrock_{tag}_{lang}.jsonl", encoding="utf-8")}
    f2 = RES / f"retry_{tag}_{lang}.jsonl"
    rec = ({json.loads(l)["id"] for l in open(f2, encoding="utf-8")
            if json.loads(l).get("ok")} if f2.exists() else set())
    after = {i: (ok or i in rec) for i, ok in first.items()}
    return first, after


def gap_ci(en, bn, rng):
    by_t = {}
    for iid, t in gold.items():
        by_t.setdefault(t, []).append((en.get(iid, False), bn.get(iid, False)))
    ts = list(by_t)
    gaps = []
    for _ in range(2000):
        pick = rng.choice(len(ts), size=len(ts), replace=True)
        pairs = [p for i in pick for p in by_t[ts[i]]]
        gaps.append(100 * (sum(p[0] for p in pairs) - sum(p[1] for p in pairs)) / len(pairs))
    point = 100 * (sum(en.values()) - sum(bn.values())) / len(gold)
    lo, hi = np.percentile(gaps, [2.5, 97.5])
    return point, lo, hi


def delta_gap_ci(en0, bn0, en1, bn1, rng):
    """CI of (gap before - gap after), same template resample for both."""
    by_t = {}
    for iid, t in gold.items():
        by_t.setdefault(t, []).append((en0.get(iid, False), bn0.get(iid, False),
                                       en1.get(iid, False), bn1.get(iid, False)))
    ts = list(by_t)
    deltas = []
    for _ in range(2000):
        pick = rng.choice(len(ts), size=len(ts), replace=True)
        q = [p for i in pick for p in by_t[ts[i]]]
        n = len(q)
        g0 = 100 * (sum(p[0] for p in q) - sum(p[1] for p in q)) / n
        g1 = 100 * (sum(p[2] for p in q) - sum(p[3] for p in q)) / n
        deltas.append(g0 - g1)
    point = (100 * (sum(en0.values()) - sum(bn0.values())) / len(gold)
             - 100 * (sum(en1.values()) - sum(bn1.values())) / len(gold))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return point, lo, hi


tags = sorted({re.match(r"bedrock_(.+)_(en|bn)$", p.stem).group(1)
               for p in RES.glob("bedrock_*.jsonl")})
data = {tag: (outcomes(tag, "en"), outcomes(tag, "bn")) for tag in tags}

# "before" intervals replicate eval/bootstrap_gap.py exactly: one generator
# seeded 0, models in sorted order, 2000 draws each, nothing else drawn.
rng0 = np.random.default_rng(0)
before = {tag: gap_ci(data[tag][0][0], data[tag][1][0], rng0) for tag in tags}

# after-repair and narrowing intervals use a separate generator.
rng1 = np.random.default_rng(1)
for tag in tags:
    (en0, en1), (bn0, bn1) = data[tag]
    p0, l0, h0 = before[tag]
    p1, l1, h1 = gap_ci(en1, bn1, rng1)
    d, dl, dh = delta_gap_ci(en0, bn0, en1, bn1, rng1)
    print(f"{tag:46s} before {p0:5.1f} [{l0:5.1f},{h0:5.1f}]   "
          f"after {p1:5.1f} [{l1:5.1f},{h1:5.1f}]   "
          f"narrowing {d:5.1f} [{dl:5.1f},{dh:5.1f}]")
