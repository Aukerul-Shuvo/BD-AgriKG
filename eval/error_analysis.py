"""Classify every failure in the saved runs into a small taxonomy.

Buckets per item (strict grading):
  api          model call failed
  unsafe       write clause rejected
  syntax       Cypher did not execute
  formatting   right answer, extra value(s) per row (lenient passes)
  empty        executed but returned nothing (wrong filter / hallucinated
               schema element that silently matches nothing)
  wrong        executed, non-empty, wrong values or row count

Prints a composition table per model (EN+BN pooled) and writes
eval/results/error_table.tex plus example failures for the paper.
"""
import glob
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase, Query

import os

ROOT = Path(__file__).resolve().parents[1]
# RESULTS_DIR selects the re-scored copies (eval/results/camera), whose
# stored ok / ok_lenient verdicts are then used for the pass and
# formatting buckets instead of this script's own grader
RESULTS = Path(os.environ.get("RESULTS_DIR") or ROOT / "eval" / "results")
BENCH = ROOT / "benchmark" / "v1"

URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")

SHORT = {
    "us.anthropic.claude-opus-5": "Claude Opus 5",
    "us.anthropic.claude-sonnet-5": "Claude Sonnet 5",
    "us.anthropic.claude-haiku-4-5-20251001-v1_0": "Claude Haiku 4.5",
    "us.meta.llama3-3-70b-instruct-v1_0": "Llama 3.3 70B",
    "us.meta.llama3-1-8b-instruct-v1_0": "Llama 3.1 8B",
    "us.mistral.pixtral-large-2502-v1_0": "Pixtral Large 25.02",
    "us.deepseek.r1-v1_0": "DeepSeek-R1",
}
ORDER = ["Claude Opus 5", "Claude Sonnet 5", "DeepSeek-R1",
         "Pixtral Large 25.02", "Claude Haiku 4.5", "Llama 3.3 70B",
         "Llama 3.1 8B"]
BUCKETS = ["formatting", "wrong", "empty", "syntax", "unsafe", "api"]


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


def row_match(g, h, slack):
    gs, hs = list(g.values()), list(h.values())
    if not (len(gs) <= len(hs) <= len(gs) + slack):
        return False
    rem = list(hs)
    for v in gs:
        for i, w in enumerate(rem):
            if val_eq(v, w):
                del rem[i]
                break
        else:
            return False
    return True


def compare(gold, got, slack):
    if len(gold) != len(got):
        return False
    rem = list(got)
    for g in gold:
        for i, h in enumerate(rem):
            if row_match(g, h, slack):
                del rem[i]
                break
        else:
            return False
    return True


def main():
    gold = {json.loads(l)["id"]: json.loads(l)
            for l in open(BENCH / "benchmark.jsonl", encoding="utf-8")}
    driver = GraphDatabase.driver(URI, auth=AUTH)
    comp = defaultdict(Counter)
    totals = Counter()
    examples = defaultdict(list)
    cache = {}
    import sys as _sys
    with driver.session(default_access_mode="READ") as s:
        for f in sorted(glob.glob(str(RESULTS / "bedrock_*.jsonl"))):
            print("FILE", Path(f).stem, flush=True, file=_sys.stderr)
            m = re.match(r"bedrock_(.+)_(en|bn)$", Path(f).stem)
            if not m:
                continue
            model = SHORT.get(m.group(1), m.group(1))
            for line in open(f, encoding="utf-8"):
                r = json.loads(line)
                it = gold.get(r["id"])
                totals[model] += 1
                err = str(r.get("error", ""))
                if err.startswith("model:"):
                    comp[model]["api"] += 1
                    continue
                if err == "write-clause":
                    comp[model]["unsafe"] += 1
                    continue
                if not r.get("valid"):
                    comp[model]["syntax"] += 1
                    if len(examples["syntax"]) < 6:
                        examples["syntax"].append((model, r["id"],
                                                   r.get("cypher", "")[:200],
                                                   err[:120]))
                    continue
                cy = r.get("cypher", "")
                if cy not in cache:
                    try:
                        cache[cy] = [dict(x) for x in
                                     s.run(Query(cy, timeout=6))]
                    except Exception:
                        cache[cy] = None
                got = cache[cy]
                if got is None:
                    comp[model]["syntax"] += 1
                    continue
                strict = r["ok"] if "ok_lenient" in r else compare(it["gold"], got, 0)
                if strict:
                    continue  # strict pass, not a failure
                lenient = r["ok_lenient"] if "ok_lenient" in r else compare(it["gold"], got, 1)
                if lenient:
                    comp[model]["formatting"] += 1
                elif len(got) == 0:
                    comp[model]["empty"] += 1
                    if len(examples["empty"]) < 6:
                        examples["empty"].append((model, r["id"],
                                                  cy[:220], ""))
                else:
                    comp[model]["wrong"] += 1
                    if len(examples["wrong"]) < 6:
                        examples["wrong"].append((model, r["id"],
                                                  cy[:220], ""))
    driver.close()

    hdr = f"{'model':22s}" + "".join(f"{b:>12s}" for b in BUCKETS) + f"{'fails':>8s}"
    print(hdr)
    tex = []
    for mdl in ORDER:
        c = comp[mdl]
        fails = sum(c.values())
        print(f"{mdl:22s}" + "".join(f"{c[b]:12d}" for b in BUCKETS)
              + f"{fails:8d}")
        n = totals[mdl]
        tex.append(mdl.replace(" 25.02", "") + " & " +
                   " & ".join(f"{100*c[b]/n:.1f}" for b in BUCKETS) + r" \\")
    (RESULTS / "error_table.tex").write_text("\n".join(tex), encoding="utf-8")

    print("\nexamples:")
    for k, exs in examples.items():
        print(f"-- {k}")
        for mdl, iid, cy, err in exs:
            print(f"   [{mdl}] {iid}: {cy}")
            if err:
                print(f"      err: {err}")


if __name__ == "__main__":
    main()
