"""Merge the per-edition BBS extracts into one district x crop x year panel.

Each crop year appears in up to 3 yearbook editions (provisional, then
revised). Consensus rule per (crop, year, district):
- one edition only: take it
- several editions: take the newest value that agrees with the median of
  production within 2%; if the newest disagrees, take the median-agreeing
  value and flag the row (protects against single-edition digit garbling)
- with exactly two editions the median is their mean, so if they disagree
  at all neither is within 2% of it and the agreement test selects nothing.
  Previously that fell through to the newest edition silently, which is how
  the 2017 edition's misparsed sugarcane table (2.44 t/ha against the 2016
  edition's 30.76) reached the panel. Now, when the agreement test is empty
  and the candidates disagree materially, we prefer the candidate whose
  derived yield is agronomically plausible and always flag the row.

Writes data/processed/kg/production.csv keyed on adm2 pcode.
"""
import glob
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BBS = ROOT / "data" / "processed" / "bbs"
OUT = ROOT / "data" / "processed" / "kg"

# Plausible derived-yield band per crop, in metric tons per hectare. Used
# only to break ties between editions that disagree; never to alter a value.
YIELD_BAND = {
    "Aus": (0.5, 6), "Aman": (0.5, 6), "Boro": (0.8, 8), "Wheat": (0.5, 7),
    "Maize": (1.0, 16), "Potato": (4.0, 45), "Jute": (0.5, 5),
    "Lentil": (0.2, 3), "Mustard": (0.2, 3), "Onion": (1.5, 30),
    "Garlic": (1.0, 20), "Chili": (0.2, 20), "Groundnut": (0.3, 6),
    "Mung": (0.15, 3), "Gram": (0.15, 3), "Sugarcane": (8.0, 90),
}

# Chili is not one series. Through 2019-20 the yearbooks report dry chili at
# 1.2-1.6 t/ha; from 2020-21 they report green chili, which is harvested wet
# and runs 3.8-6.0 t/ha. The two are not comparable, so chili rows from the
# break onward carry a flag and are excluded from temporal questions. The
# Chili ceiling above is set to 20 so that green-chili rows are not
# misreported as garbled cells.
CHILI_SERIES_BREAK = "2020-21"


def plausible(crop, prod, area_acres):
    """True if the derived yield falls in the crop's plausible band."""
    band = YIELD_BAND.get(crop)
    if band is None or not area_acres or area_acres <= 0:
        return None
    if prod is None or not pd.notna(prod) or prod <= 0:
        return None
    y = prod / (area_acres * 0.404686)
    return band[0] <= y <= band[1]


def main():
    frames = []
    for f in sorted(glob.glob(str(BBS / "yield_*.csv"))):
        df = pd.read_csv(f)
        frames.append(df)
    all_df = pd.concat(frames, ignore_index=True)
    all_df["edition"] = all_df["edition"].astype(int)

    adm2 = pd.read_excel(ROOT / "data" / "external" / "bgd_admin_boundaries.xlsx",
                         sheet_name="bgd_admin2")[["adm2_name", "adm2_pcode"]]
    pcode = dict(zip(adm2["adm2_name"], adm2["adm2_pcode"]))

    rows, flagged = [], 0
    for (crop, yr, dist), g in all_df.groupby(["crop", "crop_year", "district"]):
        g = g.sort_values("edition")
        med = g["production_mt"].median()
        agree = g[(g["production_mt"] - med).abs() <= 0.02 * max(abs(med), 1)]
        flag = ""
        if len(agree):
            r = agree.iloc[-1]
        elif len(g) > 1:
            # No edition agrees with the median: the two-edition case, or a
            # genuine three-way split. Prefer a plausible candidate over the
            # merely newest one, and flag either way.
            ok = [i for i, row in g.iterrows()
                  if plausible(crop, row["production_mt"], row["area_acres"])]
            if ok and len(ok) < len(g):
                r = g.loc[ok[-1]]
                flag = "edition-disagreement-implausible-rejected"
            else:
                r = g.iloc[-1]
                flag = "edition-disagreement-unresolved"
            flagged += 1
        else:
            r = g.iloc[-1]
        if len(g) > 1 and not flag and r["edition"] != g.iloc[-1]["edition"]:
            flag = "newest-edition-outlier-rejected"
            flagged += 1
        area = r["area_acres"]
        prod = r["production_mt"]
        # always derive yield from production/area (1 acre = 0.404686 ha):
        # the printed yield columns mix maund/acre, kg/acre and mt/ha across
        # editions (bales for jute), so the derived figure is the only one
        # that is internally consistent
        y = None
        if area and area > 0 and prod is not None and pd.notna(prod):
            y = prod / (area * 0.404686)
        rows.append({
            "crop": crop, "crop_year": yr,
            "district_pcode": pcode[dist], "district": dist,
            "area_acres": area, "production_mt": prod,
            "yield_mt_per_ha": round(y, 3) if y is not None and pd.notna(y) else None,
            "edition_used": int(r["edition"]),
            "n_editions": len(g), "flag": flag,
        })
    panel = pd.DataFrame(rows)

    # Cells whose derived yield is physically implausible. Every edition
    # reproduces these, and inspecting the district time series shows a
    # stable area with production spiking in a single year, so the
    # production figure is garbled and the true value is unrecoverable.
    # They are flagged for exclusion, never rewritten.
    def _implausible(row):
        band = YIELD_BAND.get(row["crop"])
        y = row["yield_mt_per_ha"]
        return bool(band and y is not None and pd.notna(y) and y > band[1])

    imp = panel.apply(_implausible, axis=1)
    panel.loc[imp, "flag"] = (panel.loc[imp, "flag"].astype(str)
                              .str.strip(";") + ";implausible-yield").str.lstrip(";")
    print(f"{int(imp.sum())} rows flagged with an implausible derived yield")

    # Chili changes definition mid-panel; see CHILI_SERIES_BREAK.
    chili = (panel["crop"] == "Chili") & (panel["crop_year"] >= CHILI_SERIES_BREAK)
    panel.loc[chili, "flag"] = (panel.loc[chili, "flag"].astype(str)
                                .str.strip(";") + ";chili-green-series").str.lstrip(";")
    print(f"{int(chili.sum())} chili rows flagged as the green-chili series")
    # flag >10x year-over-year production jumps (both sides nonzero): these
    # are almost always thousand-unit slips in one yearbook edition
    panel = panel.sort_values(["crop", "district", "crop_year"])
    prev = panel.groupby(["crop", "district"])["production_mt"].shift()
    ratio = panel["production_mt"] / prev
    jump = ((prev > 0) & (panel["production_mt"] > 0)
            & ((ratio > 10) | (ratio < 0.1)))
    panel.loc[jump, "flag"] = (panel.loc[jump, "flag"].replace("", pd.NA)
                               .fillna("") .astype(str)
                               .str.rstrip(";") + ";yoy-jump-gt-10x")
    panel["flag"] = panel["flag"].str.lstrip(";")
    print(f"{int(jump.sum())} rows flagged for >10x year-over-year jumps")
    OUT.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT / "production.csv", index=False)
    yrs = sorted(panel["crop_year"].unique())
    print(f"panel: {len(panel)} rows, {panel['crop'].nunique()} crops, "
          f"{panel['district'].nunique()} districts, {len(yrs)} years "
          f"({yrs[0]}..{yrs[-1]}), {flagged} newest-edition outliers rejected")
    cov = panel.pivot_table(index="crop_year", values="crop",
                            aggfunc="nunique")
    print(cov.to_string())


if __name__ == "__main__":
    main()
