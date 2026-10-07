"""Re-run adequacy rows that have no verdict (throttled), one at a time."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from bangla_adequacy_check import OUT, TRANSLATOR, JUDGE, one  # noqa: E402
from adapters import BedrockConverseAdapter  # noqa: E402

items = {json.loads(l)["id"]: json.loads(l)
         for l in open(ROOT / "benchmark/v1/benchmark.jsonl", encoding="utf-8")}
tr = BedrockConverseAdapter(TRANSLATOR, max_tokens=300)
jd = BedrockConverseAdapter(JUDGE, max_tokens=200)
for attempt in range(4):
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8")]
    todo = [r for r in rows if r["same"] is None]
    print(f"pass {attempt+1}: {len(todo)} rows without verdict")
    if not todo:
        break
    fixed = {}
    for r in todo:
        fixed[r["id"]] = one(items[r["id"]], tr, jd)
        time.sleep(1.0)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(fixed.get(r["id"], r), ensure_ascii=False) + "\n")
rows = [json.loads(l) for l in open(OUT, encoding="utf-8")]
from collections import Counter
print("final:", dict(Counter(r["same"] for r in rows)))
