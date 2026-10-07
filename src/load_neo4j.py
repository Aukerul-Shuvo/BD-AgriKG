"""Load data/processed/kg/*.csv into Neo4j. Idempotent (MERGE on keys).

Usage: python src/load_neo4j.py [--wipe]
Env: NEO4J_URI (default bolt://localhost:7687), NEO4J_USER, NEO4J_PASSWORD.
"""
import os
import sys
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
# KG_DIR lets an older snapshot of the CSVs be loaded (used to re-score the
# NORA runs on the graph exactly as it was evaluated).
KG = Path(os.environ.get("KG_DIR") or ROOT / "data" / "processed" / "kg")

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USER = os.environ.get("NEO4J_USER", "neo4j")
PWD = os.environ.get("NEO4J_PASSWORD", "bdagrikg2026")

CONSTRAINTS = [
    "CREATE CONSTRAINT division_pcode IF NOT EXISTS FOR (n:Division) REQUIRE n.pcode IS UNIQUE",
    "CREATE CONSTRAINT district_pcode IF NOT EXISTS FOR (n:District) REQUIRE n.pcode IS UNIQUE",
    "CREATE CONSTRAINT upazila_pcode IF NOT EXISTS FOR (n:Upazila) REQUIRE n.pcode IS UNIQUE",
    "CREATE CONSTRAINT crop_name IF NOT EXISTS FOR (n:Crop) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT pest_name IF NOT EXISTS FOR (n:PestDisease) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT soil_name IF NOT EXISTS FOR (n:SoilType) REQUIRE n.name IS UNIQUE",
    # One observation per district-month. The composite key is also what
    # makes the MERGE below cheap: without it each of the ~10k merges would
    # scan every WeatherMonth node.
    "CREATE CONSTRAINT weather_key IF NOT EXISTS FOR (n:WeatherMonth) "
    "REQUIRE (n.district_pcode, n.year, n.month) IS UNIQUE",
    "CREATE CONSTRAINT nutrient_symbol IF NOT EXISTS FOR (n:Nutrient) "
    "REQUIRE n.symbol IS UNIQUE",
    "CREATE CONSTRAINT variety_name IF NOT EXISTS FOR (n:Variety) "
    "REQUIRE n.name IS UNIQUE",
]

NUTRIENT_NAMES = {"N": "Nitrogen", "P": "Phosphorus", "K": "Potassium",
                  "S": "Sulphur", "Zn": "Zinc", "B": "Boron",
                  "Mo": "Molybdenum", "Mg": "Magnesium"}


def rows(name):
    df = pd.read_csv(KG / name)
    # cast to object first, otherwise None reverts to NaN in float columns
    # and reaches Neo4j as a NaN property instead of a missing one
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict("records")


def run_batch(session, query, records, batch=500):
    for i in range(0, len(records), batch):
        session.run(query, rows=records[i:i + batch])


def main():
    wipe = "--wipe" in sys.argv
    driver = GraphDatabase.driver(URI, auth=(USER, PWD))
    with driver.session() as s:
        if wipe:
            s.run("MATCH (n) DETACH DELETE n")
        for c in CONSTRAINTS:
            s.run(c)

        run_batch(s, """
            UNWIND $rows AS r
            MERGE (n:Division {pcode: r.pcode}) SET n.name = r.name
        """, rows("divisions.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MERGE (n:District {pcode: r.pcode}) SET n.name = r.name
            WITH n, r MATCH (d:Division {pcode: r.division_pcode})
            MERGE (n)-[:IN_DIVISION]->(d)
        """, rows("districts.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MERGE (n:Upazila {pcode: r.pcode})
            SET n.name = r.name, n.area_sqkm = r.area_sqkm,
                n.lat = r.center_lat, n.lon = r.center_lon
            WITH n, r MATCH (d:District {pcode: r.district_pcode})
            MERGE (n)-[:IN_DISTRICT]->(d)
        """, rows("upazilas.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MERGE (c:Crop {name: r.name})
            SET c.sowing_time = r.sowing_time, c.harvest_time = r.harvest_time,
                c.seed_requirement_per_acre = r.seed_requirement_per_acre,
                c.favourable_temperature = r.favourable_temperature,
                c.favourable_humidity = r.favourable_humidity,
                c.favourable_soil_temperature = r.favourable_soil_temperature,
                c.photo_period = r.photo_period,
                c.favourable_rainfall = r.favourable_rainfall,
                c.water_requirement = r.water_requirement
        """, rows("crops.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MATCH (c:Crop {name: r.crop}), (u:Upazila {pcode: r.upazila_pcode})
            MERGE (c)-[x:SUITABLE_IN]->(u)
            SET x.very_suitable = r.very_suitable, x.suitable = r.suitable,
                x.moderately_suitable = r.moderately_suitable,
                x.marginally_suitable = r.marginally_suitable,
                x.not_suitable = r.not_suitable, x.total_area = r.total_area,
                x.zone = r.zone, x.suitability_factor = r.suitability_factor,
                x.source = 'BARC crop zoning', x.barc_source_name = r.barc_source_name,
                x.source_span = r.source_span
        """, rows("suitability.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MERGE (n:SoilType {name: r.name})
        """, rows("soil_types.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MATCH (u:Upazila {pcode: r.upazila_pcode}), (t:SoilType {name: r.soil_type})
            MERGE (u)-[x:HAS_SOIL]->(t)
            SET x.characteristics = r.characteristics, x.source = 'SRDI'
        """, rows("upazila_soil.csv"))

        if (KG / "production.csv").exists():
            run_batch(s, """
                UNWIND $rows AS r
                MATCH (c:Crop {name: r.crop}), (d:District {pcode: r.district_pcode})
                MERGE (c)-[x:PRODUCED_IN {crop_year: r.crop_year}]->(d)
                SET x.area_acres = r.area_acres,
                    x.production_mt = r.production_mt,
                    x.yield_mt_per_ha = r.yield_mt_per_ha,
                    x.source = 'BBS Yearbook ' + toString(r.edition_used),
                    x.quality_flag = r.flag
            """, [r for r in rows("production.csv")
                  if r["production_mt"] and r["production_mt"] > 0])

        run_batch(s, """
            UNWIND $rows AS r
            MERGE (n:PestDisease {name: r.name})
        """, rows("pests.csv"))

        run_batch(s, """
            UNWIND $rows AS r
            MATCH (c:Crop {name: r.crop}), (p:PestDisease {name: r.pest})
            MERGE (c)-[x:AFFECTED_BY]->(p)
            SET x.conditions = r.conditions, x.source = r.source
        """, [dict(r, source=r.get("source") or "BAMIS")
              for r in rows("crop_pest.csv")])

        # Monthly agro-meteorology per district, reified as observation
        # nodes rather than edge properties: unlike PRODUCED_IN there is no
        # second entity for the measurement to connect, and a node keeps
        # each month addressable by year and month directly.
        if (KG / "weather_monthly.csv").exists():
            run_batch(s, """
                UNWIND $rows AS r
                MATCH (d:District {pcode: r.district_pcode})
                MERGE (w:WeatherMonth {district_pcode: r.district_pcode,
                                       year: toInteger(r.year),
                                       month: toInteger(r.month)})
                SET w.rainfall_mm = r.rainfall_mm_month,
                    w.rainfall_mm_per_day = r.rainfall_mm_per_day,
                    w.temp_mean_c = r.temp_mean_c,
                    w.temp_max_c = r.temp_max_c,
                    w.temp_min_c = r.temp_min_c,
                    w.humidity_pct = r.humidity_pct,
                    w.source = 'NASA POWER'
                MERGE (d)-[:OBSERVED]->(w)
            """, rows("weather_monthly.csv"), batch=1000)

        # Agriculture Census 2019 holdings, as properties on the admin units
        # themselves rather than separate nodes: there is exactly one census
        # and one row per unit, so a node would add a hop for nothing.
        if (KG / "census_holdings.csv").exists():
            cen = rows("census_holdings.csv")
            run_batch(s, """
                UNWIND $rows AS r
                MATCH (d:District {name: r.district})
                SET d.census_holdings_total = r.all_holdings,
                    d.census_farm_holdings = r.farm_total,
                    d.census_farm_small = r.farm_small_005_249,
                    d.census_farm_medium = r.farm_medium_250_749,
                    d.census_farm_large = r.farm_large_750_plus,
                    d.census_source = 'BBS Agriculture Census 2019'
            """, [r for r in cen if r["level"] == "district"])
            run_batch(s, """
                UNWIND $rows AS r
                MATCH (d:District {name: r.district})<-[:IN_DISTRICT]-
                      (u:Upazila {name: r.upazila})
                SET u.census_holdings_total = r.all_holdings,
                    u.census_farm_holdings = r.farm_total,
                    u.census_farm_small = r.farm_small_005_249,
                    u.census_farm_medium = r.farm_medium_250_749,
                    u.census_farm_large = r.farm_large_750_plus,
                    u.census_source = 'BBS Agriculture Census 2019'
            """, [r for r in cen if r["level"] == "upazila"])

        # BARC fertilizer doses. A crop has several variety groups, each with
        # four soil-fertility classes, so one Crop-Nutrient pair carries many
        # edges; the MERGE key is the full (group, class) combination.
        if (KG / "fertilizer_doses.csv").exists():
            fert = rows("fertilizer_doses.csv")
            run_batch(s, """
                UNWIND $rows AS r
                MERGE (n:Nutrient {symbol: r.symbol}) SET n.name = r.name
            """, [{"symbol": k, "name": v} for k, v in NUTRIENT_NAMES.items()
                  if k in {f["nutrient"] for f in fert}])
            run_batch(s, """
                UNWIND $rows AS r
                MATCH (c:Crop {name: r.crop}), (n:Nutrient {symbol: r.nutrient})
                MERGE (c)-[x:RECOMMENDED_DOSE {
                    variety_group: toInteger(r.variety_group),
                    fertility_class: r.fertility_class}]->(n)
                SET x.min_kg_ha = r.dose_min_kg_ha,
                    x.max_kg_ha = r.dose_max_kg_ha,
                    x.yield_goal_t_ha = r.yield_goal_t_ha,
                    x.source = 'BARC Fertilizer Recommendation Guide 2024'
            """, fert)

        # BARI released varieties, as nodes: a variety is an entity in its
        # own right with a name, release year and yield, not a measurement.
        # Yield and duration are left null where the source gives several
        # ranges (by season, green and dry); the printed text is kept.
        if (KG / "varieties.csv").exists():
            run_batch(s, """
                UNWIND $rows AS r
                MATCH (c:Crop {name: r.crop})
                MERGE (v:Variety {name: r.name_en})
                SET v.name_bn = r.name_bn,
                    v.release_year = toInteger(r.release_year),
                    v.registration = r.registration,
                    v.yield_min_t_ha = r.yield_min_t_ha,
                    v.yield_max_t_ha = r.yield_max_t_ha,
                    v.yield_text_bn = r.yield_text,
                    v.duration_min_days = toInteger(r.duration_min_days),
                    v.duration_max_days = toInteger(r.duration_max_days),
                    v.duration_text_bn = r.duration_text,
                    v.traits_bn = r.traits,
                    v.bari_serial = toInteger(r.serial),
                    v.source = 'BARI Fashol O Jat Porichiti 2025'
                MERGE (v)-[:VARIETY_OF]->(c)
            """, rows("varieties.csv"))

        counts = s.run("""
            MATCH (n) WITH labels(n)[0] AS l, count(*) AS c
            RETURN l, c ORDER BY l
        """).data()
        rels = s.run("""
            MATCH ()-[r]->() WITH type(r) AS t, count(*) AS c
            RETURN t, c ORDER BY t
        """).data()
        print("nodes:", {d["l"]: d["c"] for d in counts})
        print("rels:", {d["t"]: d["c"] for d in rels})
    driver.close()


if __name__ == "__main__":
    main()
