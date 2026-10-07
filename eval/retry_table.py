"""Aggregate execution-feedback retry runs into a LaTeX table and summary.

Reads eval/results/bedrock_<model>_<lang>.jsonl (first attempt) and
eval/results/retry_<model>_<lang>.jsonl (one corrected attempt for every
invalid or empty first attempt). Writes eval/results/retry_table.tex and
prints a summary with template-clustered bootstrap 95% CIs of the gain.
"""
import glob
import json
import os
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
# RESULTS_DIR selects re-scored copies (eval/results/camera) over the originals
RES = Path(os.environ.get("RESULTS_DIR") or ROOT / "eval" / "results")
N = 460

NAMES = {
    "us.anthropic.claude-opus-5": "Opus 5",
    "us.anthropic.claude-sonnet-5": "Sonnet 5",
    "us.anthropic.claude-haiku-4-5-20251001-v1_0": "Haiku 4.5",
    "us.deepseek.r1-v1_0": "DeepSeek-R1",
    "us.mistral.pixtral-large-2502-v1_0": "Pixtral Large",
    "us.meta.llama3-3-70b-instruct-v1_0": "Llama 3.3 70B",
    "us.meta.llama3-1-8b-instruct-v1_0": "Llama 3.1 8B",
}
ORDER = list(NAMES)

gold_t = {json.loads(l)["id"]: json.loads(l)["template_id"]
          for l in open(ROOT / "benchmark/v1/benchmark.jsonl",
                        encoding="utf-8")}
rng = np.random.default_rng(0)


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def clustered_gain_ci(first, rec_ids):
    """95% CI (points) of accuracy gain, resampling templates."""
    by_t = {}
    for r in first:
        ok0 = bool(r.get("ok"))
        ok1 = ok0 or (r["id"] in rec_ids)
        by_t.setdefault(gold_t[r["id"]], []).append((ok0, ok1))
    ts = list(by_t)
    gains = []
    for _ in range(2000):
        pick = rng.choice(len(ts), size=len(ts), replace=True)
        pairs = [p for i in pick for p in by_t[ts[i]]]
        gains.append(100 * (sum(p[1] for p in pairs)
                            - sum(p[0] for p in pairs)) / len(pairs))
    return np.percentile(gains, [2.5, 97.5])


rows, summary = [], []
for tag in ORDER:
    cells = []
    for lang in ("en", "bn"):
        f1 = RES / f"bedrock_{tag}_{lang}.jsonl"
        f2 = RES / f"retry_{tag}_{lang}.jsonl"
        if not f2.exists():
            cells.append(None)
            continue
        first, retry = load(f1), load(f2)
        first_by = {r["id"]: r for r in first}
        base_ok = sum(bool(r.get("ok")) for r in first)
        rec_ids = {r["id"] for r in retry if r.get("ok")}
        n_rep = len(retry)
        n_inv = sum(1 for r in retry if not first_by[r["id"]].get("valid"))
        n_emp = n_rep - n_inv
        rec_inv = sum(1 for r in retry if r.get("ok")
                      and not first_by[r["id"]].get("valid"))
        rec_emp = len(rec_ids) - rec_inv
        after = base_ok + len(rec_ids)
        lo, hi = clustered_gain_ci(first, rec_ids)
        cells.append(dict(rep=n_rep, inv=n_inv, emp=n_emp, rec=len(rec_ids),
                          rec_inv=rec_inv, rec_emp=rec_emp,
                          before=100 * base_ok / N, after=100 * after / N,
                          lo=lo, hi=hi))
        summary.append(
            f"{NAMES[tag]:18s} {lang}  repairable {n_rep:3d} "
            f"(inv {n_inv:3d}, empty {n_emp:3d})  recovered {len(rec_ids):3d} "
            f"(inv {rec_inv}, empty {rec_emp})  "
            f"{100*base_ok/N:5.1f} -> {100*after/N:5.1f}  "
            f"gain CI [{lo:4.1f},{hi:4.1f}]")
    rows.append((NAMES[tag], cells))

print("\n".join(summary))


def fmt(c):
    if c is None:
        return "-- & -- & --"
    return (f"{c['rep']} & {c['rec']} & "
            f"{c['before']:.1f}$\\rightarrow${c['after']:.1f}")


lines = [
    r"\begin{tabular}{l rrc rrc}",
    r"\toprule",
    r"& \multicolumn{3}{c}{English} & \multicolumn{3}{c}{Bangla} \\",
    r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
    r"Model & rep. & rec. & acc. & rep. & rec. & acc. \\",
    r"\midrule",
]
for name, cells in rows:
    lines.append(f"{name} & {fmt(cells[0])} & {fmt(cells[1])} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
(RES / "retry_table.tex").write_text("\n".join(lines) + "\n",
                                     encoding="utf-8")
print("\nwrote", RES / "retry_table.tex")


def fmt2(c):
    if c is None:
        return "-- & -- & -- & --"
    return f"{c['inv']} & {c['rec_inv']} & {c['emp']} & {c['rec_emp']}"


app = [
    r"\begin{tabular}{l rr rr rr rr}",
    r"\toprule",
    r"& \multicolumn{4}{c}{English} & \multicolumn{4}{c}{Bangla} \\",
    r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}",
    r"& \multicolumn{2}{c}{invalid} & \multicolumn{2}{c}{empty}"
    r" & \multicolumn{2}{c}{invalid} & \multicolumn{2}{c}{empty} \\",
    r"Model & n & rec. & n & rec. & n & rec. & n & rec. \\",
    r"\midrule",
]
for name, cells in rows:
    app.append(f"{name} & {fmt2(cells[0])} & {fmt2(cells[1])} \\\\")
app += [r"\bottomrule", r"\end{tabular}"]
(RES / "retry_appendix.tex").write_text("\n".join(app) + "\n",
                                        encoding="utf-8")
print("wrote", RES / "retry_appendix.tex")
