"""Aggregate eval/results/*.jsonl into the paper's results tables.

Writes eval/results/summary.md (readable) and eval/results/table.tex
(ACL booktabs body). Metrics: valid-Cypher rate, execution accuracy,
per-category accuracy, and the EN-BN gap per model.
"""
import glob
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"

SHORT = {
    "us.anthropic.claude-sonnet-5": "Claude Sonnet 5",
    "us.anthropic.claude-haiku-4-5-20251001-v1_0": "Claude Haiku 4.5",
    "us.meta.llama3-3-70b-instruct-v1_0": "Llama 3.3 70B",
    "us.meta.llama3-1-8b-instruct-v1_0": "Llama 3.1 8B",
    "us.mistral.pixtral-large-2502-v1_0": "Mistral Large 25.02",
    "us.deepseek.r1-v1_0": "DeepSeek-R1",
}


def load():
    runs = {}
    for f in glob.glob(str(RESULTS / "bedrock_*.jsonl")):
        name = Path(f).stem  # bedrock_<model>_<lang>
        m = re.match(r"bedrock_(.+)_(en|bn)$", name)
        if not m:
            continue
        model, lang = m.groups()
        rows = [json.loads(l) for l in open(f, encoding="utf-8")]
        runs[(model, lang)] = rows
    return runs


def acc(rows):
    return sum(bool(r.get("ok")) for r in rows) / max(len(rows), 1)


def valid(rows):
    return sum(bool(r.get("valid")) for r in rows) / max(len(rows), 1)


def main():
    runs = load()
    if not runs:
        print("no result files in eval/results/")
        return
    models = sorted({m for m, _ in runs},
                    key=lambda m: -acc(runs.get((m, "en"), [])))
    cats = sorted({r.get("category") for rows in runs.values()
                   for r in rows if r.get("category")})

    md = ["| model | lang | valid | exec acc | " +
          " | ".join(cats) + " |",
          "|" + "---|" * (4 + len(cats))]
    tex = []
    for m in models:
        label = SHORT.get(m, m)
        for lang in ("en", "bn"):
            rows = runs.get((m, lang))
            if not rows:
                continue
            by_cat = defaultdict(list)
            for r in rows:
                by_cat[r.get("category")].append(r)
            md.append(f"| {label} | {lang} | {valid(rows):.1%} | "
                      f"**{acc(rows):.1%}** | " +
                      " | ".join(f"{acc(by_cat[c]):.0%}" for c in cats) + " |")
        en, bn = runs.get((m, "en")), runs.get((m, "bn"))
        if en and bn:
            md.append(f"| {label} | gap | | {acc(en) - acc(bn):+.1%} | " +
                      " | ".join("" for _ in cats) + "|")
            tex.append(f"{label} & {valid(en):.1%} & {acc(en):.1%} & "
                       f"{valid(bn):.1%} & {acc(bn):.1%} & "
                       f"{(acc(en) - acc(bn)) * 100:+.1f} \\\\"
                       .replace("%", "\\%"))

    (RESULTS / "summary.md").write_text("\n".join(md), encoding="utf-8")
    (RESULTS / "table.tex").write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {RESULTS / 'summary.md'} and table.tex")


if __name__ == "__main__":
    main()
