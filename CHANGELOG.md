# Changelog

## v1.1, 7 October 2026

Corrections from a post-review audit of the data, which went beyond the
division and national checksums: every crop year present in two yearbook
editions was reconciled, per-crop plausibility bands were applied, and the
crop calendar and the crop-pest table were re-read against the issuing
agencies' publications. Seven defects were found and corrected.

Production panel (`data/kg/v1.1/production.csv`):

1. Jute, crop years 2018-19 and 2019-20. The 2021 yearbook prints jute
   production in 400 lb bales under a "M. Ton" heading. The values were
   5.5 times too high and are now converted (181.44 kg per bale).
2. Sugarcane, 2013-14. A misread table in the 2017 edition gave 2.44 t/ha
   against 30-36 in every other year; the 2016 edition's values are used.
3. Chili. The yearbooks report dry chili up to 2019-20 and green chili
   from 2020-21, two series that are not comparable. Rows from 2020-21
   carry the flag `chili-green-series`.
4. 29 cells exceed per-crop plausibility ceilings in every edition that
   prints them (for example maize at 179 t/ha). They carry the flag
   `implausible-yield` and are kept as printed, not rewritten.
5. Where exactly two editions report a crop year and disagree, the
   earlier rule took the newer edition silently. The consensus now prefers
   the value whose derived yield is plausible and always flags the row.

Crop-pest table (`data/kg/v1.1/crop_pest.csv`, `data/raw/crop_pest_corrected.csv`):

6. Four blocks had been copy-pasted across crops in the source sheet
   (the same pests attached to wheat, maize, potato and lentil alike;
   onion diseases attached to sugarcane). Associations for 12 crops were
   rebuilt from DAE and peer-reviewed sources, each row carrying its
   source.

Crop calendar (`data/kg/v1.1/crops.csv`):

7. Five sowing or harvest windows were wrong (Aman harvest, potato
   sowing, onion harvest, sugarcane harvest start, and chili harvest,
   which had been released as "3-4 months after sowing"). Corrected
   against BRRI, BARI, BSRI and DAE calendars.

Effect on the benchmark (`benchmark/v1/benchmark_v1.1.jsonl`,
`benchmark/v1/CHANGES_v1.1.md`): 415 of the 460 items keep their gold
answer, 33 change (harvest_time 8, count_crops_pest 6, sowing_time 5,
pests_of_top_crop 4, pest_conditions 3, suitable_and_affected 3,
production_two_years 2, national_production 1, division_production 1) and
12 are retired because their crop-pest pair no longer exists
(pest_conditions 8, suitable_and_affected 4). Questions, parameters and
gold queries are identical in both versions.

Evaluation harness:

- The grader (`eval/grading.py`) now reads a single `collect()` list as
  rows and matches booleans only to booleans. Re-scoring every stored run
  on the v1.0 graph (`eval/results/camera`) changed five DeepSeek-R1
  verdicts (two English, three Bangla) and two of its repairs; no other
  run changed.
- The model listed as "Mistral Large 25.02" in the reviewed version is
  Pixtral Large 25.02 (Bedrock id `us.mistral.pixtral-large-2502-v1:0`).
- The results figure computed the Bangla penalty from rounded
  percentages; it now uses item counts (Sonnet 5: 10.4, not 10.5).

## v1.0, 13 September 2026

Graph, benchmark and model outputs as evaluated in the paper submitted
to NORA 2026.
