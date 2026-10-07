# EN-BN gap tests (eval\results)

| model | gap | 95% CI | p boot | Holm | p sign-flip | Holm | templates EN>BN / BN>EN / tie | p sign | Holm | top-2 templates (items) | share | gap without top-2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Opus 5 | +4.3 | [0.2, 10.0] | 0.044 | 0.132 | 0.126 | 0.496 | 5 / 1 / 20 | 0.219 | 0.474 | top_districts_production (+11), compare_two_districts (+6) | 85% | +0.7 |
| Sonnet 5 | +10.4 | [0.9, 21.6] | 0.023 | 0.092 | 0.124 | 0.496 | 4 / 0 / 22 | 0.125 | 0.474 | water_req_of_top_crop (+18), top_districts_production (+14) | 67% | +3.8 |
| DeepSeek-R1 | +7.0 | [2.2, 11.8] | 0.003 | 0.018 | 0.014 | 0.082 | 13 / 3 / 10 | 0.021 | 0.128 | division_production (+7), best_upazila_suitability (+5) | 38% | +4.7 |
| Pixtral Large | +13.7 | [4.7, 21.1] | 0.005 | 0.025 | 0.005 | 0.034 | 21 / 2 / 3 | 0.000 | 0.000 | pests_of_top_crop (+10), most_suitable_crop_upazila (+8) | 29% | +10.6 |
| Haiku 4.5 | +3.9 | [-1.9, 10.5] | 0.215 | 0.430 | 0.291 | 0.582 | 11 / 4 / 11 | 0.118 | 0.474 | highest_yield_district (+11), top_crop_in_district (+5) | 89% | +0.5 |
| Llama 3.3 70B | +5.2 | [0.7, 13.4] | 0.000 | 0.000 | 0.031 | 0.157 | 6 / 0 / 20 | 0.031 | 0.156 | count_crops_pest (+17), compare_two_crops (+3) | 83% | +0.9 |
| Llama 3.1 8B | +0.9 | [-0.9, 3.7] | 0.717 | 0.717 | 1.000 | 1.000 | 1 / 2 / 23 | 1.000 | 1.000 | sowing_time (+6), harvest_time (+0) | 150% | -0.5 |
