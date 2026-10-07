"""Cross-family adequacy check of the Bangla questions.

Back-translate every Bangla question to English with one non-Claude model
(Mistral Large), then let a second non-Claude model (Llama 3.3 70B) judge
whether the back-translation asks the same thing as the original English
question. The translator is given the benchmark's own 16-entry crop-name
glossary so that the check tests sentence meaning, not vocabulary recall.
Writes eval/results/bangla_adequacy.jsonl and prints a per-template
summary. This complements, and does not replace, a native-speaker review.
"""
import concurrent.futures as cf
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "benchmark"))
import clockskew  # noqa: F401,E402
from adapters import BedrockConverseAdapter  # noqa: E402
from templates import CROP_BN  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except ImportError:
    pass

OUT = ROOT / "eval/results/bangla_adequacy.jsonl"
TRANSLATOR = "us.mistral.pixtral-large-2502-v1:0"
JUDGE = "us.meta.llama3-3-70b-instruct-v1:0"

GLOSSARY = "; ".join(f"{bn} = {en}" for en, bn in CROP_BN.items())
T_SYS = ("You are a professional Bangla-to-English translator. Translate the "
         "question faithfully and literally. Keep Latin-script names and "
         "years exactly as written. Use these crop-name equivalents: "
         + GLOSSARY + ". Output only the English translation.")
J_SYS = ("You compare two English questions and decide whether they ask for "
         "exactly the same thing: same entities (crop, place, year), same "
         "quantity or attribute, same constraints (e.g. highest, per hectare, "
         "three crops). Minor wording differences do not matter. Answer with "
         "one JSON object only: {\"same\": true or false, \"issue\": \"short "
         "reason if false, else empty\"}.")


def parse_verdict(text):
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            js = json.loads(m.group(0))
            if isinstance(js.get("same"), bool):
                return js["same"], str(js.get("issue", ""))
        except Exception:
            pass
    m = re.search(r'"?same"?\s*:\s*(true|false)', text, re.I)
    if m:
        return m.group(1).lower() == "true", text[:200]
    return None, text[:200]


def one(item, tr, jd):
    bn, en = item["question_bn"], item["question_en"]
    try:
        bt = tr.generate(T_SYS, bn).strip()
        verdict = jd.generate(
            J_SYS, f"Question A (original): {en}\nQuestion B (back-translated "
                   f"from Bangla): {bt}\nJSON:")
        same, issue = parse_verdict(verdict)
    except Exception as e:
        bt, verdict, same, issue = "", "", None, f"error: {e}"[:200]
    return {"id": item["id"], "template_id": item["template_id"],
            "question_en": en, "question_bn": bn, "back_translation": bt,
            "same": same, "issue": issue, "raw_verdict": verdict[:400]}


def run_items(items, tr, jd, mode="a"):
    with open(OUT, mode, encoding="utf-8") as f, \
            cf.ThreadPoolExecutor(max_workers=4) as ex:
        for rec in ex.map(lambda it: one(it, tr, jd), items):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()


def main():
    items = [json.loads(l) for l in open(ROOT / "benchmark/v1/benchmark.jsonl",
                                         encoding="utf-8")]
    by_id = {it["id"]: it for it in items}
    tr = BedrockConverseAdapter(TRANSLATOR, max_tokens=300)
    jd = BedrockConverseAdapter(JUDGE, max_tokens=200)
    t0 = time.time()
    if OUT.exists():
        OUT.unlink()
    print(f"{len(items)} items to check")
    run_items(items, tr, jd, "w")
    # one retry pass for rows without a usable verdict
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8")]
    redo = [by_id[r["id"]] for r in rows if r["same"] is None]
    if redo:
        print(f"retrying {len(redo)} rows without a verdict")
        keep = [r for r in rows if r["same"] is not None]
        with open(OUT, "w", encoding="utf-8") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        run_items(redo, tr, jd, "a")
    print(f"done in {time.time()-t0:.0f}s")

    rows = [json.loads(l) for l in open(OUT, encoding="utf-8")]
    by_t = defaultdict(lambda: [0, 0, []])
    for r in rows:
        b = by_t[r["template_id"]]
        b[1] += 1
        if r["same"] is True:
            b[0] += 1
        else:
            b[2].append((r["id"], r["issue"]))
    tot_same = sum(b[0] for b in by_t.values())
    print(f"\nadequate {tot_same}/{len(rows)} = {100*tot_same/len(rows):.1f}%")
    for t, (s, n, bad) in sorted(by_t.items(), key=lambda kv: kv[1][0] / kv[1][1]):
        flag = "" if s == n else f"  <-- {n - s} flagged"
        print(f"{t:32s} {s:2d}/{n:2d}{flag}")
        for iid, issue in bad[:3]:
            print(f"      {iid}: {str(issue)[:120]}")


if __name__ == "__main__":
    main()
