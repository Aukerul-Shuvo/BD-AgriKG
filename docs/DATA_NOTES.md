# Data notes

# Data repair round, 21 September 2026

A post-submission audit went beyond the checksum validation and found seven defects, all fixed in v1.1. Two further suspected defects did not survive verification and were left alone. Everything below was checked against the source PDFs or against an independent edition, never assumed.

## Fixed

**Jute unit error (editions affected: 2021).** Crop years 2018-19 and
2019-20 entered the panel at about 11 t/ha against a national norm near
2.2. The cause was not the extraction heuristic: the 2021 edition contains
no occurrence of the word "bale" on its jute page and its header explicitly
reads "Production (M. Ton)". The figures are nonetheless 400 lb bales.
Evidence: crop year 2018-19 appears in both the 2020 and 2021 editions, and
for Bagerhat they report 2,314 MT and 12,063 respectively, a ratio of 5.21
against the bale constant of 5.511; applying the conversion reconciles them
to within 5%, normal provisional-to-revised drift. Every other crop year
covered by two editions agrees at a ratio of exactly 1.000. Handled by an
explicit documented override (`UNIT_OVERRIDE_BALES` in `extract_bbs.py`),
not by a heuristic. Jute now reads 2.02 and 2.09 t/ha for those years.

**Printed yield column not converted with production.** For the five-column
table format `yield_mt_per_ha` is read from the printed yield-rate column,
which carries the same unit as production, but only production was being
converted. Every jute yield in the per-edition CSVs was therefore 5.5x high
across all ten editions. The panel had masked this because it always
rederives yield from production and area. Fixed at source.

**Two-edition consensus resolved silently to the newest edition.** With
exactly two editions the median equals their mean, so if they disagree at
all neither lies within the 2% agreement window, the agreement test selects
nothing, and the old code fell through to the newest edition without a
flag. This is how the 2017 edition's misparsed sugarcane table (2.44 t/ha
against the 2016 edition's 30.76, with byte-identical areas in both) reached
the panel. The consensus rule now prefers a candidate whose derived yield is
agronomically plausible over the merely newest one, and always flags. A
corpus-wide scan for systematically inconsistent (edition, crop, year)
triples finds exactly one, the sugarcane case, so this was isolated.

**Physically implausible cells.** 29 cells exceed a per-crop plausibility
ceiling. Every edition reproduces each one, and the district time series
shows a stable area with production spiking in a single year (Narsingdi
maize 2,752 MT against a neighbourhood of about 95; Sylhet groundnut 844
against about 30; Khulna sugarcane 7,452 against about 1,470), so the
production figure is garbled and the true value is unrecoverable. They carry
the flag `implausible-yield` and are excluded from benchmark sampling. They
are never rewritten.

**Chili is two incomparable series.** Dry chili runs 1.2-1.6 t/ha through
2019-20; from 2020-21 the yearbooks report green chili, harvested wet, at
3.8-6.0 t/ha. 320 rows from the break carry `chili-green-series`. The chili
plausibility ceiling is set at 20 t/ha so green chili is not misreported as
garbled. Correction, 23 September: this note said the rows were excluded
from temporal questions, but no template did so. Benchmark v1, as released
for NORA, has four chili items spanning the break; `best_year_yield-007`
(Feni) and `-008` (Natore) have gold years, 2022-23 and 2023-24, that win
only because green chili is weighed wet. The two `area_trend` items report
area, which the change of series does not affect. Benchmark v2 excludes
chili from every template that compares crop years.

**Benchmark sampler quality guard.** The sampler used a blanket
`yield <= 25` ceiling, which was wrong in both directions: it admitted
garbled maize at 179 t/ha and excluded legitimate sugarcane, which really
does yield 30-40. Replaced with a check against the panel's own quality
flags, rejecting values marked `implausible-yield`, `yoy-jump` or
`unresolved`, while accepting flags where the consensus rule already
resolved the conflict. `best_year_yield` previously had no flag check at
all.

**Crop-pest associations.** The "Insects and Diseases" sheet of
`crop-meteorology.xlsx` contains four blocks of copy-pasted sets: an
identical `{Aphid, Blast, Leaf Rust, Stem Borer}` on wheat, maize, potato
and lentil; an Allium set on onion, garlic and sugarcane; a mustard set on
chili and groundnut; and mungbean's yellow mosaic on chickpea. These produce
associations that are false, such as Leaf Rust on potato, Purple Blotch on
sugarcane and Yellow Mosaic Virus on chickpea. The defect is in the source
file, not the pipeline. The twelve affected crops are replaced from
`data/raw/crop_pest_corrected.csv`, compiled page by page from the DAE
Krishoker Janala crop database, with peer-reviewed Bangladeshi sources where
the DAE pages are thin or predate an outbreak: wheat blast, which reached
Bangladesh only in 2016, and maize fall armyworm, first recorded in 2018.
Every row carries its source. The rice and jute rows of the original sheet
are crop-specific and correct and are kept. 82 associations over 35 pests
became 97 over 69.

**Crop calendar.** Verified against BRRI, BARI, BSRI and BAMIS/DAE.
Corrected: Aman harvest (December-early January to November-December),
potato sowing (mid-September, when the land is still under T. Aman, to
mid-November-early December), onion harvest (late April-mid June, which is
closer to storage than field harvest, to March-April), groundnut (mid-June
to mid-July matched no Bangladeshi season; now rabi, mid-October to
mid-November, harvest February-March), gram harvest (November is impossible
for an October-November sowing; now February-March), mung harvest (a 60-70
day crop, so late October-November), maize sowing (closes mid-November, not
late December), garlic harvest (March-April), and chili, whose sowing window
matched no Bangladeshi season and whose harvest was stored as the relative
phrase "3-4 months after sowing", unusable as a gold answer.

The sheet gives one sowing and one harvest window per crop, so for crops
grown in more than one season these describe the dominant season only.
Separately, the three rice rows reproduce the local and traditional-variety
rows of the BBS rice crop calendar rather than the HYV rows that account for
most of the area; they are internally consistent and correctly sourced, but
the distinction matters when reading Aus and Boro windows.

## Checked and found sound

**Sugarcane calendar overlap is not an error.** The review flagged harvest
(mid-October to mid-April) beginning before planting ends (mid-October to
mid-December). Cane occupies the land 12 to 14 months, so harvesting the
previous crop genuinely overlaps planting the next. Only the harvest start
was tightened, to November.

**Garlic yields are correct.** Flagged during verification as running about
40% below an assumed norm. National totals track BBS closely (485k MT for
2019-20, 502k for 2020-21) and the yield series rises smoothly from 4.28 to
6.16 t/ha across twelve years with no discontinuity. The assumed norm was
wrong, not the data.

# Data quality notes, BBS production panel

Verified 31 Aug 2026, superseded in part by the repair round above. A 5-agent adversarial pass re-read 12 randomly sampled
panel cells directly from the yearbook PDFs: 12 of 12 exact matches,
including summed Boro component tables (2018), summed Kharif and Rabi chili
tables (2019), and the jute bale conversion (2016 and 2023 editions print
jute production in 400 lb bales, converted at 181.44 kg per bale).

Panel: data/processed/kg/production.csv. 12,273 rows, 16 crops x 12 crop
years (2013-14 to 2024-25) x 64 districts, from yearbook editions 2016-2025
with cross-edition median consensus. 264 rows where the newest edition
disagreed with the median were resolved in favour of the agreeing editions
(flag newest-edition-outlier-rejected). 2,477 rows (20 percent) rest on a
single edition (n_editions = 1).

Known limitations, all inherited from the source:
- 12 of 192 (crop, year) pairs cover 61-63 districts instead of 64. Worst:
  Jute (5 years), and 2017-18 where Cox's Bazar is missing for 6 crops.
  The missing rows are mostly all-zero rows the PDFs print with blank cells.
- 134 rows carry flag yoy-jump-gt-10x: production changes more than 10x
  between consecutive years. Several look like thousand-unit slips in one
  edition (e.g. Wheat Madaripur 2023-24, Chili Cumilla 2022-23). Treat these
  cells with caution; do not silently correct them.
- yield_mt_per_ha is always derived as production_mt / (area_acres x
  0.404686), never taken from the printed yield columns, whose units drift
  across editions (maund per acre, kg per acre, mt per ha, bales).
- The yearbooks' own national and division subtotal rows contain misprints
  (e.g. Mung 2022-23 national area, Meherpur maize 2023-24 production
  missing a digit). District rows were kept faithful to print and validated
  against division subtotals; discrepancies are listed in
  data/processed/bbs/extract_report.txt.
- Editions 2013-2015 (old Zila/Region layout) are not ingested. The 6 major
  crops' long series 1969-2015 can come from the BBS "45 Years" volume later.

National totals cross-checked against published figures for 2023-24: Boro
21.1M MT, Aman 16.7M, Aus 3.0M, Potato 10.6M, Maize 4.4M, Wheat 1.15M.

# Benchmark v1 quality assurance (1 Sept 2026)

A 5-agent adversarial review (4 item reviewers over all 24 templates plus a
harness red-team) found 14 blockers; all were fixed and the benchmark was
regenerated:
- Grading now compares rows strictly by value multisets with numeric
  tolerance; extra columns fail, killing the shotgun-column exploit that
  would have beaten 222 single-value items. The prompt tells models to
  return only what is asked, aliased AS answer.
- Gold queries no longer carry cosmetic round(), extra metric columns or
  cosmetic ORDER BY; ranking, comparison and top-pick templates now grade
  on the asked-for names only.
- Generation guards reject items with ties at the LIMIT boundary, top
  suitability below 0.4, implausible top yields (over 25 mt/ha) or
  quality-flagged top rows.
- KG fixes: Aphid/Aphids merged (35 pests), Gram calendar corrected against
  DAE/BARI (the raw sheet carried Mung's dates), HTML residue stripped,
  zero and null production rows are no longer loaded as PRODUCED_IN edges
  (11,632 remain), sadar-named upazilas excluded from location questions.
- Query timeout was silently inert (passed as a query parameter); now a
  real 15 s transaction timeout.

Known residual limitations, stated in the paper: single-value integer
answers cluster (64, 9, small counts), so a wrong query can coincide with
the right value; template-based questions lack paraphrase diversity;
Bangla place names stay in Latin script by design.
