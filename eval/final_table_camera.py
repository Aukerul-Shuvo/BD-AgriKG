"""Results table for the camera-ready from the re-scored v1 verdicts.

Reads eval/results/camera/bedrock_*.jsonl (written by rescore_v1_graders.py:
ok = corrected-grader strict verdict, ok_lenient = corrected-grader lenient
verdict, valid = ran without error) and writes final_table.tex and
final_summary.md in the same directory, in the format of eval/rescore.py so
that figs/make_results_fig.py can read them. The gap column is computed
from counts, not from the rounded percentages.

Usage: python eval/final_table_camera.py
"""
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "eval" / "results" / "camera"

SHORT = {
    "us.anthropic.claude-opus-5": "Claude Opus 5",
    "us.anthropic.claude-sonnet-5": "Claude Sonnet 5",
    "us.deepseek.r1-v1_0": "DeepSeek-R1",
    "us.mistral.pixtral-large-2502-v1_0": "Pixtral Large 25.02",
    "us.anthropic.claude-haiku-4-5-20251001-v1_0": "Claude Haiku 4.5",
    "us.meta.llama3-3-70b-instruct-v1_0": "Llama 3.3 70B",
    "us.meta.llama3-1-8b-instruct-v1_0": "Llama 3.1 8B",
}


def main():
    scores = {}
    for f in sorted(glob.glob(str(RES / "bedrock_*.jsonl"))):
        m = re.match(r"bedrock_(.+)_(en|bn)$", Path(f).stem)
        rows = [json.loads(l) for l in open(f, encoding="utf-8")]
        scores[m.groups()] = dict(
            n=len(rows),
            valid=sum(bool(r.get("valid")) for r in rows),
            strict=sum(bool(r.get("ok")) for r in rows),
            lenient=sum(bool(r.get("ok_lenient")) for r in rows))
    md = ["| model | lang | valid | strict | lenient |", "|---|---|---|---|---|"]
    tex = []
    for mid, label in SHORT.items():
        en, bn = scores.get((mid, "en")), scores.get((mid, "bn"))
        if not (en and bn):
            continue
        for lang, sc in (("en", en), ("bn", bn)):
            md.append(f"| {label} | {lang} | {sc['valid']/sc['n']:.1%} | "
                      f"**{sc['strict']/sc['n']:.1%}** | {sc['lenient']/sc['n']:.1%} |")
        gap = 100 * (en["strict"] - bn["strict"]) / en["n"]
        tex.append(f"{label} & {100*en['valid']/en['n']:.1f} & "
                   f"{100*en['strict']/en['n']:.1f} & {100*en['lenient']/en['n']:.1f} & "
                   f"{100*bn['valid']/bn['n']:.1f} & "
                   f"{100*bn['strict']/bn['n']:.1f} & {100*bn['lenient']/bn['n']:.1f} & "
                   f"{gap:+.1f} \\\\")
    (RES / "final_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (RES / "final_table.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    print("\n".join(tex))


if __name__ == "__main__":
    main()
