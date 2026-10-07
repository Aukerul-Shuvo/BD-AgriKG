"""Re-execute the v1 gold queries on the corrected (v1.1) graph.

Benchmark v1.0 was evaluated on the graph as of the NORA submission. The
post-review audit corrected the data; this script keeps every v1 item,
its parameters and its gold query, re-executes the query on the graph
currently loaded (which must be the corrected one) and records the new
gold answer beside the old. Items whose query returns nothing on the
corrected graph (a pest pair that no longer exists) are marked retired.

Usage: python benchmark/regold_v1.py
Writes benchmark/v1/benchmark_v1.1.jsonl and benchmark/v1/CHANGES_v1.1.md
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from grading import compare  # noqa: E402

V1 = ROOT / "benchmark" / "v1"
URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")


def jsonable(v):
    return round(v, 4) if isinstance(v, float) else v


def main():
    items = [json.loads(l) for l in open(V1 / "benchmark.jsonl", encoding="utf-8")]
    driver = GraphDatabase.driver(URI, auth=AUTH)
    out, status = [], Counter()
    changed = defaultdict(list)
    with driver.session(default_access_mode="READ") as s:
        for it in items:
            got = [{k: jsonable(v) for k, v in dict(r).items()}
                   for r in s.run(it["cypher"], **it["params"])]
            if not got:
                st = "retired"
            elif compare(it["gold"], got):
                st = "unchanged"
            else:
                st = "changed"
            status[st] += 1
            if st != "unchanged":
                changed[it["template_id"]].append((it["id"], st))
            rec = dict(it)
            rec["gold_v1_0"] = it["gold"]
            rec["gold"] = got if got else None
            rec["status_v1_1"] = st
            out.append(rec)
    driver.close()

    with open(V1 / "benchmark_v1.1.jsonl", "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    md = ["# Benchmark v1.1: gold answers on the corrected graph", "",
          f"{status['unchanged']} of {len(items)} items keep their v1.0 gold answer, "
          f"{status['changed']} change, {status['retired']} are retired (the query "
          "returns nothing on the corrected graph). Questions, parameters and "
          "gold queries are identical to v1.0; only the executed answers differ. "
          "`benchmark_v1.1.jsonl` holds both (`gold` is v1.1, `gold_v1_0` the "
          "evaluated answer) and a `status_v1_1` field.", "",
          "| template | changed | retired | items |", "|---|---|---|---|"]
    for t, lst in sorted(changed.items(), key=lambda kv: -len(kv[1])):
        c = sum(1 for _, st in lst if st == "changed")
        r = sum(1 for _, st in lst if st == "retired")
        md.append(f"| {t} | {c} | {r} | " + ", ".join(i for i, _ in lst) + " |")
    (V1 / "CHANGES_v1.1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(dict(status))
    print("\n".join(md[6:]))


if __name__ == "__main__":
    main()
