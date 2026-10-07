"""Execution-accuracy evaluation for the BD-AgriKG Text2Cypher benchmark.

For each benchmark item: prompt the model with the KG schema and the
question, extract the generated Cypher, execute it read-only against Neo4j,
and compare the result set with the gold result by VALUES (column names are
free; row multisets must match; row order matters only when the gold query
orders and limits).

Grading lives in eval/grading.py. Results for benchmark v1 are written to
eval/results/, as the NORA paper reports them; any other benchmark writes to
eval/results/<version>/, so a new run can never overwrite a reported one.

Usage:
  python eval/run_eval.py --adapter gold --lang en          # harness smoke test
  python eval/run_eval.py --adapter bedrock:anthropic.claude-sonnet-5 --lang bn
  python eval/run_eval.py --bench benchmark/v1 ...          # the NORA benchmark
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

from neo4j import GraphDatabase, Query
from neo4j.exceptions import ServiceUnavailable, SessionExpired

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters import make_adapter, GoldAdapter  # noqa: E402
from grading import compare  # noqa: E402,F401  (run_retry imports it here)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCH = "benchmark/v1"

# Failures of the infrastructure rather than the model: an unreachable
# Neo4j, or a model server that refuses the connection or times out
# (OSError covers urllib's URLError and socket timeouts).
INFRA = (OSError, ServiceUnavailable, SessionExpired)


def bench_paths(bench):
    """(benchmark directory, results directory) for a benchmark version."""
    path = ROOT / bench
    out = ROOT / "eval" / "results"
    return path, (out if path.name == "v1" else out / path.name)

URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")

SYSTEM = """You translate natural-language questions about Bangladeshi \
agriculture into Cypher queries for a Neo4j knowledge graph.

{schema}

Rules:
- Output ONLY the Cypher query, no explanation, no code fences.
- The question may be in English or Bangla; entity names in the graph are in
  English (crops: Aus, Aman, Boro, ...; districts: current spellings).
- Read-only queries only (MATCH/RETURN); never CREATE, MERGE, SET or DELETE.
- Return ONLY the value or values the question asks for, nothing extra, and
  alias the main answer column AS answer.
"""


def extract_cypher(text):
    text = text.strip()
    m = re.search(r"```(?:cypher)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    # drop leading prose lines until a Cypher keyword
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if re.match(r"\s*(MATCH|OPTIONAL|WITH|CALL|UNWIND|RETURN)\b", ln, re.I):
            return "\n".join(lines[i:]).strip()
    return text


FORBIDDEN = re.compile(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD)\b",
                       re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="gold")
    ap.add_argument("--bench", default=DEFAULT_BENCH)
    ap.add_argument("--lang", choices=["en", "bn"], default="en")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--sleep", type=float, default=0.0,
                    help="seconds between model calls (rate limits)")
    ap.add_argument("--resume", action="store_true",
                    help="keep the results file and skip items already in it")
    args = ap.parse_args()
    BENCH, OUT = bench_paths(args.bench)

    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=True)  # project creds beat ambient AWS config  # AWS credentials for Bedrock adapters
    except ImportError:
        pass

    items = [json.loads(l) for l in
             open(BENCH / "benchmark.jsonl", encoding="utf-8")]
    if args.limit:
        items = items[:args.limit]
    schema = (BENCH / "schema.txt").read_text(encoding="utf-8")
    system = SYSTEM.format(schema=schema)
    adapter = make_adapter(args.adapter, region=args.region)

    # Results are written item by item, so an interruption loses nothing;
    # --resume skips the ids already in the file.
    OUT.mkdir(parents=True, exist_ok=True)
    tag = re.sub(r"[^A-Za-z0-9._-]", "_", args.adapter) + f"_{args.lang}"
    out_path = OUT / f"{tag}.jsonl"
    done = {}
    if args.resume and out_path.exists():
        for line in open(out_path, encoding="utf-8"):
            r = json.loads(line)
            done[r["id"]] = r
    results = [done[it["id"]] for it in items if it["id"] in done]
    f = open(out_path, "a" if args.resume else "w", encoding="utf-8")

    def emit(rec):
        results.append(rec)
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        f.flush()

    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        with driver.session(default_access_mode="READ") as s:
            for it in items:
                if it["id"] in done:
                    continue
                q = it["question_en"] if args.lang == "en" else it["question_bn"]
                base = {"id": it["id"], "category": it["category"],
                        "template_id": it["template_id"]}
                if isinstance(adapter, GoldAdapter):
                    adapter.current_item = it
                try:
                    raw = adapter.generate(system, q)
                except INFRA:
                    raise
                except Exception as e:
                    emit(dict(base, ok=False, valid=False, error=f"model:{e}"))
                    continue
                if isinstance(adapter, GoldAdapter):
                    d = json.loads(raw)
                    cypher, params = d["cypher"], d["params"]
                else:
                    cypher, params = extract_cypher(raw), {}
                rec = dict(base, cypher=cypher)
                if FORBIDDEN.search(cypher):
                    rec.update(ok=False, valid=False, error="write-clause")
                    emit(rec)
                    continue
                try:
                    got = [dict(r) for r in
                           s.run(Query(cypher, timeout=15), parameters=params)]
                    rec["valid"] = True
                except INFRA:
                    raise
                except Exception as e:
                    rec.update(ok=False, valid=False,
                               error=f"cypher:{str(e)[:200]}")
                    emit(rec)
                    continue
                rec["ok"] = compare(it["gold"], got)
                emit(rec)
                if args.sleep:
                    time.sleep(args.sleep)
    except INFRA as e:
        # a dead database or model server is not a wrong query: stop, so
        # an outage cannot be scored as model failures
        print(f"stopped after {len(results)} items: {type(e).__name__}: "
              f"{str(e)[:200]}\nrerun with --resume to continue")
        sys.exit(2)
    finally:
        f.close()
        driver.close()

    n = len(results)
    n_valid = sum(bool(r.get("valid")) for r in results)
    n_ok = sum(bool(r.get("ok")) for r in results)
    print(f"adapter={args.adapter} lang={args.lang} items={n}")
    print(f"valid-cypher rate: {n_valid}/{n} = {n_valid/n:.1%}")
    print(f"execution accuracy: {n_ok}/{n} = {n_ok/n:.1%}")
    by_cat = {}
    for r in results:
        c = r.get("category", "?")
        a, b = by_cat.get(c, (0, 0))
        by_cat[c] = (a + int(bool(r.get("ok"))), b + 1)
    for c, (a, b) in sorted(by_cat.items()):
        print(f"  {c:12s} {a}/{b} = {a/b:.1%}")


if __name__ == "__main__":
    main()
