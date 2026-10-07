"""Build the BD-AgriKG node/relationship tables from the raw sources.

Reads:  data/raw/*.xlsx, data/external/bgd_admin_boundaries.xlsx,
        data/processed/gazetteer.csv (from build_gazetteer.py)
Writes: data/processed/kg/*.csv - one file per node label / relationship type.

Design decisions (fixes to the old Agro-KG notebook):
- Admin units are keyed on COD-AB P-codes, never on names. This removes the
  11-name collision bug (Companiganj etc.).
- Suitability is ONE relationship (Crop)-[:SUITABLE_IN]->(Upazila) carrying
  all class areas as properties, instead of per-class Suitability nodes.
- BARC rows whose Total Area is 0 get suitability_factor = empty (unknown),
  not 0 (which would falsely read as unsuitable).
- BARC units that span several COD-AB units (Dhaka Metro, pre-split Matlab)
  produce one relationship per target unit, flagged with source_span so the
  double counting is visible. Several BARC city thanas that fall in one City
  Corporation are summed into a single relationship.
- Pest sheet's "Aman Rice" is normalised to "Aman".
- Favourable-environment values live as properties on Crop, no hub node and
  no mirrored edges.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXT = ROOT / "data" / "external"
PROC = ROOT / "data" / "processed"
OUT = PROC / "kg"

CROPS = ["Aus", "Boro", "Aman", "Wheat", "Maize", "Potato", "Lentil", "Mung",
         "Gram", "Mustard", "Groundnut", "Chili", "Onion", "Garlic",
         "Sugarcane", "Jute"]

CROP_NAME_FIXES = {"Aman Rice": "Aman"}

# same real-world pest split by singular/plural in the source sheet
PEST_NAME_FIXES = {"Aphids": "Aphid",
                   "Blank Band": "Black Band"}  # source typo

# The raw Crop Calendar sheet carries several errors, corrected here against
# BRRI, BARI, BSRI and BAMIS/DAE sources. The sheet gives one sowing and one
# harvest window per crop, so for crops grown in more than one season these
# values describe the dominant season only; that simplification is recorded
# in docs/DATA_NOTES.md.
#
# Note on provenance: the three rice rows in the sheet reproduce the
# local/traditional-variety rows of the BBS rice crop calendar, not the HYV
# rows that account for the large majority of area. They are left as they
# are because they are internally consistent and correctly sourced, but the
# distinction matters when reading Aus and Boro windows.
CALENDAR_OVERRIDES = {
    # Chickpea is rabi; the sheet had Mung's kharif dates verbatim, and a
    # November harvest is impossible for a crop sown in mid-August.
    "Gram": {"sowing_time": "Mid October to End November",
             "harvest_time": "February to March"},
    # T. Aman is harvested November to December nationally. The sheet's
    # December to early January reflects late local and deepwater aman.
    "Aman": {"harvest_time": "November to December"},
    # Mid-September is far too early: the land is still under T. Aman.
    # Planting runs mid-November to early December.
    "Potato": {"sowing_time": "Mid November to Early December",
               "harvest_time": "February to March"},
    # Rabi onion transplanted December to early January is harvested March
    # to April. The sheet's late April to mid June is closer to storage and
    # marketing than to field harvest.
    "Onion": {"harvest_time": "March to April"},
    # Mid-June to mid-July matches neither Bangladeshi groundnut season.
    # The dominant season is rabi.
    "Groundnut": {"sowing_time": "Mid October to Mid November",
                  "harvest_time": "February to March"},
    # Mung matures in 60 to 70 days, so a kharif-2 sowing of mid-August to
    # late September is harvested late October to November.
    "Mung": {"harvest_time": "Late October to November"},
    # Rabi maize sowing closes in mid-November, not late December.
    "Maize": {"sowing_time": "Mid October to Mid November"},
    # Garlic needs 130 to 150 days from a mid-October to November planting.
    "Garlic": {"harvest_time": "March to April"},
    # The sheet's mid-April to mid-July sowing matches no Bangladeshi chili
    # season, and its harvest was stored as the relative phrase "3-4 months
    # after sowing" rather than a date range, which made it unusable as a
    # gold answer. These are the rabi (dry chili) windows.
    "Chili": {"sowing_time": "September to October",
              "harvest_time": "January to April"},
    # Cane occupies the land 12 to 14 months, so harvest of the previous
    # crop overlaps planting of the next; that overlap is real, not an
    # error. Harvest realistically runs November to April.
    "Sugarcane": {"harvest_time": "November to April"},
}

WEIGHTS = {"very_suitable": 1.0, "suitable": 0.8, "moderately_suitable": 0.5,
           "marginally_suitable": 0.2}


def clean(s):
    if pd.isna(s):
        return ""
    t = str(s).replace("<br>", "; ").replace("<BR>", "; ")
    return " ".join(t.split())


def admin_tables():
    xl = pd.ExcelFile(EXT / "bgd_admin_boundaries.xlsx")
    a1 = xl.parse("bgd_admin1")
    a2 = xl.parse("bgd_admin2")
    a3 = xl.parse("bgd_admin3")
    div = a1[["adm1_pcode", "adm1_name"]].rename(
        columns={"adm1_pcode": "pcode", "adm1_name": "name"})
    dist = a2[["adm2_pcode", "adm2_name", "adm1_pcode"]].rename(
        columns={"adm2_pcode": "pcode", "adm2_name": "name",
                 "adm1_pcode": "division_pcode"})
    upa = a3[["adm3_pcode", "adm3_name", "adm2_pcode", "area_sqkm",
              "center_lat", "center_lon"]].rename(
        columns={"adm3_pcode": "pcode", "adm3_name": "name",
                 "adm2_pcode": "district_pcode"})
    upa["area_sqkm"] = upa["area_sqkm"].round(2)
    return div, dist, upa


def crop_table():
    cal = pd.read_excel(RAW / "Crop Calendar.xlsx", sheet_name="Crop Calendar")
    cal["Crop"] = cal["Crop"].map(clean)
    met = pd.read_excel(RAW / "crop-meteorology.xlsx",
                        sheet_name="Favourable Environment")
    met["Crop"] = met["Crop"].map(clean)
    rows = []
    for c in CROPS:
        r = {"name": c}
        m = cal[cal["Crop"] == c]
        if len(m):
            r["sowing_time"] = clean(m.iloc[0]["Time of Sowing/Transplanting"])
            r["harvest_time"] = clean(m.iloc[0]["Time of Harvest"])
            r["seed_requirement_per_acre"] = clean(
                m.iloc[0]["Per Acre Seed Requirement"])
        for k, v in CALENDAR_OVERRIDES.get(c, {}).items():
            r[k] = v
        m = met[met["Crop"] == c]
        if len(m):
            r["favourable_temperature"] = clean(m.iloc[0]["Suitable Temparature"])
            r["favourable_humidity"] = clean(m.iloc[0]["Relative Humidity"])
            r["favourable_soil_temperature"] = clean(m.iloc[0]["Soil Temparature"])
            r["photo_period"] = clean(m.iloc[0]["Photo Period"])
            r["favourable_rainfall"] = clean(m.iloc[0]["Rainfalll"])
            r["water_requirement"] = clean(m.iloc[0]["Water Requirement"])
        rows.append(r)
    return pd.DataFrame(rows)


def suitability_table(gaz):
    gxl = pd.ExcelFile(RAW / "crop_data.xlsx")
    key = gaz.set_index(["barc_district", "barc_upazila"])
    all_rows = []
    for crop in CROPS:
        df = gxl.parse(crop)
        zone_col = [c for c in df.columns if c.endswith("Zone")][0]
        for _, r in df.iterrows():
            d, u = str(r["District Name"]).strip(), str(r["Upazila Name"]).strip()
            try:
                targets = key.loc[[(d, u)]]
            except KeyError:
                raise SystemExit(f"gazetteer missing {d}/{u} - rerun build_gazetteer")
            span = len(targets) > 1
            for _, t in targets.iterrows():
                all_rows.append({
                    "crop": crop,
                    "upazila_pcode": t["adm3_pcode"],
                    "very_suitable": r["Very Suitable"],
                    "suitable": r["Suitable"],
                    "moderately_suitable": r["Moderately Suitable"],
                    "marginally_suitable": r["Marginally Suitable"],
                    "not_suitable": r["Not Suitable"],
                    "total_area": r["Total Area"],
                    "zone": int(r[zone_col]),
                    "source_span": (u if span else ""),
                    "barc_source_name": f"{d}/{u}",
                })
    df = pd.DataFrame(all_rows)
    # BARC city thanas that map into one City Corporation: sum the areas,
    # keep the source names for provenance. zone: take min (best) and flag.
    agg = df.groupby(["crop", "upazila_pcode"], as_index=False).agg(
        very_suitable=("very_suitable", "sum"),
        suitable=("suitable", "sum"),
        moderately_suitable=("moderately_suitable", "sum"),
        marginally_suitable=("marginally_suitable", "sum"),
        not_suitable=("not_suitable", "sum"),
        total_area=("total_area", "sum"),
        zone=("zone", "min"),
        source_span=("source_span", "first"),
        barc_source_name=("barc_source_name", lambda s: "; ".join(s)),
        n_source_rows=("crop", "size"),
    )
    num = (agg["very_suitable"] * WEIGHTS["very_suitable"]
           + agg["suitable"] * WEIGHTS["suitable"]
           + agg["moderately_suitable"] * WEIGHTS["moderately_suitable"]
           + agg["marginally_suitable"] * WEIGHTS["marginally_suitable"])
    agg["suitability_factor"] = (num / agg["total_area"]).round(4)
    agg.loc[agg["total_area"] <= 0, "suitability_factor"] = None
    for c in ["very_suitable", "suitable", "moderately_suitable",
              "marginally_suitable", "not_suitable", "total_area"]:
        agg[c] = agg[c].round(1)
    return agg


def soil_tables(gaz):
    soil = pd.read_excel(RAW / "soil-type-description.xlsx")
    key = gaz.set_index(["barc_district", "barc_upazila"])
    types, links = set(), []
    for _, r in soil.iterrows():
        d, u = str(r["District"]).strip(), str(r["Upazila Name"]).strip()
        raw_types = clean(r["Soil Types"])
        if not raw_types:
            continue
        try:
            targets = key.loc[[(d, u)]]
        except KeyError:
            raise SystemExit(f"gazetteer missing soil row {d}/{u}")
        chars = clean(r["Soil Characteristics"])
        for st in [t.strip() for t in raw_types.split(",") if t.strip()]:
            types.add(st)
            for _, t in targets.iterrows():
                links.append({"upazila_pcode": t["adm3_pcode"], "soil_type": st,
                              "characteristics": chars})
    links = pd.DataFrame(links).drop_duplicates(
        subset=["upazila_pcode", "soil_type"])
    return (pd.DataFrame(sorted(types), columns=["name"]), links)


def pest_tables():
    """Crop-pest associations.

    The "Insects and Diseases" sheet of crop-meteorology.xlsx contains four
    blocks of copy-pasted associations: an identical set on wheat, maize,
    potato and lentil; an Allium set on onion, garlic and sugarcane; a
    mustard set on chili and groundnut; and mungbean's yellow mosaic on
    chickpea. Those produce associations that are simply false, such as
    Leaf Rust on potato, Purple Blotch on sugarcane and Yellow Mosaic Virus
    on chickpea.

    For the twelve affected crops we therefore use crop_pest_corrected.csv,
    compiled from the DAE Krishoker Janala crop pages with peer-reviewed
    Bangladeshi sources where those pages are thin or predate an outbreak
    (wheat blast, which reached Bangladesh only in 2016, and maize fall
    armyworm, first recorded in 2018). The rice and jute rows of the
    original sheet are crop-specific and correct, so they are kept.
    """
    p = pd.read_excel(RAW / "crop-meteorology.xlsx",
                      sheet_name="Insects and Diseases")
    p["Crop"] = p["Crop"].map(clean).replace(CROP_NAME_FIXES)
    p["Pest/Disease"] = p["Pest/Disease"].map(clean).replace(PEST_NAME_FIXES)
    p["Conditions"] = p["Conditions"].map(clean)
    bad = set(p["Crop"]) - set(CROPS)
    if bad:
        raise SystemExit(f"unknown crop names in pest sheet: {bad}")
    links = p.rename(columns={"Crop": "crop", "Pest/Disease": "pest",
                              "Conditions": "conditions"})[
        ["crop", "pest", "conditions"]]
    links["source"] = "BAMIS crop-meteorology sheet"

    corrected = pd.read_csv(RAW / "crop_pest_corrected.csv")
    unknown = set(corrected["crop"]) - set(CROPS)
    if unknown:
        raise SystemExit(f"unknown crop names in corrected pest file: {unknown}")
    replaced = sorted(set(corrected["crop"]))
    links = links[~links["crop"].isin(replaced)]
    links = pd.concat([links, corrected[["crop", "pest", "conditions",
                                         "source"]]], ignore_index=True)
    links = links.drop_duplicates(subset=["crop", "pest"])
    print(f"  pest associations: replaced {len(replaced)} crops from "
          f"crop_pest_corrected.csv, kept the sheet for "
          f"{sorted(set(links['crop']) - set(replaced))}")

    pests = pd.DataFrame(sorted(links["pest"].unique()), columns=["name"])
    return pests, links[["crop", "pest", "conditions", "source"]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gaz = pd.read_csv(PROC / "gazetteer.csv")

    div, dist, upa = admin_tables()
    div.to_csv(OUT / "divisions.csv", index=False)
    dist.to_csv(OUT / "districts.csv", index=False)
    upa.to_csv(OUT / "upazilas.csv", index=False)

    crops = crop_table()
    crops.to_csv(OUT / "crops.csv", index=False)

    suit = suitability_table(gaz)
    suit.to_csv(OUT / "suitability.csv", index=False)

    soil_types, soil_links = soil_tables(gaz)
    soil_types.to_csv(OUT / "soil_types.csv", index=False)
    soil_links.to_csv(OUT / "upazila_soil.csv", index=False)

    pests, crop_pest = pest_tables()
    pests.to_csv(OUT / "pests.csv", index=False)
    crop_pest.to_csv(OUT / "crop_pest.csv", index=False)

    print(f"divisions {len(div)}, districts {len(dist)}, upazilas {len(upa)}")
    print(f"crops {len(crops)}, suitability rels {len(suit)} "
          f"(merged {int((suit['n_source_rows'] > 1).sum())} multi-source, "
          f"span-flagged {int((suit['source_span'] != '').sum())}, "
          f"factor-null {int(suit['suitability_factor'].isna().sum())})")
    print(f"soil types {len(soil_types)}, upazila-soil rels {len(soil_links)}")
    print(f"pests {len(pests)}, crop-pest rels {len(crop_pest)}")


if __name__ == "__main__":
    main()
