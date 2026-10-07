"""Execution-feedback repair experiment: one corrected attempt for failures.

For each item whose first attempt (from the saved run) was INVALID or
returned an EMPTY result, send the model a follow-up turn containing the
execution error (or the empty-result signal) and ask for a corrected
query. Signals never include the gold answer, so there is no leakage.
Wrong-but-non-empty results get no retry (no honest signal exists).

Usage:
  python eval/run_retry.py --adapter ollama:llama3.1:8b-instruct-q8_0 --lang en
  python eval/run_retry.py --bench benchmark/v1 \
      --adapter bedrock:us.anthropic.claude-haiku-4-5-20251001-v1:0 --lang en
The adapter spec is the one given to run_eval, whose results file this
reads. Writes retry_<spec>_<lang>.jsonl beside the first-attempt results
(eval/results/ for v1, eval/results/<version>/ otherwise) and prints
recovery stats.
"""
import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

from neo4j import GraphDatabase, Query

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters import make_adapter  # noqa: E402
from run_eval import (SYSTEM, extract_cypher, FORBIDDEN,  # noqa: E402
                      DEFAULT_BENCH, bench_paths, compare)

ROOT = Path(__file__).resolve().parents[1]
URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")

RETRY_TMPL = (
    "Executing your query {signal}. Reply with a corrected Cypher query "
    "only, following the same rules."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True,
                    help="adapter spec as given to run_eval")
    ap.add_argument("--lang", choices=["en", "bn"], required=True)
    ap.add_argument("--bench", default=DEFAULT_BENCH)
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()
    BENCH, RESULTS = bench_paths(args.bench)

    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=True)
    except ImportError:
        pass

    items = {json.loads(l)["id"]: json.loads(l)
             for l in open(BENCH / "benchmark.jsonl", encoding="utf-8")}
    schema = (BENCH / "schema.txt").read_text(encoding="utf-8")
    system = SYSTEM.format(schema=schema)
    # the same file name run_eval writes for this adapter spec
    tag = re.sub(r"[^A-Za-z0-9._-]", "_", args.adapter)
    first = [json.loads(l) for l in
             open(RESULTS / f"{tag}_{args.lang}.jsonl", encoding="utf-8")]
    adapter = make_adapter(args.adapter)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    out, n_retry, n_rec = [], 0, 0
    with driver.session(default_access_mode="READ") as s:
        for r in first:
            if r.get("ok"):
                continue
            it = items[r["id"]]
            cy1 = r.get("cypher", "")
            # determine the honest feedback signal
            signal = None
            if not r.get("valid"):
                err = str(r.get("error", ""))[:300]
                signal = f"failed with this error: {err}"
            else:
                try:
                    got = [dict(x) for x in s.run(Query(cy1, timeout=6))]
                    if len(got) == 0:
                        signal = "executed but returned zero rows"
                except Exception as e:
                    signal = f"failed with this error: {str(e)[:300]}"
            if signal is None:
                continue  # wrong-but-non-empty: no honest signal
            n_retry += 1
            q = it["question_en"] if args.lang == "en" else it["question_bn"]
            user2 = (q + "\n\nYour previous query:\n" + cy1 + "\n\n"
                     + RETRY_TMPL.format(signal=signal))
            try:
                raw = adapter.generate(system, user2)
            except Exception as e:
                out.append({"id": r["id"], "retried": True, "ok": False,
                            "error": f"model:{e}"})
                continue
            cy2 = extract_cypher(raw)
            rec = {"id": r["id"], "retried": True, "cypher": cy2,
                   "category": it["category"]}
            if FORBIDDEN.search(cy2):
                rec.update(ok=False, valid=False, error="write-clause")
            else:
                try:
                    got2 = [dict(x) for x in s.run(Query(cy2, timeout=15))]
                    rec["valid"] = True
                    rec["ok"] = compare(it["gold"], got2)
                except Exception as e:
                    rec.update(ok=False, valid=False,
                               error=f"cypher:{str(e)[:150]}")
            n_rec += bool(rec.get("ok"))
            out.append(rec)
            if args.sleep:
                time.sleep(args.sleep)
    driver.close()

    with open(RESULTS / f"retry_{tag}_{args.lang}.jsonl", "w",
              encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    base_ok = sum(bool(r.get("ok")) for r in first)
    n = len(first)
    print(f"{args.adapter} {args.lang}: retried {n_retry} "
          f"(invalid/empty), recovered {n_rec}; strict accuracy "
          f"{base_ok}/{n} = {base_ok/n:.1%} -> "
          f"{(base_ok+n_rec)}/{n} = {(base_ok+n_rec)/n:.1%}")


if __name__ == "__main__":
    main()
