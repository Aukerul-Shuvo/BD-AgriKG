"""Run the full baseline sweep: every model x language, resumable.

Usage:
  python eval/run_all.py                # full sweep, skips finished configs
  python eval/run_all.py --limit 3      # smoke test every config
  python eval/run_all.py --only us.deepseek.r1-v1:0
Each config shells out to run_eval.py so a crash in one model never takes
down the sweep; a config is skipped when its result file already exists
(delete the file to re-run).
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"

# model id -> polite delay between calls (seconds), tuned for on-demand quota
MODELS = {
    "us.anthropic.claude-opus-5": 1.0,
    "us.anthropic.claude-sonnet-5": 1.0,
    "us.anthropic.claude-haiku-4-5-20251001-v1:0": 0.5,
    "us.meta.llama3-3-70b-instruct-v1:0": 0.5,
    "us.meta.llama3-1-8b-instruct-v1:0": 0.3,
    "us.mistral.pixtral-large-2502-v1:0": 1.0,
    "us.deepseek.r1-v1:0": 1.0,
}
LANGS = ["en", "bn"]


def tag_for(adapter, lang):
    return re.sub(r"[^A-Za-z0-9._-]", "_", adapter) + f"_{lang}.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    models = {m: s for m, s in MODELS.items()
              if not args.only or m == args.only}
    todo = [(m, l) for m in models for l in LANGS]
    print(f"{len(todo)} configs")
    failures = []
    for model, lang in todo:
        adapter = f"bedrock:{model}"
        out = RESULTS / tag_for(adapter, lang)
        if out.exists() and not args.limit:
            print(f"SKIP (done)  {model} {lang}")
            continue
        cmd = [sys.executable, str(ROOT / "eval" / "run_eval.py"),
               "--adapter", adapter, "--lang", lang,
               "--sleep", str(models[model])]
        if args.limit:
            cmd += ["--limit", str(args.limit)]
        print(f"RUN  {model} {lang}" + (f" (limit {args.limit})" if args.limit else ""))
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            failures.append((model, lang))
            print(f"FAILED  {model} {lang}")
    if failures:
        print("\nfailed configs:", failures)
        sys.exit(1)
    print("\nall configs finished")


if __name__ == "__main__":
    main()
