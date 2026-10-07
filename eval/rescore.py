"""Re-score all saved runs from their stored Cypher, no API calls.

Two metrics per config:
- strict:  exact projection (rows match as value multisets, no extra values)
- lenient: same row count, gold values contained in the row, at most ONE
           extra value per row (accepts 'winner plus its metric' answers
           while keeping the many-column dump exploit dead)

Writes eval/results/final_summary.md and final_table.tex.
"""
import glob
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase, Query

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
BENCH = ROOT / "benchmark" / "v1"

URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")

SHORT = {
    "us.anthropic.claude-sonnet-5": "Claude Sonnet 5",
    "us.anthropic.claude-opus-5": "Claude Opus 5",
    "us.anthropic.claude-haiku-4-5-20251001-v1_0": "Claude Haiku 4.5",
    "us.meta.llama3-3-70b-instruct-v1_0": "Llama 3.3 70B",
    "us.meta.llama3-1-8b-instruct-v1_0": "Llama 3.1 8B",
    "us.mistral.pixtral-large-2502-v1_0": "Pixtral Large 25.02",
    "us.deepseek.r1-v1_0": "DeepSeek-R1",
}


def norm_val(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return float(v)
    if isinstance(v, str):
        return v.strip()
    return v


def val_eq(a, b):
    a, b = norm_val(a), norm_val(b)
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    return a == b


def row_match(gold_row, got_row, slack):
    gs, hs = list(gold_row.values()), list(got_row.values())
    if not (len(gs) <= len(hs) <= len(gs) + slack):
        return False
    remaining = list(hs)
    for v in gs:
        for i, w in enumerate(remaining):
            if val_eq(v, w):
                del remaining[i]
                break
        else:
            return False
    return True


def compare(gold_rows, got_rows, slack):
    if len(gold_rows) != len(got_rows):
        return False
    remaining = list(got_rows)
    for g in gold_rows:
        for i, h in enumerate(remaining):
            if row_match(g, h, slack):
                del remaining[i]
                break
        else:
            return False
    return True


def main():
    gold = {json.loads(l)["id"]: json.loads(l)
            for l in open(BENCH / "benchmark.jsonl", encoding="utf-8")}
    driver = GraphDatabase.driver(URI, auth=AUTH)
    scores = {}
    cache = {}
    with driver.session(default_access_mode="READ") as s:
        for f in sorted(glob.glob(str(RESULTS / "bedrock_*.jsonl"))):
            m = re.match(r"bedrock_(.+)_(en|bn)$", Path(f).stem)
            if not m:
                continue
            model, lang = m.groups()
            rows = [json.loads(l) for l in open(f, encoding="utf-8")]
            n = len(rows)
            strict = lenient = valid = 0
            by_cat = defaultdict(lambda: [0, 0])
            for r in rows:
                it = gold.get(r["id"])
                cy = r.get("cypher", "")
                ok_s = ok_l = False
                if it and cy and r.get("valid"):
                    key = cy
                    if key not in cache:
                        try:
                            cache[key] = [dict(x) for x in
                                          s.run(Query(cy, timeout=15))]
                        except Exception:
                            cache[key] = None
                    got = cache[key]
                    if got is not None:
                        valid += 1
                        ok_s = compare(it["gold"], got, slack=0)
                        ok_l = ok_s or compare(it["gold"], got, slack=1)
                strict += ok_s
                lenient += ok_l
                cat = it["category"] if it else "?"
                by_cat[cat][0] += ok_s
                by_cat[cat][1] += 1
            scores[(model, lang)] = dict(n=n, valid=valid, strict=strict,
                                         lenient=lenient, by_cat=dict(by_cat))
    driver.close()

    models = sorted({m for m, _ in scores},
                    key=lambda m: -scores.get((m, "en"), {}).get("strict", 0))
    md = ["| model | lang | valid | strict | lenient |",
          "|---|---|---|---|---|"]
    tex = []
    for m in models:
        label = SHORT.get(m, m)
        for lang in ("en", "bn"):
            sc = scores.get((m, lang))
            if not sc:
                continue
            md.append(f"| {label} | {lang} | {sc['valid']/sc['n']:.1%} | "
                      f"**{sc['strict']/sc['n']:.1%}** | "
                      f"{sc['lenient']/sc['n']:.1%} |")
        en, bn = scores.get((m, "en")), scores.get((m, "bn"))
        if en and bn:
            tex.append(
                f"{label} & {en['valid']/en['n']*100:.1f} & "
                f"{en['strict']/en['n']*100:.1f} & {en['lenient']/en['n']*100:.1f} & "
                f"{bn['valid']/bn['n']*100:.1f} & "
                f"{bn['strict']/bn['n']*100:.1f} & {bn['lenient']/bn['n']*100:.1f} & "
                f"{(en['strict']-bn['strict'])/en['n']*100:+.1f} \\\\")
    (RESULTS / "final_summary.md").write_text("\n".join(md), encoding="utf-8")
    (RESULTS / "final_table.tex").write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
