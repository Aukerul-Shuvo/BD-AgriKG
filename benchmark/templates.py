"""Question-Cypher templates for the BD-AgriKG Text2Cypher benchmark.

Each template has:
  id, category, difficulty (1-3),
  sampler:  Cypher returning candidate parameter rows from the live KG,
  cypher:   the gold query with $params,
  en / bn:  question surface forms (python format strings over the params).

Design rules:
- Cypher-first: gold queries are written and executed first; questions are
  rendered from the sampled parameters, so every item has an executable,
  non-empty gold answer.
- Upazila-parameterised templates sample only upazilas whose name is unique
  nationwide, or carry the district in the question, so questions are
  unambiguous.
- Bangla questions use Bangla crop names (standard usage) but keep
  district/upazila names and years in Latin script, matching how Bangladeshi
  extension workers actually type.
"""

CROP_BN = {
    "Aus": "আউশ ধান", "Aman": "আমন ধান", "Boro": "বোরো ধান",
    "Wheat": "গম", "Maize": "ভুট্টা", "Potato": "আলু",
    "Lentil": "মসুর", "Mung": "মুগ", "Gram": "ছোলা",
    "Mustard": "সরিষা", "Groundnut": "চীনাবাদাম", "Chili": "মরিচ",
    "Onion": "পেঁয়াজ", "Garlic": "রসুন", "Sugarcane": "আখ", "Jute": "পাট",
}

# inflected genitive (X-er) forms, standard orthography joins the ending
CROP_BN_GEN = {
    "Aus": "আউশ ধানের", "Aman": "আমন ধানের", "Boro": "বোরো ধানের",
    "Wheat": "গমের", "Maize": "ভুট্টার", "Potato": "আলুর",
    "Lentil": "মসুরের", "Mung": "মুগের", "Gram": "ছোলার",
    "Mustard": "সরিষার", "Groundnut": "চীনাবাদামের", "Chili": "মরিচের",
    "Onion": "পেঁয়াজের", "Garlic": "রসুনের", "Sugarcane": "আখের",
    "Jute": "পাটের",
}

# locative (X-e/te) forms for "attacks on <crop>"
CROP_BN_LOC = {
    "Aus": "আউশ ধানে", "Aman": "আমন ধানে", "Boro": "বোরো ধানে",
    "Wheat": "গমে", "Maize": "ভুট্টায়", "Potato": "আলুতে",
    "Lentil": "মসুরে", "Mung": "মুগে", "Gram": "ছোলায়",
    "Mustard": "সরিষায়", "Groundnut": "চীনাবাদামে", "Chili": "মরিচে",
    "Onion": "পেঁয়াজে", "Garlic": "রসুনে", "Sugarcane": "আখে",
    "Jute": "পাটে",
}

# samplers shared by several templates
ANY_CROP = "MATCH (c:Crop) RETURN c.name AS crop"
CROP_YEAR = """
    MATCH (c:Crop)-[p:PRODUCED_IN]->() WHERE p.production_mt > 0
    RETURN DISTINCT c.name AS crop, p.crop_year AS year
"""
CROP_DIST_YEAR = """
    MATCH (c:Crop)-[p:PRODUCED_IN]->(d:District)
    WHERE p.production_mt > 1000
    RETURN c.name AS crop, d.name AS district, p.crop_year AS year
"""
UNIQUE_UPAZILA = """
    MATCH (u:Upazila)-[:IN_DISTRICT]->(d:District)
    WITH u.name AS upazila, collect(d.name) AS ds
    WHERE size(ds) = 1 AND NOT upazila STARTS WITH ds[0]
    RETURN upazila
"""

TEMPLATES = [
    # ---------- lookup (single fact) ----------
    dict(id="sowing_time", category="lookup", difficulty=1,
         sampler=ANY_CROP,
         cypher="MATCH (c:Crop {name: $crop}) RETURN c.sowing_time AS answer",
         en="When is {crop} sown, planted or transplanted in Bangladesh?",
         bn="বাংলাদেশে {crop_bn} কখন বপন বা রোপণ করা হয়?"),
    dict(id="harvest_time", category="lookup", difficulty=1,
         sampler=ANY_CROP,
         cypher="MATCH (c:Crop {name: $crop}) RETURN c.harvest_time AS answer",
         en="When is {crop} harvested?",
         bn="{crop_bn} কখন ঘরে তোলা হয়?"),
    dict(id="seed_req", category="lookup", difficulty=1,
         sampler=ANY_CROP,
         cypher="MATCH (c:Crop {name: $crop}) "
                "RETURN c.seed_requirement_per_acre AS answer",
         en="How much seed or planting material is needed per acre for {crop}?",
         bn="{crop_bn} চাষে একর প্রতি কী পরিমাণ বীজ লাগে?"),
    dict(id="water_req", category="lookup", difficulty=1,
         sampler=ANY_CROP,
         cypher="MATCH (c:Crop {name: $crop}) "
                "RETURN c.water_requirement AS answer",
         en="What is the water requirement of {crop}?",
         bn="{crop_bn} চাষে পানির চাহিদা কেমন?"),
    dict(id="upazila_district", category="lookup", difficulty=1,
         sampler=UNIQUE_UPAZILA,
         cypher="MATCH (u:Upazila {name: $upazila})-[:IN_DISTRICT]->(d) "
                "RETURN d.name AS answer",
         en="Which district is {upazila} upazila in?",
         bn="{upazila} উপজেলা কোন জেলায় অবস্থিত?"),
    dict(id="upazila_soils", category="lookup", difficulty=1,
         sampler="""MATCH (u:Upazila)-[:HAS_SOIL]->()
                    WITH u, count(*) AS s
                    MATCH (x:Upazila) WHERE x.name = u.name
                    WITH u, s, count(x) AS n WHERE n = 1 AND s >= 2
                    RETURN u.name AS upazila""",
         cypher="MATCH (u:Upazila {name: $upazila})-[:HAS_SOIL]->(s) "
                "RETURN s.name AS answer ORDER BY s.name",
         en="What soil types are found in {upazila} upazila?",
         bn="{upazila} উপজেলায় কোন কোন ধরনের মাটি পাওয়া যায়?"),
    dict(id="pest_conditions", category="lookup", difficulty=2,
         sampler="""MATCH (c:Crop)-[a:AFFECTED_BY]->(p:PestDisease)
                    WHERE a.conditions <> ''
                    RETURN c.name AS crop, p.name AS pest""",
         cypher="MATCH (:Crop {name: $crop})-[a:AFFECTED_BY]->"
                "(:PestDisease {name: $pest}) RETURN a.conditions AS answer",
         en="Under what conditions does {pest} attack {crop}?",
         bn="কোন অবস্থায় {crop_bn_loc} {pest} আক্রমণ করে?"),

    # ---------- aggregation ----------
    dict(id="count_upazilas", category="aggregation", difficulty=1,
         sampler="""MATCH (d:District)
                    WHERE NOT EXISTS {
                        MATCH (u:Upazila)-[:IN_DISTRICT]->(d)
                        WHERE u.name ENDS WITH 'City Corporation'
                    }
                    RETURN d.name AS district""",
         cypher="MATCH (u:Upazila)-[:IN_DISTRICT]->(:District {name: $district}) "
                "RETURN count(u) AS answer",
         en="How many upazilas are there in {district} district?",
         bn="{district} জেলায় কয়টি উপজেলা আছে?"),
    dict(id="count_crops_pest", category="aggregation", difficulty=1,
         sampler="MATCH (:Crop)-[:AFFECTED_BY]->(p:PestDisease) "
                 "RETURN DISTINCT p.name AS pest",
         cypher="MATCH (c:Crop)-[:AFFECTED_BY]->(:PestDisease {name: $pest}) "
                "RETURN count(c) AS answer",
         en="How many crops are attacked by {pest}?",
         bn="{pest} কয়টি ফসলে আক্রমণ করে?"),
    dict(id="national_production", category="aggregation", difficulty=2,
         sampler=CROP_YEAR,
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->() RETURN sum(p.production_mt) AS answer",
         en="What was the total national production of {crop} in {year}?",
         bn="{year} সালে সারা দেশে {crop_bn_gen} মোট উৎপাদন কত ছিল?"),
    dict(id="count_producing_districts", category="aggregation", difficulty=2,
         sampler=CROP_YEAR,
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(d:District) RETURN count(d) AS answer",
         en="In how many districts was {crop} produced in {year}?",
         bn="{year} সালে কতটি জেলায় {crop_bn} উৎপাদিত হয়েছিল?"),
    dict(id="division_production", category="aggregation", difficulty=3,
         sampler="""MATCH (c:Crop)-[p:PRODUCED_IN]->(:District)-[:IN_DIVISION]
                    ->(v:Division) WHERE p.production_mt > 0
                    RETURN DISTINCT c.name AS crop, p.crop_year AS year,
                           v.name AS division""",
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(:District)-[:IN_DIVISION]->(:Division {name: $division}) "
                "RETURN sum(p.production_mt) AS answer",
         en="How much {crop} was produced in {division} division in {year}?",
         bn="{year} সালে {division} বিভাগে কত {crop_bn} উৎপাদিত হয়েছিল?"),

    # ---------- ranking / superlative ----------
    dict(id="top_districts_production", category="ranking", difficulty=2,
         sampler=CROP_YEAR,
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(d:District) RETURN d.name AS answer "
                "ORDER BY p.production_mt DESC LIMIT 3",
         guard=("MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(:District) RETURN p.production_mt AS m ORDER BY m DESC LIMIT 4",
                lambda g: len(g) >= 4 and g[2]["m"] > g[3]["m"] and g[0]["m"] > 0),
         en="Which three districts produced the most {crop} in {year}?",
         bn="{year} সালে কোন তিনটি জেলায় সবচেয়ে বেশি {crop_bn} উৎপাদিত হয়েছিল?"),
    dict(id="best_upazila_suitability", category="ranking", difficulty=2,
         sampler="""MATCH (c:Crop)-[s:SUITABLE_IN]->(u:Upazila)-[:IN_DISTRICT]
                    ->(d:District) WHERE s.suitability_factor IS NOT NULL
                    RETURN DISTINCT c.name AS crop, d.name AS district""",
         cypher="MATCH (:Crop {name: $crop})-[s:SUITABLE_IN]->(u:Upazila)"
                "-[:IN_DISTRICT]->(:District {name: $district}) "
                "WHERE s.suitability_factor IS NOT NULL "
                "RETURN u.name AS answer "
                "ORDER BY s.suitability_factor DESC LIMIT 1",
         guard=("MATCH (:Crop {name: $crop})-[s:SUITABLE_IN]->(:Upazila)"
                "-[:IN_DISTRICT]->(:District {name: $district}) "
                "WHERE s.suitability_factor IS NOT NULL "
                "RETURN s.suitability_factor AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"] and g[0]["m"] >= 0.4),
         en="Which upazila of {district} district is most suitable for "
            "growing {crop}?",
         bn="{district} জেলার কোন উপজেলা {crop_bn} চাষের জন্য সবচেয়ে উপযোগী?"),
    dict(id="top_crop_in_district", category="ranking", difficulty=2,
         sampler="""MATCH (:Crop)-[p:PRODUCED_IN]->(d:District)
                    WHERE p.production_mt > 0
                    RETURN DISTINCT d.name AS district, p.crop_year AS year""",
         cypher="MATCH (c:Crop)-[p:PRODUCED_IN {crop_year: $year}]->"
                "(:District {name: $district}) "
                "RETURN c.name AS answer "
                "ORDER BY p.production_mt DESC LIMIT 1",
         guard=("MATCH (:Crop)-[p:PRODUCED_IN {crop_year: $year}]->"
                "(:District {name: $district}) "
                "RETURN p.production_mt AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]),
         en="Which crop had the highest production in {district} district "
            "in {year}?",
         bn="{year} সালে {district} জেলায় কোন ফসলের উৎপাদন সবচেয়ে বেশি ছিল?"),
    dict(id="highest_yield_district", category="ranking", difficulty=2,
         sampler=CROP_YEAR,
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(d:District) WHERE p.yield_mt_per_ha IS NOT NULL "
                "RETURN d.name AS answer "
                "ORDER BY p.yield_mt_per_ha DESC LIMIT 1",
         guard=("MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(:District) WHERE p.yield_mt_per_ha IS NOT NULL "
                "RETURN p.yield_mt_per_ha AS m, p.quality_flag AS f "
                "ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]
                and g[0]["m"] <= 25 and not g[0]["f"]),
         en="Which district had the highest {crop} yield per hectare "
            "in {year}?",
         bn="{year} সালে কোন জেলায় হেক্টর প্রতি {crop_bn_gen} ফলন সবচেয়ে বেশি ছিল?"),
    dict(id="most_suitable_crop_upazila", category="ranking", difficulty=2,
         sampler="""MATCH (:Crop)-[s:SUITABLE_IN]->(u:Upazila)
                    WHERE s.suitability_factor IS NOT NULL
                    WITH u, count(*) AS k
                    MATCH (x:Upazila) WHERE x.name = u.name
                    WITH u, k, count(x) AS n WHERE n = 1 AND k >= 5
                    RETURN u.name AS upazila""",
         cypher="MATCH (c:Crop)-[s:SUITABLE_IN]->(:Upazila {name: $upazila}) "
                "WHERE s.suitability_factor IS NOT NULL "
                "RETURN c.name AS answer "
                "ORDER BY s.suitability_factor DESC LIMIT 3",
         guard=("MATCH (:Crop)-[s:SUITABLE_IN]->(:Upazila {name: $upazila}) "
                "WHERE s.suitability_factor IS NOT NULL "
                "RETURN s.suitability_factor AS m ORDER BY m DESC LIMIT 4",
                lambda g: len(g) >= 4 and g[2]["m"] > g[3]["m"]
                and g[0]["m"] >= 0.4),
         en="Which three crops are most suitable for cultivation in "
            "{upazila} upazila?",
         bn="{upazila} উপজেলায় চাষের জন্য সবচেয়ে উপযোগী তিনটি ফসল কী কী?"),

    # ---------- temporal ----------
    dict(id="production_two_years", category="temporal", difficulty=2,
         sampler="""MATCH (c:Crop)-[p1:PRODUCED_IN {crop_year: '2019-20'}]->
                    (d:District)
                    MATCH (c)-[p2:PRODUCED_IN {crop_year: '2023-24'}]->(d)
                    WHERE p1.production_mt > 500 AND p2.production_mt > 500
                    RETURN c.name AS crop, d.name AS district""",
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN]->"
                "(:District {name: $district}) "
                "WHERE p.crop_year IN ['2019-20', '2023-24'] "
                "RETURN p.crop_year AS answer, p.production_mt AS mt "
                "ORDER BY p.crop_year",
         en="Compare the production of {crop} in {district} district between "
            "2019-20 and 2023-24.",
         bn="2019-20 এবং 2023-24 সালে {district} জেলায় {crop_bn_gen} উৎপাদন "
            "তুলনা করুন।"),
    dict(id="best_year_yield", category="temporal", difficulty=2,
         sampler="""MATCH (c:Crop)-[p:PRODUCED_IN]->(d:District)
                    WHERE p.production_mt > 1000
                    RETURN DISTINCT c.name AS crop, d.name AS district""",
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN]->"
                "(:District {name: $district}) "
                "WHERE p.yield_mt_per_ha IS NOT NULL "
                "RETURN p.crop_year AS answer "
                "ORDER BY p.yield_mt_per_ha DESC LIMIT 1",
         guard=("MATCH (:Crop {name: $crop})-[p:PRODUCED_IN]->"
                "(:District {name: $district}) "
                "WHERE p.yield_mt_per_ha IS NOT NULL "
                "RETURN p.yield_mt_per_ha AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"] and g[0]["m"] <= 25),
         en="In which year did {district} district get its best {crop} "
            "yield?",
         bn="{district} জেলায় কোন বছর {crop_bn_gen} ফলন সবচেয়ে ভালো হয়েছিল?"),
    dict(id="area_trend", category="temporal", difficulty=3,
         sampler="""MATCH (c:Crop)-[p:PRODUCED_IN]->(d:District)
                    WHERE p.production_mt > 1000
                    RETURN DISTINCT c.name AS crop, d.name AS district""",
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN]->"
                "(:District {name: $district}) "
                "RETURN p.crop_year AS answer, p.area_acres AS acres "
                "ORDER BY p.crop_year",
         en="How has the cultivated area of {crop} changed over the years in "
            "{district} district?",
         bn="{district} জেলায় {crop_bn} চাষের জমির পরিমাণ বিভিন্ন বছরে "
            "কীভাবে বদলেছে?"),

    # ---------- comparison ----------
    dict(id="compare_two_districts", category="comparison", difficulty=2,
         sampler="""MATCH (c:Crop)-[p1:PRODUCED_IN]->(d1:District),
                          (c)-[p2:PRODUCED_IN {crop_year: p1.crop_year}]->
                          (d2:District)
                    WHERE d1.name < d2.name AND p1.production_mt > 1000
                          AND p2.production_mt > 1000
                    RETURN c.name AS crop, p1.crop_year AS year,
                           d1.name AS district1, d2.name AS district2
                    LIMIT 500""",
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(d:District) WHERE d.name IN [$district1, $district2] "
                "RETURN d.name AS answer "
                "ORDER BY p.production_mt DESC LIMIT 1",
         guard=("MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(d:District) WHERE d.name IN [$district1, $district2] "
                "RETURN p.production_mt AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]),
         en="Between {district1} and {district2}, which district produced "
            "more {crop} in {year}?",
         bn="{year} সালে {district1} নাকি {district2}, কোন জেলায় বেশি "
            "{crop_bn} উৎপাদিত হয়েছিল?"),
    dict(id="compare_two_crops", category="comparison", difficulty=2,
         sampler="""MATCH (c1:Crop)-[:PRODUCED_IN {crop_year: '2023-24'}]->(),
                          (c2:Crop)
                    WHERE c1.name < c2.name AND c2.name IS NOT NULL
                    RETURN DISTINCT c1.name AS crop1, c2.name AS crop2""",
         cypher="MATCH (c:Crop)-[p:PRODUCED_IN {crop_year: '2023-24'}]->() "
                "WHERE c.name IN [$crop1, $crop2] "
                "WITH c.name AS answer, sum(p.production_mt) AS total "
                "RETURN answer ORDER BY total DESC LIMIT 1",
         guard=("MATCH (c:Crop)-[p:PRODUCED_IN {crop_year: '2023-24'}]->() "
                "WHERE c.name IN [$crop1, $crop2] "
                "WITH c.name AS a, sum(p.production_mt) AS m "
                "RETURN m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]),
         en="Which had the higher national production in 2023-24, {crop1} "
            "or {crop2}?",
         bn="2023-24 সালে {crop1_bn} নাকি {crop2_bn}, কোনটির জাতীয় উৎপাদন "
            "বেশি ছিল?"),

    # ---------- multi-hop ----------
    dict(id="water_req_of_top_crop", category="multihop", difficulty=3,
         sampler="""MATCH (c:Crop)-[p:PRODUCED_IN]->(d:District)
                    WHERE p.production_mt > 0
                    RETURN DISTINCT d.name AS district, p.crop_year AS year""",
         cypher="MATCH (c:Crop)-[p:PRODUCED_IN {crop_year: $year}]->"
                "(:District {name: $district}) "
                "WITH c, p ORDER BY p.production_mt DESC LIMIT 1 "
                "RETURN c.water_requirement AS answer",
         guard=("MATCH (:Crop)-[p:PRODUCED_IN {crop_year: $year}]->"
                "(:District {name: $district}) "
                "RETURN p.production_mt AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]),
         en="What is the water requirement of the top crop of {district} "
            "district (by {year} production)?",
         bn="{year} সালের উৎপাদন অনুযায়ী {district} জেলার প্রধান ফসলের পানির "
            "চাহিদা কেমন?"),
    dict(id="division_of_top_producer", category="multihop", difficulty=3,
         sampler=CROP_YEAR,
         cypher="MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(d:District) WITH d, p ORDER BY p.production_mt DESC LIMIT 1 "
                "MATCH (d)-[:IN_DIVISION]->(v) RETURN v.name AS answer",
         guard=("MATCH (:Crop {name: $crop})-[p:PRODUCED_IN {crop_year: $year}]"
                "->(:District) RETURN p.production_mt AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]),
         en="In which division is the district that produced the most {crop} "
            "in {year}?",
         bn="{year} সালে সবচেয়ে বেশি {crop_bn} উৎপাদনকারী জেলাটি কোন বিভাগে অবস্থিত?"),
    dict(id="pests_of_top_crop", category="multihop", difficulty=3,
         sampler="""MATCH (c:Crop)-[p:PRODUCED_IN]->(d:District),
                          (c)-[:AFFECTED_BY]->()
                    WHERE p.production_mt > 0
                    RETURN DISTINCT d.name AS district, p.crop_year AS year""",
         cypher="MATCH (c:Crop)-[p:PRODUCED_IN {crop_year: $year}]->"
                "(:District {name: $district}) "
                "WITH c, p ORDER BY p.production_mt DESC LIMIT 1 "
                "MATCH (c)-[:AFFECTED_BY]->(pest) "
                "RETURN pest.name AS answer",
         guard=("MATCH (:Crop)-[p:PRODUCED_IN {crop_year: $year}]->"
                "(:District {name: $district}) "
                "RETURN p.production_mt AS m ORDER BY m DESC LIMIT 2",
                lambda g: len(g) >= 2 and g[0]["m"] > g[1]["m"]),
         en="Which pests and diseases threaten the top crop of {district} "
            "district (by {year} production)?",
         bn="{year} সালের উৎপাদন অনুযায়ী {district} জেলার প্রধান ফসলটিতে কোন "
            "কোন পোকা ও রোগ আক্রমণ করতে পারে?"),
    dict(id="suitable_and_affected", category="multihop", difficulty=3,
         sampler="""MATCH (c:Crop)-[:AFFECTED_BY]->(p:PestDisease),
                          (c)-[s:SUITABLE_IN]->(:Upazila)-[:IN_DISTRICT]->
                          (d:District)
                    WHERE s.suitability_factor > 0.7
                    RETURN DISTINCT p.name AS pest, d.name AS district
                    LIMIT 500""",
         cypher="MATCH (c:Crop)-[:AFFECTED_BY]->(:PestDisease {name: $pest}), "
                "(c)-[s:SUITABLE_IN]->(:Upazila)-[:IN_DISTRICT]->"
                "(:District {name: $district}) "
                "WHERE s.suitability_factor > 0.7 "
                "RETURN DISTINCT c.name AS answer ORDER BY c.name",
         en="Which crops that are highly suitable somewhere in {district} "
            "district are attacked by {pest}?",
         bn="{district} জেলায় চাষের জন্য অত্যন্ত উপযোগী এমন কোন কোন ফসলে {pest} "
            "আক্রমণ করে?"),
]
