"""Template-clustered bootstrap CIs for strict accuracy per config."""
import glob
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
gold = {json.loads(l)["id"]: json.loads(l)["template_id"]
        for l in open(ROOT / "benchmark/v1/benchmark.jsonl", encoding="utf-8")}
rng = np.random.default_rng(0)
w = 0
for f in sorted(glob.glob(str(ROOT / "eval/results/bedrock_*.jsonl"))):
    rows = [json.loads(l) for l in open(f, encoding="utf-8")]
    by_t = {}
    for r in rows:
        by_t.setdefault(gold.get(r["id"]), []).append(bool(r.get("ok")))
    ts = list(by_t)
    accs = []
    for _ in range(2000):
        pick = rng.choice(len(ts), size=len(ts), replace=True)
        vals = [v for i in pick for v in by_t[ts[i]]]
        accs.append(100 * sum(vals) / len(vals))
    lo, hi = np.percentile(accs, [2.5, 97.5])
    point = 100 * sum(sum(v) for v in by_t.values()) / len(rows)
    name = Path(f).stem.replace("bedrock_", "")
    print(f"{name:52s} {point:5.1f}  [{lo:5.1f},{hi:5.1f}]  half {((hi-lo)/2):4.1f}")
    w = max(w, (hi - lo) / 2)
print("max half-width:", round(w, 1))
