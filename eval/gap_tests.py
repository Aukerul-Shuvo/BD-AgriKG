"""Significance and concentration of the English-Bangla gap, per model.

For each model, from per-item verdicts in a results directory:
- gap: strict EN accuracy minus strict BN accuracy, in points;
- template-clustered percentile bootstrap 95% CI (the paper's procedure,
  eval/bootstrap_gap.py, same seed) and its two-sided bootstrap p;
- cluster sign-flip permutation p: the sign of each template's paired
  difference is flipped at random, 20,000 times;
- sign test over templates with a nonzero paired difference;
- Holm correction of each p across the seven models;
- concentration: the two templates contributing most to the gap, their
  share of it, and the gap recomputed without them.

Usage: python eval/gap_tests.py [results_dir]   (default eval/results/camera)
Writes <results_dir>/gap_tests.md
"""
import glob
import json
import re
import sys
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES = (Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "eval/results/camera").resolve()
NAMES = {
    "us.anthropic.claude-opus-5": "Opus 5",
    "us.anthropic.claude-sonnet-5": "Sonnet 5",
    "us.deepseek.r1-v1_0": "DeepSeek-R1",
    "us.mistral.pixtral-large-2502-v1_0": "Pixtral Large",
    "us.anthropic.claude-haiku-4-5-20251001-v1_0": "Haiku 4.5",
    "us.meta.llama3-3-70b-instruct-v1_0": "Llama 3.3 70B",
    "us.meta.llama3-1-8b-instruct-v1_0": "Llama 3.1 8B",
}


def holm(ps):
    """Holm step-down adjusted p-values, same order as input."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, running)
    return adj


def sign_test_p(pos, neg):
    """Exact two-sided binomial test on pos wins vs neg losses."""
    n, k = pos + neg, min(pos, neg)
    if n == 0:
        return 1.0
    tail = sum(comb(n, j) for j in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    gold = {json.loads(l)["id"]: json.loads(l)["template_id"]
            for l in open(ROOT / "benchmark/v1/benchmark.jsonl",
                          encoding="utf-8")}
    N = len(gold)
    runs = {}
    for f in sorted(glob.glob(str(RES / "bedrock_*.jsonl"))):
        m = re.match(r"bedrock_(.+)_(en|bn)$", Path(f).stem)
        runs[(m.group(1), m.group(2))] = {
            json.loads(l)["id"]: bool(json.loads(l).get("ok"))
            for l in open(f, encoding="utf-8")}
    models = [m for m in NAMES if (m, "en") in runs and (m, "bn") in runs]
    rows = []
    rng = np.random.default_rng(0)     # one generator, models in sorted order,
    for mdl in sorted(models):         # as bootstrap_gap.py drew them
        en, bn = runs[(mdl, "en")], runs[(mdl, "bn")]
        by_t = {}
        for iid, t in gold.items():
            by_t.setdefault(t, []).append((en.get(iid, False), bn.get(iid, False)))
        ts = list(by_t)
        point = 100 * (sum(en.values()) - sum(bn.values())) / N
        # the paper's bootstrap, seed and procedure as in bootstrap_gap.py
        gaps = []
        for _ in range(2000):
            pick = rng.choice(len(ts), size=len(ts), replace=True)
            pairs = [p for i in pick for p in by_t[ts[i]]]
            gaps.append(100 * (sum(p[0] for p in pairs) - sum(p[1] for p in pairs))
                        / len(pairs))
        gaps = np.array(gaps)
        lo, hi = np.percentile(gaps, [2.5, 97.5])
        p_boot = min(1.0, 2 * min((gaps <= 0).mean(), (gaps >= 0).mean()))
        # per-template paired difference in items (EN correct minus BN correct)
        d = np.array([sum(p[0] - p[1] for p in by_t[t]) for t in ts], dtype=float)
        obs = abs(d.sum())
        rng2 = np.random.default_rng(1)
        flips = rng2.choice([-1, 1], size=(20000, len(ts)))
        p_perm = ((np.abs((flips * d).sum(axis=1)) >= obs).sum() + 1) / 20001
        pos, neg = int((d > 0).sum()), int((d < 0).sum())
        p_sign = sign_test_p(pos, neg)
        # concentration
        top = sorted(range(len(ts)), key=lambda i: -d[i])[:2]
        share = 100 * d[top].sum() / d.sum() if d.sum() > 0 else float("nan")
        rest = [t for i, t in enumerate(ts) if i not in top]
        n_rest = sum(len(by_t[t]) for t in rest)
        gap_rest = 100 * sum(p[0] - p[1] for t in rest for p in by_t[t]) / n_rest
        rows.append(dict(model=NAMES[mdl], gap=point, lo=lo, hi=hi, p_boot=p_boot,
                         p_perm=p_perm, pos=pos, neg=neg, tie=len(ts) - pos - neg,
                         p_sign=p_sign, top=[(ts[i], int(d[i])) for i in top],
                         share=share, gap_rest=gap_rest))
    rows.sort(key=lambda r: list(NAMES.values()).index(r["model"]))
    for key in ("p_boot", "p_perm", "p_sign"):
        adj = holm([r[key] for r in rows])
        for r, a in zip(rows, adj):
            r[key + "_holm"] = a
    md = [f"# EN-BN gap tests ({RES.relative_to(ROOT)})", "",
          "| model | gap | 95% CI | p boot | Holm | p sign-flip | Holm | "
          "templates EN>BN / BN>EN / tie | p sign | Holm | top-2 templates "
          "(items) | share | gap without top-2 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['model']} | {r['gap']:+.1f} | [{r['lo']:.1f}, {r['hi']:.1f}] "
                  f"| {r['p_boot']:.3f} | {r['p_boot_holm']:.3f} | {r['p_perm']:.3f} "
                  f"| {r['p_perm_holm']:.3f} | {r['pos']} / {r['neg']} / {r['tie']} "
                  f"| {r['p_sign']:.3f} | {r['p_sign_holm']:.3f} | "
                  + ", ".join(f"{t} ({k:+d})" for t, k in r["top"])
                  + f" | {r['share']:.0f}% | {r['gap_rest']:+.1f} |")
    (RES / "gap_tests.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))

    # the same table for the paper's appendix (copy into papers/nora-latex)
    tex = [r"\begin{table*}[t]", r"\centering\scriptsize",
           r"\setlength{\tabcolsep}{2.6pt}",
           r"\begin{tabular}{l r c rr rr c rr r r}", r"\toprule",
           r"& & & \multicolumn{2}{c}{bootstrap $p$} & \multicolumn{2}{c}{sign-flip $p$} "
           r"& templates & \multicolumn{2}{c}{sign test $p$} & top-2 & gap w/o \\",
           r"Model & gap & 95\% CI & raw & Holm & raw & Holm & EN$>$BN / BN$>$EN / tie "
           r"& raw & Holm & share & top-2 \\", r"\midrule"]
    for r in rows:
        tex.append(f"{r['model']} & {r['gap']:+.1f} & $[{r['lo']:.1f}, {r['hi']:.1f}]$ & "
                   f"{r['p_boot']:.3f} & {r['p_boot_holm']:.3f} & {r['p_perm']:.3f} & "
                   f"{r['p_perm_holm']:.3f} & {r['pos']} / {r['neg']} / {r['tie']} & "
                   f"{r['p_sign']:.3f} & {r['p_sign_holm']:.3f} & {r['share']:.0f}\\% & "
                   f"{r['gap_rest']:+.1f} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\caption{Tests of the EN--BN strict gap per model (points). The",
            r"interval and $p$ are the paper's template-clustered percentile",
            r"bootstrap; the sign-flip test permutes the sign of each template's",
            r"paired difference; the sign test counts templates by the direction",
            r"of their difference; Holm corrects each across the seven models.",
            r"The last two columns give the share of the gap carried by its two",
            r"largest templates and the gap recomputed without them. Three gaps",
            r"survive Holm under the bootstrap, one under the permutation test.}",
            r"\label{tab:gaptests}", r"\end{table*}"]
    (RES / "gap_tests_table.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
