# Bangla validation, pre-screen verdicts (for native-speaker sign-off)

How this was produced: every template's Bangla pattern was abstracted from the
460 released items and checked across all crop substitutions (nominative,
genitive and locative forms), against the English twin, and against the
cross-family adequacy flags. Verdicts below are the pre-screen. The
native-speaking author reads each row and marks **Agree** (Y or N with a
comment). The paper's claim rests on that sign-off, not on this pre-screen.

Scales: Fluency 1 unnatural, 2 acceptable, 3 natural. Adequacy yes / no.

Case-ending check: all 16 crops render correctly in every slot. Genitive
forms (সরিষার, আলুর, পেঁয়াজের, বোরো ধানের, মসুরের, ভুট্টার, মরিচের, রসুনের,
গমের, পাটের, চীনাবাদামের, মুগের, ছোলার, আখের) and locative forms (আমন ধানে,
পেঁয়াজে, চীনাবাদামে, মুগে, সরিষায়, ছোলায়, পাটে, গমে, আলুতে, আখে) are all
correct. No template hardcodes a wrong ending.

Register: standard written Bangla as used in DAE and BBS material (হয়েছিল,
অবস্থিত, উৎপাদিত). This matches the "extension-officer usage" claim; it is not
farmer speech, and the paper does not claim it is.

| # | template | Bangla pattern | Flu. | Adeq. | Pre-screen note | Action | Agree? |
|---|---|---|---|---|---|---|---|
| 1 | water_req_of_top_crop | {year} সালের উৎপাদন অনুযায়ী {district} জেলার **প্রধান ফসলের** পানির চাহিদা কেমন? | 3 | yes | Only real note in the set. প্রধান ফসলের does not mark number. Template 16 (pests_of_top_crop) uses the definite singular **প্রধান ফসলটিতে**, so this one should match. All models read it as singular in practice (Sonnet's failures were an extra column). | **Recommend** ফসলের → ফসলটির, then regenerate and re-run this template's 18 Bangla items on 7 models. | |
| 2 | sowing_time | বাংলাদেশে {crop} কখন বপন বা রোপণ করা হয়? | 3 | yes | English lists "sown, planted or transplanted"; রোপণ covers planting and transplanting in Bangla. The 8 machine flags are the translator, not the Bangla. | none | |
| 3 | count_crops_pest | {pest} কয়টি ফসলে আক্রমণ করে? | 3 | yes | কয়টি is present, so the answer type is a count, matching the gold. The 6 flags came from the back-translator dropping কয়টি. | none | |
| 4 | pest_conditions | কোন অবস্থায় {crop:LOC} {pest} আক্রমণ করে? | 3 | yes | Bangla adds ধান to Aman/Aus/Boro (আমন ধানে), which is idiomatic; English uses bare season names. কোন পরিস্থিতিতে would also work. | none | |
| 5 | water_req | {crop} চাষে পানির চাহিদা কেমন? | 3 | yes | Same ধান note as row 4. | none | |
| 6 | suitable_and_affected | {district} জেলায় চাষের জন্য অত্যন্ত উপযোগী এমন কোন কোন ফসলে {pest} আক্রমণ করে? | 3 | yes | অত্যন্ত উপযোগী carries the "highly suitable" threshold. The English "somewhere in" (any upazila) is not spelled out in Bangla, but neither reading changes the query. | none | |
| 7 | area_trend | {district} জেলায় {crop} চাষের জমির পরিমাণ বিভিন্ন বছরে কীভাবে বদলেছে? | 3 | yes | | none | |
| 8 | harvest_time | {crop} কখন ঘরে তোলা হয়? | 3 | yes | ঘরে তোলা is the idiomatic term for harvest. | none | |
| 9 | seed_req | {crop} চাষে একর প্রতি কী পরিমাণ বীজ লাগে? | 3 | yes | English says "seed or planting material" because sugarcane is planted from setts and potato from seed tubers. Bangla says only বীজ. Farmers do say বীজ আলু, so acceptable; বীজ বা রোপণ সামগ্রী would be more exact. Optional. | optional | |
| 10 | upazila_district | {upazila} উপজেলা কোন জেলায় অবস্থিত? | 3 | yes | | none | |
| 11 | upazila_soils | {upazila} উপজেলায় কোন কোন ধরনের মাটি পাওয়া যায়? | 3 | yes | কোন কোন gives a list, matching the gold. | none | |
| 12 | count_producing_districts | {year} সালে কতটি জেলায় {crop} উৎপাদিত হয়েছিল? | 3 | yes | কতটি gives a count. | none | |
| 13 | count_upazilas | {district} জেলায় কয়টি উপজেলা আছে? | 3 | yes | | none | |
| 14 | division_production | {year} সালে {division} বিভাগে কত {crop} উৎপাদিত হয়েছিল? | 3 | yes | কত gives a quantity. | none | |
| 15 | national_production | {year} সালে সারা দেশে {crop:GEN} মোট উৎপাদন কত ছিল? | 3 | yes | | none | |
| 16 | best_upazila_suitability | {district} জেলার কোন উপজেলা {crop} চাষের জন্য সবচেয়ে উপযোগী? | 3 | yes | | none | |
| 17 | highest_yield_district | {year} সালে কোন জেলায় হেক্টর প্রতি {crop:GEN} ফলন সবচেয়ে বেশি ছিল? | 3 | yes | হেক্টর প্রতি present, so yield not production. | none | |
| 18 | most_suitable_crop_upazila | {upazila} উপজেলায় চাষের জন্য সবচেয়ে উপযোগী তিনটি ফসল কী কী? | 3 | yes | তিনটি present, matching the three-row gold. | none | |
| 19 | top_crop_in_district | {year} সালে {district} জেলায় কোন ফসলের উৎপাদন সবচেয়ে বেশি ছিল? | 3 | yes | | none | |
| 20 | top_districts_production | {year} সালে কোন তিনটি জেলায় সবচেয়ে বেশি {crop} উৎপাদিত হয়েছিল? | 3 | yes | তিনটি present. | none | |
| 21 | best_year_yield | {district} জেলায় কোন বছর {crop:GEN} ফলন সবচেয়ে ভালো হয়েছিল? | 3 | yes | | none | |
| 22 | production_two_years | 2019-20 এবং 2023-24 সালে {district} জেলায় {crop:GEN} উৎপাদন তুলনা করুন। | 3 | yes | Imperative, matching the English "Compare". | none | |
| 23 | compare_two_crops | 2023-24 সালে {crop1} নাকি {crop2}, কোনটির জাতীয় উৎপাদন বেশি ছিল? | 3 | yes | Natural spoken pattern. The strict-metric failures on this template are formatting (models add the total), not language. | none | |
| 24 | compare_two_districts | {year} সালে {district1} নাকি {district2}, কোন জেলায় বেশি {crop} উৎপাদিত হয়েছিল? | 3 | yes | | none | |
| 25 | division_of_top_producer | {year} সালে সবচেয়ে বেশি {crop} উৎপাদনকারী জেলাটি কোন বিভাগে অবস্থিত? | 3 | yes | Slightly formal (উৎপাদনকারী জেলাটি) but standard in official prose. | none | |
| 26 | pests_of_top_crop | {year} সালের উৎপাদন অনুযায়ী {district} জেলার প্রধান ফসলটিতে কোন কোন পোকা ও রোগ আক্রমণ করতে পারে? | 3 | yes | Uses the definite singular ফসলটিতে, which is why row 1 should match it. | none | |

## Pre-screen summary

- 26 of 26 adequate. No template asks for a different quantity, entity or
  constraint than its English twin.
- 26 of 26 fluency 3 in standard written register.
- One recommended correction (row 1, ফসলের → ফসলটির), one optional (row 9).
- Zero case-ending errors across 16 crops in nominative, genitive and
  locative slots.

## Sign-off

Reviewed by (native Bangla-speaking author): ______________   Date: ________

Rows disagreed with, and the correction you would make:
