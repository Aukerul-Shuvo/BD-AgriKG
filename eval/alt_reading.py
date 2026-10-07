"""How many suitability errors are the alternative reading of "most suitable"?

A reviewer noted that "most suitable" could rank by the very-suitable
area instead of by suitability_factor. For every stored run, this takes
the items of the two templates that rank suitability, re-executes the
gold query with the alternative ranking key, and counts the model
failures whose result equals that alternative answer. Run on the v1 graph
snapshot. Reads eval/results/camera, prints the count per run and the
total.
"""
import glob
import json
import re
import sys
from pathlib import Path

from neo4j import GraphDatabase, Query

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grading  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "eval" / "results" / "camera"
URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")
TEMPLATES = ("best_upazila_suitability", "most_suitable_crop_upazila")


def main():
    gold = {json.loads(l)["id"]: json.loads(l)
            for l in open(ROOT / "benchmark/v1/benchmark.jsonl", encoding="utf-8")}
    driver = GraphDatabase.driver(URI, auth=AUTH)
    total_wrong = total_alt = 0
    with driver.session(default_access_mode="READ") as s:
        alt_gold = {}
        for iid, it in gold.items():
            if it["template_id"] in TEMPLATES:
                q = it["cypher"].replace("s.suitability_factor", "s.very_suitable")
                alt_gold[iid] = [dict(r) for r in s.run(q, **it["params"])]
        for f in sorted(glob.glob(str(RES / "bedrock_*.jsonl"))):
            name = re.sub(r"^bedrock_", "", Path(f).stem)
            wrong = alt = 0
            for line in open(f, encoding="utf-8"):
                r = json.loads(line)
                if r["id"] not in alt_gold or r.get("ok") or not r.get("valid"):
                    continue
                wrong += 1
                try:
                    got = [dict(x) for x in s.run(Query(r["cypher"], timeout=15))]
                except Exception:
                    continue
                alt += grading.compare(alt_gold[r["id"]], got)
            total_wrong += wrong
            total_alt += alt
            print(f"{name:48s} wrong-but-valid on suitability templates {wrong:3d}, "
                  f"of which the very-suitable reading {alt:3d}")
    driver.close()
    print(f"\ntotal: {total_alt} of {total_wrong} valid-but-wrong suitability "
          f"answers across all runs are the alternative reading")


if __name__ == "__main__":
    main()
