"""Re-score the NORA (benchmark v1) runs under the corrected grader.

Run against the graph exactly as it was evaluated (load the v1 snapshot
with KG_DIR, see src/load_neo4j.py). For every stored query the script
re-executes it and grades the result twice: with the grader the submitted
paper used (eval/rescore.py, kept verbatim as OLD) and with eval/grading.py
(NEW), which differs in two rules: booleans match only booleans, and a
single collect() list is read as rows. The strict OLD score must reproduce
the "ok" stored at run time; any mismatch means the graph snapshot is not
the evaluated one, and the script says so.

Writes eval/results/camera/<same file name>.jsonl with ok under the new
grader where the graders differ and the stored verdict otherwise (a few
queries order by a null property and so return an arbitrary row on each
execution), plus ok_old and ok_lenient (so retry_table.py and the figures can be rebuilt from them)
and eval/results/camera/rescore_graders.md with the before/after table.

Usage: python eval/rescore_v1_graders.py
"""
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase, Query

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grading                       # noqa: E402  (NEW)
import rescore as old                # noqa: E402  (OLD, verbatim)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
OUT = RESULTS / "camera"
BENCH = ROOT / "benchmark" / "v1"
URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")


def lenient_new(gold_rows, got_rows):
    """The paper's lenient metric (one extra value per row allowed) under
    the new value rules: collect() unpacked, booleans strict."""
    got_rows = grading.unpack_collected(got_rows)
    if len(gold_rows) != len(got_rows):
        return False
    remaining = list(got_rows)
    for g in gold_rows:
        for i, h in enumerate(remaining):
            gs, hs = list(g.values()), list(h.values())
            if not (len(gs) <= len(hs) <= len(gs) + 1):
                continue
            rem = list(hs)
            for v in gs:
                for j, w in enumerate(rem):
                    if grading.val_eq(v, w):
                        del rem[j]
                        break
                else:
                    break
            else:
                del remaining[i]
                break
        else:
            return False
    return True


def main():
    gold = {json.loads(l)["id"]: json.loads(l)
            for l in open(BENCH / "benchmark.jsonl", encoding="utf-8")}
    files = sorted(p for p in RESULTS.glob("*.jsonl")
                   if re.match(r"(bedrock|retry|rerun)_", p.name))
    OUT.mkdir(exist_ok=True)
    driver = GraphDatabase.driver(URI, auth=AUTH)
    cache, table, snapshot_bad = {}, [], 0
    with driver.session(default_access_mode="READ") as s:
        # the graph must reproduce every gold answer first
        bad_gold = 0
        for it in gold.values():
            got = [dict(x) for x in s.run(it["cypher"], **it["params"])]
            bad_gold += not grading.compare(it["gold"], got)
        print(f"gold answers reproduced on this graph: {len(gold) - bad_gold}"
              f"/{len(gold)}")
        if bad_gold:
            sys.exit("this is not the v1 graph snapshot; load it with KG_DIR")

        for f in files:
            rows = [json.loads(l) for l in open(f, encoding="utf-8")]
            c = defaultdict(int)
            flips = []
            out_rows = []
            for r in rows:
                it = gold.get(r["id"])
                cy = r.get("cypher", "")
                so = sn = lo = ln = False
                if it and cy and r.get("valid"):
                    if cy not in cache:
                        try:
                            cache[cy] = [dict(x) for x in
                                         s.run(Query(cy, timeout=15))]
                        except Exception:
                            cache[cy] = None
                    got = cache[cy]
                    if got is not None:
                        so = old.compare(it["gold"], got, slack=0)
                        lo = so or old.compare(it["gold"], got, slack=1)
                        sn = grading.compare(it["gold"], got)
                        ln = sn or lenient_new(it["gold"], got)
                stored = bool(r.get("ok"))
                if "ok" in r and stored != so:
                    c["stored_ok_mismatch"] += 1
                c["n"] += 1
                c["strict_old"] += so
                c["strict_new"] += sn
                c["lenient_old"] += lo
                c["lenient_new"] += ln
                if so != sn:
                    flips.append((r["id"], so, sn))
                nr = dict(r)
                if "ok" in r or r.get("valid"):
                    # where the two graders agree, keep the verdict as run:
                    # six queries order by a null property and return an
                    # arbitrary row, so re-execution is a coin flip
                    nr["ok"] = sn if so != sn else stored
                    nr["ok_old"] = so
                    # lenient adds to the strict verdict only what passes
                    # lenient and not strict, so a coin-flip query cannot
                    # pass lenient while its strict verdict stays as run
                    nr["ok_lenient"] = nr["ok"] or (ln and not sn)
                out_rows.append(nr)
            with open(OUT / f.name, "w", encoding="utf-8") as g:
                for nr in out_rows:
                    g.write(json.dumps(nr, ensure_ascii=False, default=str)
                            + "\n")
            snapshot_bad += c["stored_ok_mismatch"]
            table.append((f.name, {k: c[k] for k in ("n", "stored_ok_mismatch", "strict_old", "strict_new", "lenient_old", "lenient_new")}, flips))
    driver.close()

    md = ["# NORA runs re-scored under the corrected grader", "",
          "Graph: the v1 snapshot as evaluated (gold reproduced "
          f"{len(gold)}/{len(gold)}). OLD = grader of the submitted paper, "
          "NEW = eval/grading.py (booleans strict, collect() unpacked).", "",
          "| run | n | stored ok ≠ OLD | strict OLD | strict NEW | "
          "lenient OLD | lenient NEW | items changed |",
          "|---|---|---|---|---|---|---|---|"]
    for name, c, flips in table:
        md.append(f"| {name.replace('.jsonl', '')} | {c['n']} | "
                  f"{c['stored_ok_mismatch']} | {c['strict_old']} | "
                  f"{c['strict_new']} | {c['lenient_old']} | "
                  f"{c['lenient_new']} | "
                  + (", ".join(f"{i}:{'+' if n else '-'}" for i, o, n in flips)
                     or "none") + " |")
    (OUT / "rescore_graders.md").write_text("\n".join(md) + "\n",
                                            encoding="utf-8")
    print("\n".join(md))
    if snapshot_bad:
        print(f"\nnote: {snapshot_bad} stored verdicts differ from the OLD grader "
              "on re-execution (queries that order by a null property return "
              "an arbitrary row); the verdicts as run were kept")


if __name__ == "__main__":
    main()
