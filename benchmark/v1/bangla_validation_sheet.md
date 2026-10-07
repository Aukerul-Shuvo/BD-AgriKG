# Bangla validation sheet (26 templates)

Rows the automatic check flagged are first and marked **CHECK**.
Each template shows up to three items with different crops, so that a
wrong case ending on a substituted crop name is visible.

For each template fill in:

- **Fluency**: 1 unnatural, 2 acceptable, 3 natural.
- **Adequacy**: does the Bangla ask exactly what the English asks?
  yes, or no plus what differs.
- **Correction**: the Bangla you would write instead.

Latin-script place names, years and pest names are deliberate; do not
flag those. Crop names should always be in Bangla.

## What fixes the expected answer type

| Bangla | meaning |
|---|---|
| কয়টি | how many (expects a count) |
| কতটি | how many (expects a count) |
| কত | how much (expects a quantity) |
| কোন কোন | which ones (expects a list) |
| কোনটি | which one (expects a single item) |
| তিনটি | three (expects exactly three) |
| সবচেয়ে বেশি | the highest |
| সবচেয়ে | the most |
| হেক্টর প্রতি | per hectare |
| একর প্রতি | per acre |
| অত্যন্ত | highly |
| প্রধান | main or top |

---

### 1. `water_req_of_top_crop` (multihop, n=18) **CHECK (18 of 18 flagged)**

Answer-type words present: `প্রধান`

| | English | Bangla |
|---|---|---|
| water_req_of_top_crop-000 | What is the water requirement of the top crop of Khulna district (by 2018-19 production)? | 2018-19 সালের উৎপাদন অনুযায়ী Khulna জেলার প্রধান ফসলের পানির চাহিদা কেমন? |
| water_req_of_top_crop-001 | What is the water requirement of the top crop of Gazipur district (by 2015-16 production)? | 2015-16 সালের উৎপাদন অনুযায়ী Gazipur জেলার প্রধান ফসলের পানির চাহিদা কেমন? |
| water_req_of_top_crop-002 | What is the water requirement of the top crop of Pirojpur district (by 2016-17 production)? | 2016-17 সালের উৎপাদন অনুযায়ী Pirojpur জেলার প্রধান ফসলের পানির চাহিদা কেমন? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 2. `sowing_time` (lookup, n=16) **CHECK (8 of 16 flagged)**

| | English | Bangla |
|---|---|---|
| sowing_time-000 | When is Wheat sown, planted or transplanted in Bangladesh? | বাংলাদেশে গম কখন বপন বা রোপণ করা হয়? |
| sowing_time-001 | When is Sugarcane sown, planted or transplanted in Bangladesh? | বাংলাদেশে আখ কখন বপন বা রোপণ করা হয়? |
| sowing_time-002 | When is Mung sown, planted or transplanted in Bangladesh? | বাংলাদেশে মুগ কখন বপন বা রোপণ করা হয়? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 3. `count_crops_pest` (aggregation, n=18) **CHECK (6 of 18 flagged)**

Answer-type words present: `কয়টি`

| | English | Bangla |
|---|---|---|
| count_crops_pest-000 | How many crops are attacked by Seedling Blight? | Seedling Blight কয়টি ফসলে আক্রমণ করে? |
| count_crops_pest-001 | How many crops are attacked by Thrips? | Thrips কয়টি ফসলে আক্রমণ করে? |
| count_crops_pest-002 | How many crops are attacked by Jute Hairy Caterpillar? | Jute Hairy Caterpillar কয়টি ফসলে আক্রমণ করে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 4. `pest_conditions` (lookup, n=18) **CHECK (4 of 18 flagged)**

| | English | Bangla |
|---|---|---|
| pest_conditions-000 | Under what conditions does Rice Bug attack Aman? | কোন অবস্থায় আমন ধানে Rice Bug আক্রমণ করে? |
| pest_conditions-001 | Under what conditions does Thrips attack Onion? | কোন অবস্থায় পেঁয়াজে Thrips আক্রমণ করে? |
| pest_conditions-002 | Under what conditions does Aphid attack Groundnut? | কোন অবস্থায় চীনাবাদামে Aphid আক্রমণ করে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 5. `water_req` (lookup, n=16) **CHECK (1 of 16 flagged)**

| | English | Bangla |
|---|---|---|
| water_req-000 | What is the water requirement of Groundnut? | চীনাবাদাম চাষে পানির চাহিদা কেমন? |
| water_req-001 | What is the water requirement of Lentil? | মসুর চাষে পানির চাহিদা কেমন? |
| water_req-002 | What is the water requirement of Onion? | পেঁয়াজ চাষে পানির চাহিদা কেমন? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 6. `suitable_and_affected` (multihop, n=18) **CHECK (1 of 18 flagged)**

Answer-type words present: `কোন কোন`, `অত্যন্ত`

| | English | Bangla |
|---|---|---|
| suitable_and_affected-000 | Which crops that are highly suitable somewhere in Feni district are attacked by Flea Beetle? | Feni জেলায় চাষের জন্য অত্যন্ত উপযোগী এমন কোন কোন ফসলে Flea Beetle আক্রমণ করে? |
| suitable_and_affected-001 | Which crops that are highly suitable somewhere in Bhola district are attacked by Sheath Rot? | Bhola জেলায় চাষের জন্য অত্যন্ত উপযোগী এমন কোন কোন ফসলে Sheath Rot আক্রমণ করে? |
| suitable_and_affected-002 | Which crops that are highly suitable somewhere in Faridpur district are attacked by Leaf Mosaic Virus? | Faridpur জেলায় চাষের জন্য অত্যন্ত উপযোগী এমন কোন কোন ফসলে Leaf Mosaic Virus আক্রমণ করে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 7. `harvest_time` (lookup, n=16)

| | English | Bangla |
|---|---|---|
| harvest_time-000 | When is Onion harvested? | পেঁয়াজ কখন ঘরে তোলা হয়? |
| harvest_time-001 | When is Mustard harvested? | সরিষা কখন ঘরে তোলা হয়? |
| harvest_time-002 | When is Aman harvested? | আমন ধান কখন ঘরে তোলা হয়? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 8. `seed_req` (lookup, n=16)

Answer-type words present: `একর প্রতি`

| | English | Bangla |
|---|---|---|
| seed_req-000 | How much seed or planting material is needed per acre for Sugarcane? | আখ চাষে একর প্রতি কী পরিমাণ বীজ লাগে? |
| seed_req-001 | How much seed or planting material is needed per acre for Potato? | আলু চাষে একর প্রতি কী পরিমাণ বীজ লাগে? |
| seed_req-002 | How much seed or planting material is needed per acre for Garlic? | রসুন চাষে একর প্রতি কী পরিমাণ বীজ লাগে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 9. `upazila_district` (lookup, n=18)

| | English | Bangla |
|---|---|---|
| upazila_district-000 | Which district is Mithapukur upazila in? | Mithapukur উপজেলা কোন জেলায় অবস্থিত? |
| upazila_district-001 | Which district is Basail upazila in? | Basail উপজেলা কোন জেলায় অবস্থিত? |
| upazila_district-002 | Which district is Eidgaon upazila in? | Eidgaon উপজেলা কোন জেলায় অবস্থিত? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 10. `upazila_soils` (lookup, n=18)

Answer-type words present: `কোন কোন`

| | English | Bangla |
|---|---|---|
| upazila_soils-000 | What soil types are found in Sreebardi upazila? | Sreebardi উপজেলায় কোন কোন ধরনের মাটি পাওয়া যায়? |
| upazila_soils-001 | What soil types are found in Bauphal upazila? | Bauphal উপজেলায় কোন কোন ধরনের মাটি পাওয়া যায়? |
| upazila_soils-002 | What soil types are found in Harinakundu upazila? | Harinakundu উপজেলায় কোন কোন ধরনের মাটি পাওয়া যায়? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 11. `count_producing_districts` (aggregation, n=18)

Answer-type words present: `কতটি`, `কত`

| | English | Bangla |
|---|---|---|
| count_producing_districts-000 | In how many districts was Lentil produced in 2015-16? | 2015-16 সালে কতটি জেলায় মসুর উৎপাদিত হয়েছিল? |
| count_producing_districts-001 | In how many districts was Aman produced in 2013-14? | 2013-14 সালে কতটি জেলায় আমন ধান উৎপাদিত হয়েছিল? |
| count_producing_districts-002 | In how many districts was Boro produced in 2022-23? | 2022-23 সালে কতটি জেলায় বোরো ধান উৎপাদিত হয়েছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 12. `count_upazilas` (aggregation, n=18)

Answer-type words present: `কয়টি`

| | English | Bangla |
|---|---|---|
| count_upazilas-000 | How many upazilas are there in Netrakona district? | Netrakona জেলায় কয়টি উপজেলা আছে? |
| count_upazilas-001 | How many upazilas are there in Patuakhali district? | Patuakhali জেলায় কয়টি উপজেলা আছে? |
| count_upazilas-002 | How many upazilas are there in Khagrachhari district? | Khagrachhari জেলায় কয়টি উপজেলা আছে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 13. `division_production` (aggregation, n=18)

Answer-type words present: `কত`

| | English | Bangla |
|---|---|---|
| division_production-000 | How much Groundnut was produced in Chattogram division in 2015-16? | 2015-16 সালে Chattogram বিভাগে কত চীনাবাদাম উৎপাদিত হয়েছিল? |
| division_production-001 | How much Wheat was produced in Sylhet division in 2015-16? | 2015-16 সালে Sylhet বিভাগে কত গম উৎপাদিত হয়েছিল? |
| division_production-002 | How much Aman was produced in Mymensingh division in 2021-22? | 2021-22 সালে Mymensingh বিভাগে কত আমন ধান উৎপাদিত হয়েছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 14. `national_production` (aggregation, n=18)

Answer-type words present: `কত`

| | English | Bangla |
|---|---|---|
| national_production-000 | What was the total national production of Mustard in 2024-25? | 2024-25 সালে সারা দেশে সরিষার মোট উৎপাদন কত ছিল? |
| national_production-001 | What was the total national production of Chili in 2022-23? | 2022-23 সালে সারা দেশে মরিচের মোট উৎপাদন কত ছিল? |
| national_production-002 | What was the total national production of Onion in 2023-24? | 2023-24 সালে সারা দেশে পেঁয়াজের মোট উৎপাদন কত ছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 15. `best_upazila_suitability` (ranking, n=18)

Answer-type words present: `সবচেয়ে`

| | English | Bangla |
|---|---|---|
| best_upazila_suitability-000 | Which upazila of Brahmanbaria district is most suitable for growing Aus? | Brahmanbaria জেলার কোন উপজেলা আউশ ধান চাষের জন্য সবচেয়ে উপযোগী? |
| best_upazila_suitability-001 | Which upazila of Rajshahi district is most suitable for growing Onion? | Rajshahi জেলার কোন উপজেলা পেঁয়াজ চাষের জন্য সবচেয়ে উপযোগী? |
| best_upazila_suitability-005 | Which upazila of Brahmanbaria district is most suitable for growing Wheat? | Brahmanbaria জেলার কোন উপজেলা গম চাষের জন্য সবচেয়ে উপযোগী? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 16. `highest_yield_district` (ranking, n=18)

Answer-type words present: `সবচেয়ে বেশি`, `সবচেয়ে`, `হেক্টর প্রতি`

| | English | Bangla |
|---|---|---|
| highest_yield_district-000 | Which district had the highest Maize yield per hectare in 2024-25? | 2024-25 সালে কোন জেলায় হেক্টর প্রতি ভুট্টার ফলন সবচেয়ে বেশি ছিল? |
| highest_yield_district-001 | Which district had the highest Aman yield per hectare in 2015-16? | 2015-16 সালে কোন জেলায় হেক্টর প্রতি আমন ধানের ফলন সবচেয়ে বেশি ছিল? |
| highest_yield_district-002 | Which district had the highest Mustard yield per hectare in 2022-23? | 2022-23 সালে কোন জেলায় হেক্টর প্রতি সরিষার ফলন সবচেয়ে বেশি ছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 17. `most_suitable_crop_upazila` (ranking, n=18)

Answer-type words present: `তিনটি`, `সবচেয়ে`

| | English | Bangla |
|---|---|---|
| most_suitable_crop_upazila-000 | Which three crops are most suitable for cultivation in Basail upazila? | Basail উপজেলায় চাষের জন্য সবচেয়ে উপযোগী তিনটি ফসল কী কী? |
| most_suitable_crop_upazila-001 | Which three crops are most suitable for cultivation in Sitakunda upazila? | Sitakunda উপজেলায় চাষের জন্য সবচেয়ে উপযোগী তিনটি ফসল কী কী? |
| most_suitable_crop_upazila-002 | Which three crops are most suitable for cultivation in Kamarkhanda upazila? | Kamarkhanda উপজেলায় চাষের জন্য সবচেয়ে উপযোগী তিনটি ফসল কী কী? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 18. `top_crop_in_district` (ranking, n=18)

Answer-type words present: `সবচেয়ে বেশি`, `সবচেয়ে`

| | English | Bangla |
|---|---|---|
| top_crop_in_district-000 | Which crop had the highest production in Chapainababganj district in 2014-15? | 2014-15 সালে Chapainababganj জেলায় কোন ফসলের উৎপাদন সবচেয়ে বেশি ছিল? |
| top_crop_in_district-001 | Which crop had the highest production in Sherpur district in 2015-16? | 2015-16 সালে Sherpur জেলায় কোন ফসলের উৎপাদন সবচেয়ে বেশি ছিল? |
| top_crop_in_district-002 | Which crop had the highest production in Rangpur district in 2017-18? | 2017-18 সালে Rangpur জেলায় কোন ফসলের উৎপাদন সবচেয়ে বেশি ছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 19. `top_districts_production` (ranking, n=18)

Answer-type words present: `তিনটি`, `সবচেয়ে বেশি`, `সবচেয়ে`

| | English | Bangla |
|---|---|---|
| top_districts_production-000 | Which three districts produced the most Mustard in 2018-19? | 2018-19 সালে কোন তিনটি জেলায় সবচেয়ে বেশি সরিষা উৎপাদিত হয়েছিল? |
| top_districts_production-001 | Which three districts produced the most Potato in 2020-21? | 2020-21 সালে কোন তিনটি জেলায় সবচেয়ে বেশি আলু উৎপাদিত হয়েছিল? |
| top_districts_production-002 | Which three districts produced the most Garlic in 2019-20? | 2019-20 সালে কোন তিনটি জেলায় সবচেয়ে বেশি রসুন উৎপাদিত হয়েছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 20. `area_trend` (temporal, n=18)

| | English | Bangla |
|---|---|---|
| area_trend-000 | How has the cultivated area of Onion changed over the years in Bhola district? | Bhola জেলায় পেঁয়াজ চাষের জমির পরিমাণ বিভিন্ন বছরে কীভাবে বদলেছে? |
| area_trend-001 | How has the cultivated area of Chili changed over the years in Magura district? | Magura জেলায় মরিচ চাষের জমির পরিমাণ বিভিন্ন বছরে কীভাবে বদলেছে? |
| area_trend-002 | How has the cultivated area of Sugarcane changed over the years in Sirajganj district? | Sirajganj জেলায় আখ চাষের জমির পরিমাণ বিভিন্ন বছরে কীভাবে বদলেছে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 21. `best_year_yield` (temporal, n=18)

Answer-type words present: `সবচেয়ে`

| | English | Bangla |
|---|---|---|
| best_year_yield-000 | In which year did Chuadanga district get its best Mustard yield? | Chuadanga জেলায় কোন বছর সরিষার ফলন সবচেয়ে ভালো হয়েছিল? |
| best_year_yield-001 | In which year did Chapainababganj district get its best Potato yield? | Chapainababganj জেলায় কোন বছর আলুর ফলন সবচেয়ে ভালো হয়েছিল? |
| best_year_yield-002 | In which year did Rangpur district get its best Onion yield? | Rangpur জেলায় কোন বছর পেঁয়াজের ফলন সবচেয়ে ভালো হয়েছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 22. `production_two_years` (temporal, n=18)

| | English | Bangla |
|---|---|---|
| production_two_years-000 | Compare the production of Garlic in Rajbari district between 2019-20 and 2023-24. | 2019-20 এবং 2023-24 সালে Rajbari জেলায় রসুনের উৎপাদন তুলনা করুন। |
| production_two_years-001 | Compare the production of Groundnut in Manikganj district between 2019-20 and 2023-24. | 2019-20 এবং 2023-24 সালে Manikganj জেলায় চীনাবাদামের উৎপাদন তুলনা করুন। |
| production_two_years-002 | Compare the production of Lentil in Chapainababganj district between 2019-20 and 2023-24. | 2019-20 এবং 2023-24 সালে Chapainababganj জেলায় মসুরের উৎপাদন তুলনা করুন। |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 23. `compare_two_crops` (comparison, n=18)

Answer-type words present: `কোনটি`

| | English | Bangla |
|---|---|---|
| compare_two_crops-000 | Which had the higher national production in 2023-24, Chili or Groundnut? | 2023-24 সালে মরিচ নাকি চীনাবাদাম, কোনটির জাতীয় উৎপাদন বেশি ছিল? |
| compare_two_crops-001 | Which had the higher national production in 2023-24, Lentil or Wheat? | 2023-24 সালে মসুর নাকি গম, কোনটির জাতীয় উৎপাদন বেশি ছিল? |
| compare_two_crops-002 | Which had the higher national production in 2023-24, Gram or Potato? | 2023-24 সালে ছোলা নাকি আলু, কোনটির জাতীয় উৎপাদন বেশি ছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 24. `compare_two_districts` (comparison, n=18)

| | English | Bangla |
|---|---|---|
| compare_two_districts-000 | Between Chandpur and Jhalokati, which district produced more Aus in 2019-20? | 2019-20 সালে Chandpur নাকি Jhalokati, কোন জেলায় বেশি আউশ ধান উৎপাদিত হয়েছিল? |
| compare_two_districts-001 | Between Chandpur and Patuakhali, which district produced more Aus in 2016-17? | 2016-17 সালে Chandpur নাকি Patuakhali, কোন জেলায় বেশি আউশ ধান উৎপাদিত হয়েছিল? |
| compare_two_districts-002 | Between Naogaon and Patuakhali, which district produced more Aus in 2016-17? | 2016-17 সালে Naogaon নাকি Patuakhali, কোন জেলায় বেশি আউশ ধান উৎপাদিত হয়েছিল? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 25. `division_of_top_producer` (multihop, n=18)

Answer-type words present: `সবচেয়ে বেশি`, `সবচেয়ে`

| | English | Bangla |
|---|---|---|
| division_of_top_producer-000 | In which division is the district that produced the most Jute in 2014-15? | 2014-15 সালে সবচেয়ে বেশি পাট উৎপাদনকারী জেলাটি কোন বিভাগে অবস্থিত? |
| division_of_top_producer-001 | In which division is the district that produced the most Maize in 2023-24? | 2023-24 সালে সবচেয়ে বেশি ভুট্টা উৎপাদনকারী জেলাটি কোন বিভাগে অবস্থিত? |
| division_of_top_producer-002 | In which division is the district that produced the most Lentil in 2017-18? | 2017-18 সালে সবচেয়ে বেশি মসুর উৎপাদনকারী জেলাটি কোন বিভাগে অবস্থিত? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

### 26. `pests_of_top_crop` (multihop, n=18)

Answer-type words present: `কোন কোন`, `প্রধান`

| | English | Bangla |
|---|---|---|
| pests_of_top_crop-000 | Which pests and diseases threaten the top crop of Gazipur district (by 2018-19 production)? | 2018-19 সালের উৎপাদন অনুযায়ী Gazipur জেলার প্রধান ফসলটিতে কোন কোন পোকা ও রোগ আক্রমণ করতে পারে? |
| pests_of_top_crop-001 | Which pests and diseases threaten the top crop of Khulna district (by 2013-14 production)? | 2013-14 সালের উৎপাদন অনুযায়ী Khulna জেলার প্রধান ফসলটিতে কোন কোন পোকা ও রোগ আক্রমণ করতে পারে? |
| pests_of_top_crop-002 | Which pests and diseases threaten the top crop of Bogura district (by 2023-24 production)? | 2023-24 সালের উৎপাদন অনুযায়ী Bogura জেলার প্রধান ফসলটিতে কোন কোন পোকা ও রোগ আক্রমণ করতে পারে? |

Fluency (1-3): 

Adequacy (yes / no + what differs): 

Correction: 

---

