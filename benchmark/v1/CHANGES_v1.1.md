# Benchmark v1.1: gold answers on the corrected graph

415 of 460 items keep their v1.0 gold answer, 33 change, 12 are retired (the query returns nothing on the corrected graph). Questions, parameters and gold queries are identical to v1.0; only the executed answers differ. `benchmark_v1.1.jsonl` holds both (`gold` is v1.1, `gold_v1_0` the evaluated answer) and a `status_v1_1` field.

| template | changed | retired | items |
|---|---|---|---|
| pest_conditions | 3 | 8 | pest_conditions-001, pest_conditions-002, pest_conditions-003, pest_conditions-004, pest_conditions-005, pest_conditions-009, pest_conditions-011, pest_conditions-012, pest_conditions-013, pest_conditions-015, pest_conditions-016 |
| harvest_time | 8 | 0 | harvest_time-000, harvest_time-002, harvest_time-003, harvest_time-005, harvest_time-006, harvest_time-007, harvest_time-009, harvest_time-015 |
| suitable_and_affected | 3 | 4 | suitable_and_affected-000, suitable_and_affected-005, suitable_and_affected-006, suitable_and_affected-007, suitable_and_affected-010, suitable_and_affected-012, suitable_and_affected-015 |
| count_crops_pest | 6 | 0 | count_crops_pest-001, count_crops_pest-010, count_crops_pest-012, count_crops_pest-014, count_crops_pest-016, count_crops_pest-017 |
| sowing_time | 5 | 0 | sowing_time-005, sowing_time-006, sowing_time-007, sowing_time-009, sowing_time-015 |
| pests_of_top_crop | 4 | 0 | pests_of_top_crop-002, pests_of_top_crop-009, pests_of_top_crop-011, pests_of_top_crop-017 |
| production_two_years | 2 | 0 | production_two_years-004, production_two_years-017 |
| national_production | 1 | 0 | national_production-005 |
| division_production | 1 | 0 | division_production-015 |
