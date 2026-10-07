"""Build the native-speaker validation sheet.

For each of the 26 templates it shows up to three released items chosen to
differ in the substituted crop, so that case-ending errors introduced by
mechanical substitution (genitive -er/-r, locative -e/-y/-te) are visible.
Templates that the cross-family adequacy check flagged are marked and
sorted first, so the reviewer's attention goes where the risk is.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATS = ["lookup", "aggregation", "ranking", "temporal", "comparison", "multihop"]

items = [json.loads(l) for l in open(ROOT / "benchmark/v1/benchmark.jsonl",
                                    encoding="utf-8")]
adq = ROOT / "eval/results/bangla_adequacy.jsonl"
flagged = Counter()
if adq.exists():
    for l in open(adq, encoding="utf-8"):
        r = json.loads(l)
        if r.get("same") is not True:
            flagged[r["template_id"]] += 1

by_t = defaultdict(list)
for it in items:
    by_t[it["template_id"]].append(it)

# Bangla question words that fix the expected answer type
ANSWER_WORDS = {
    "কয়টি": "how many (expects a count)",
    "কতটি": "how many (expects a count)",
    "কত": "how much (expects a quantity)",
    "কোন কোন": "which ones (expects a list)",
    "কোনটি": "which one (expects a single item)",
    "তিনটি": "three (expects exactly three)",
    "সবচেয়ে বেশি": "the highest",
    "সবচেয়ে": "the most",
    "হেক্টর প্রতি": "per hectare",
    "একর প্রতি": "per acre",
    "অত্যন্ত": "highly",
    "প্রধান": "main or top",
}


def pick(rows, n=3):
    """Up to n items differing in the substituted crop where possible."""
    seen, out = set(), []
    for r in rows:
        c = (r.get("params") or {}).get("crop") or \
            (r.get("params") or {}).get("crop1") or ""
        if c not in seen:
            seen.add(c)
            out.append(r)
        if len(out) == n:
            break
    while len(out) < min(n, len(rows)):
        for r in rows:
            if r not in out:
                out.append(r)
                break
    return out


order = sorted(by_t, key=lambda t: (-flagged[t],
                                    CATS.index(by_t[t][0]["category"]), t))

md = ["# Bangla validation sheet (26 templates)", "",
      "Rows the automatic check flagged are first and marked **CHECK**.",
      "Each template shows up to three items with different crops, so that a",
      "wrong case ending on a substituted crop name is visible.", "",
      "For each template fill in:", "",
      "- **Fluency**: 1 unnatural, 2 acceptable, 3 natural.",
      "- **Adequacy**: does the Bangla ask exactly what the English asks?",
      "  yes, or no plus what differs.",
      "- **Correction**: the Bangla you would write instead.", "",
      "Latin-script place names, years and pest names are deliberate; do not",
      "flag those. Crop names should always be in Bangla.", "",
      "## What fixes the expected answer type", "",
      "| Bangla | meaning |", "|---|---|"]
for k, v in ANSWER_WORDS.items():
    md.append(f"| {k} | {v} |")
md += ["", "---", ""]

for i, t in enumerate(order, 1):
    rows = by_t[t]
    cat = rows[0]["category"]
    mark = f" **CHECK ({flagged[t]} of {len(rows)} flagged)**" if flagged[t] else ""
    md.append(f"### {i}. `{t}` ({cat}, n={len(rows)}){mark}")
    md.append("")
    hits = [f"`{k}`" for k in ANSWER_WORDS if k in rows[0]["question_bn"]]
    if hits:
        md.append(f"Answer-type words present: {', '.join(hits)}")
        md.append("")
    md.append("| | English | Bangla |")
    md.append("|---|---|---|")
    for r in pick(rows):
        en = r["question_en"].replace("|", "\\|")
        bn = r["question_bn"].replace("|", "\\|")
        md.append(f"| {r['id']} | {en} | {bn} |")
    md += ["", "Fluency (1-3): ", "", "Adequacy (yes / no + what differs): ",
           "", "Correction: ", "", "---", ""]

out = ROOT / "benchmark/v1/bangla_validation_sheet.md"
out.write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"wrote {out}")
print(f"{len(order)} templates, {sum(flagged.values())} flagged items "
      f"across {len(flagged)} templates")
print("flagged first:", [t for t in order if flagged[t]])
