"""Generate the BD-AgriKG Text2Cypher benchmark from the live Neo4j graph.

Cypher-first: for each template, sample parameter rows via its sampler
query, execute the gold Cypher, and keep only items whose gold answer is
non-empty and reasonably sized. Writes benchmark/v1/benchmark.jsonl and a
schema description for prompting.

Usage: python benchmark/generate_benchmark.py [--per-template 18] [--seed 7]
"""
import argparse
import json
import random
import sys
from pathlib import Path

from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent))
from templates import (TEMPLATES, CROP_BN, CROP_BN_GEN, CROP_BN_LOC)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark" / "v1"

URI, AUTH = "bolt://localhost:7687", ("neo4j", "bdagrikg2026")

SCHEMA = """\
Node labels and properties:
- Division {pcode, name}
- District {pcode, name}
- Upazila {pcode, name, area_sqkm, center_lat, center_lon}
- Crop {name, sowing_time, harvest_time, seed_requirement_per_acre,
        favourable_temperature, favourable_humidity,
        favourable_soil_temperature, photo_period, favourable_rainfall,
        water_requirement}
- SoilType {name}
- PestDisease {name}

Relationships:
- (Upazila)-[:IN_DISTRICT]->(District)
- (District)-[:IN_DIVISION]->(Division)
- (Crop)-[:SUITABLE_IN {very_suitable, suitable, moderately_suitable,
   marginally_suitable, not_suitable, total_area, zone, suitability_factor}]
  ->(Upazila)   // BARC land-suitability areas in hectares; factor 0..1
- (Upazila)-[:HAS_SOIL {characteristics}]->(SoilType)
- (Crop)-[:AFFECTED_BY {conditions}]->(PestDisease)
- (Crop)-[:PRODUCED_IN {crop_year, area_acres, production_mt,
   yield_mt_per_ha, source, quality_flag}]->(District)
  // BBS district production; crop_year like '2023-24', 2013-14..2024-25

The 16 crops: Aus, Aman, Boro, Wheat, Maize, Potato, Lentil, Mung, Gram,
Mustard, Groundnut, Chili, Onion, Garlic, Sugarcane, Jute.
District names use current spellings (Bogura, Chattogram, Jashore,
Chapainababganj, Barishal, Cumilla, ...).
A crop is called "highly suitable" in a place when suitability_factor > 0.7."""


def render(tpl_text, params):
    fmt = dict(params)
    for k, v in list(params.items()):
        if isinstance(v, str) and v in CROP_BN:
            fmt[k + "_bn"] = CROP_BN[v]
            fmt[k + "_bn_gen"] = CROP_BN_GEN[v]
            fmt[k + "_bn_loc"] = CROP_BN_LOC[v]
    return tpl_text.format(**fmt)


def jsonable(v):
    if isinstance(v, float):
        return round(v, 4)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-template", type=int, default=18)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    random.seed(args.seed)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    items, stats = [], {}
    with driver.session() as s:
        for tpl in TEMPLATES:
            cand = [dict(r) for r in s.run(tpl["sampler"])]
            random.shuffle(cand)
            kept = 0
            seen_questions = set()
            for params in cand:
                if kept >= args.per_template:
                    break
                guard = tpl.get("guard")
                if guard is not None:
                    try:
                        grows = [dict(r) for r in s.run(guard[0], **params)]
                    except Exception:
                        continue
                    if not guard[1](grows):
                        continue  # tie at the cut-off, or quality guard failed
                try:
                    result = [dict(r) for r in s.run(tpl["cypher"], **params)]
                except Exception:
                    continue
                # reject degenerate golds
                if not result or len(result) > 40:
                    continue
                vals = [v for r in result for v in r.values()]
                if all(v is None or v == "" or v == 0 for v in vals):
                    continue
                q_en = render(tpl["en"], params)
                if q_en in seen_questions:
                    continue
                seen_questions.add(q_en)
                items.append({
                    "id": f"{tpl['id']}-{kept:03d}",
                    "template_id": tpl["id"],
                    "category": tpl["category"],
                    "difficulty": tpl["difficulty"],
                    "question_en": q_en,
                    "question_bn": render(tpl["bn"], params),
                    "params": params,
                    "cypher": tpl["cypher"],
                    "gold": [{k: jsonable(v) for k, v in r.items()}
                             for r in result],
                })
                kept += 1
            stats[tpl["id"]] = kept
    driver.close()

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "benchmark.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False, default=str) + "\n")
    (OUT / "schema.txt").write_text(SCHEMA, encoding="utf-8")

    print(f"{len(items)} items written to {OUT / 'benchmark.jsonl'}")
    by_cat = {}
    for it in items:
        by_cat[it["category"]] = by_cat.get(it["category"], 0) + 1
    print("by category:", by_cat)
    short = {k: v for k, v in stats.items() if v < args.per_template}
    if short:
        print("templates below quota:", short)


if __name__ == "__main__":
    main()
