"""Live progress bar for a running evaluation sweep.

Reads the results file run_eval writes item by item; it never touches the
model or the database, so watching does not slow the sweep. Stop with
Ctrl+C at any time.

Usage:
  python eval/watch_progress.py                 # newest file in eval/results/v2
  python eval/watch_progress.py path/to/results.jsonl
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results" / "v2"
BENCH = ROOT / "benchmark" / "v2" / "benchmark.jsonl"
WIDTH = 30


def counts(path):
    n = valid = ok = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:   # a line still being written
                continue
            n += 1
            valid += bool(r.get("valid"))
            ok += bool(r.get("ok"))
    return n, valid, ok


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        runs = [p for p in RESULTS.glob("*.jsonl") if not p.name.startswith("gold")]
        path = max(runs, key=lambda p: p.stat().st_mtime)
    total = sum(1 for _ in open(BENCH, encoding="utf-8"))
    started = path.stat().st_ctime      # creation time on Windows
    print(f"watching {path.name}  (Ctrl+C to stop)")
    while True:
        n, valid, ok = counts(path)
        elapsed = time.time() - started
        rate = elapsed / n if n else 0
        eta = rate * (total - n)
        bar = "#" * int(WIDTH * n / total) + "-" * (WIDTH - int(WIDTH * n / total))
        line = (f"\r[{bar}] {n}/{total} {100 * n / total:5.1f}%  "
                f"correct {ok} ({100 * ok / max(n, 1):.1f}%)  valid {valid}  "
                f"{rate:4.1f}s/item  ETA {int(eta // 60):3d} min ")
        print(line, end="", flush=True)
        if n >= total:
            print("\ndone")
            return
        time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
