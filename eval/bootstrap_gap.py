"""Paired template-clustered bootstrap CI for the EN-BN strict gap."""
import glob
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
gold = {json.loads(l)["id"]: json.loads(l)["template_id"]
        for l in open(ROOT / "benchmark/v1/benchmark.jsonl", encoding="utf-8")}
runs = {}
for f in sorted(glob.glob(str(ROOT / "eval/results/bedrock_*.jsonl"))):
    m = re.match(r"bedrock_(.+)_(en|bn)$", Path(f).stem)
    runs[(m.group(1), m.group(2))] = {
        json.loads(l)["id"]: bool(json.loads(l).get("ok"))
        for l in open(f, encoding="utf-8")}

rng = np.random.default_rng(0)
models = sorted({m for m, _ in runs})
for mdl in models:
    en, bn = runs[(mdl, "en")], runs[(mdl, "bn")]
    by_t = {}
    for iid, t in gold.items():
        by_t.setdefault(t, []).append((en.get(iid, False), bn.get(iid, False)))
    ts = list(by_t)
    gaps = []
    for _ in range(2000):
        pick = rng.choice(len(ts), size=len(ts), replace=True)
        pairs = [p for i in pick for p in by_t[ts[i]]]
        e = sum(p[0] for p in pairs) / len(pairs)
        b = sum(p[1] for p in pairs) / len(pairs)
        gaps.append(100 * (e - b))
    lo, hi = np.percentile(gaps, [2.5, 97.5])
    point = 100 * (sum(v for v in en.values()) - sum(v for v in bn.values())) / len(gold)
    sig = "sig" if lo > 0 else "ns "
    print(f"{mdl:48s} gap {point:5.1f}  [{lo:5.1f},{hi:5.1f}]  {sig}")
