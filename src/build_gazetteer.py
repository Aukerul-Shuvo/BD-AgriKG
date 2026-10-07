"""Build the canonical gazetteer that maps BARC crop-zoning (district, upazila)
names to OCHA COD-AB v03 P-codes.

Output: data/processed/gazetteer.csv with one row per BARC pair, columns:
  barc_district, barc_upazila, adm2_pcode, adm2_name, adm3_pcode, adm3_name,
  center_lat, center_lon, match_method
Unmatched rows are written to data/processed/gazetteer_unmatched.csv and the
script exits nonzero if any remain, so the pipeline fails loudly.
"""
import difflib
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COD = ROOT / "data" / "external" / "bgd_admin_boundaries.xlsx"
BARC = ROOT / "data" / "raw" / "crop_data.xlsx"
OUT = ROOT / "data" / "processed"

# Old BARC district spellings to COD-AB v03 spellings.
DISTRICT_ALIASES = {
    "BARISAL": "Barishal",
    "BOGRA": "Bogura",
    "CHITTAGONG": "Chattogram",
    "COMILLA": "Cumilla",
    "JESSORE": "Jashore",
    "JHALAKATI": "Jhalokati",
    "MAULVIBAZAR": "Moulvibazar",
    "MOULVIBAZAR": "Moulvibazar",
    "MOULVI BAZAR": "Moulvibazar",
    "NATOR": "Natore",
    "NAWABGANJ": "Chapainababganj",
    "COXS BAZAR": "Cox's Bazar",
    "COX'S BAZAR": "Cox's Bazar",
}

# Hand-reviewed cases the automatic rules cannot resolve. Keys are
# (barc_district_upper, barc_upazila); values are lists of raw COD-AB
# adm3_name values (a BARC unit that spans several COD-AB units, like
# Dhaka Metro or the pre-split Matlab, maps to more than one).
MANUAL_UPAZILA = {
    ("PIROJPUR", "Sarupkati"): ["Nesarabad (Swarupkathi)"],
    ("KHULNA", "Khulna Metro"): ["Khulna City Corporation"],
    ("MAGURA", "Sripur"): ["Sreepur"],
    ("GAZIPUR", "Sripur"): ["Sreepur"],
    ("BOGRA", "Kahalu"): ["Kahaloo"],
    ("PANCHAGARH", "Panchagar"): ["Panchagarh Sadar"],
    ("BARGUNA", "Borguna"): ["Barguna Sadar"],
    ("CHANDPUR", "Matlab"): ["Matlab Dakkhin", "Matlab Uttar"],
    ("COMILLA", "Comilla"): ["Adarsha Sadar"],
    ("LAKSHMIPUR", "Laksmipur"): ["Lakshmipur Sadar"],
    ("MYMENSINGH", "Phulpur"): ["Fulpur"],
    ("SHARIATPUR", "Palong (Sadar)"): ["Shariatpur Sadar"],
    ("SHARIATPUR", "Janjira"): ["Zajira"],
    ("CHITTAGONG", "Patenga"): ["Chattogram City Corporation"],
    ("CHITTAGONG", "Double Mooring"): ["Chattogram City Corporation"],
    ("CHITTAGONG", "Panchlais"): ["Chattogram City Corporation"],
    ("DHAKA", "Dhaka Metro"): ["Dhaka North City Corporation",
                               "Dhaka South City Corporation"],
    ("RAJSHAHI", "Boalia (Rajshahi)"): ["Rajshahi City Corporation"],
    ("SUNAMGANJ", "Sulla"): ["Shalla"],
}


def norm(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\(.*?\)", " ", s)          # drop parenthetical qualifiers
    s = s.replace("'", "").replace(".", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def squash(s: str) -> str:
    return s.replace(" ", "")


def main() -> int:
    adm3 = pd.read_excel(COD, sheet_name="bgd_admin3")
    adm3 = adm3[["adm3_name", "adm3_pcode", "adm2_name", "adm2_pcode",
                 "center_lat", "center_lon"]].copy()
    adm3["d_norm"] = adm3["adm2_name"].map(norm)
    adm3["u_norm"] = adm3["adm3_name"].map(norm)

    barc = pd.read_excel(BARC, sheet_name="Aus")[["District Name", "Upazila Name"]]
    barc = barc.drop_duplicates().reset_index(drop=True)

    rows, unmatched = [], []

    def emit(hit, d_raw, u_raw, method):
        rows.append({
            "barc_district": d_raw, "barc_upazila": u_raw,
            "adm2_pcode": hit["adm2_pcode"], "adm2_name": hit["adm2_name"],
            "adm3_pcode": hit["adm3_pcode"], "adm3_name": hit["adm3_name"],
            "center_lat": hit["center_lat"], "center_lon": hit["center_lon"],
            "match_method": method,
        })

    for _, r in barc.iterrows():
        d_raw = str(r["District Name"]).strip()
        u_raw = str(r["Upazila Name"]).strip()
        d_cod = DISTRICT_ALIASES.get(d_raw.upper(), d_raw)
        d_norm = norm(d_cod)

        cand = adm3[adm3["d_norm"] == d_norm]
        if cand.empty:
            unmatched.append((d_raw, u_raw, "district-not-found"))
            continue

        key = (d_raw.upper(), u_raw)
        if key in MANUAL_UPAZILA:
            ok = True
            for name in MANUAL_UPAZILA[key]:
                m = cand[cand["adm3_name"] == name]
                if len(m) != 1:
                    unmatched.append((d_raw, u_raw, f"manual-name-not-found:{name}"))
                    ok = False
                    break
                emit(m.iloc[0], d_raw, u_raw, "manual")
            if ok:
                continue
            else:
                continue

        u_norm = norm(u_raw)
        exact = cand[cand["u_norm"] == u_norm]
        if len(exact) == 1:
            emit(exact.iloc[0], d_raw, u_raw, "exact")
            continue

        # BARC writes the bare district name for the sadar upazila.
        sadar = cand[cand["u_norm"] == u_norm + " sadar"]
        if len(sadar) == 1:
            emit(sadar.iloc[0], d_raw, u_raw, "sadar")
            continue
        if squash(u_norm) in (squash(norm(d_raw)), squash(d_norm)):
            s = cand[cand["u_norm"].str.contains(r"\bsadar\b", regex=True)]
            if len(s) == 1:
                emit(s.iloc[0], d_raw, u_raw, "sadar")
                continue

        best = difflib.get_close_matches(u_norm, cand["u_norm"].tolist(),
                                         n=1, cutoff=0.80)
        if best:
            hit = cand[cand["u_norm"] == best[0]].iloc[0]
            emit(hit, d_raw, u_raw, f"fuzzy:{best[0]}")
        else:
            unmatched.append((d_raw, u_raw, "no-upazila-match"))

    OUT.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "gazetteer.csv", index=False)

    dup = out[out.duplicated("adm3_pcode", keep=False)].sort_values("adm3_pcode")
    print(f"matched {len(out)}/{len(barc)}  "
          f"(exact {sum(out.match_method == 'exact')}, "
          f"sadar {sum(out.match_method == 'sadar')}, "
          f"fuzzy {sum(out.match_method.str.startswith('fuzzy'))}, "
          f"manual {sum(out.match_method == 'manual')})")
    if len(dup):
        print(f"WARNING {len(dup)} rows share an adm3_pcode (collisions):")
        print(dup[["barc_district", "barc_upazila", "adm3_name", "adm3_pcode",
                   "match_method"]].to_string(index=False))
    if unmatched:
        pd.DataFrame(unmatched, columns=["district", "upazila", "reason"]).to_csv(
            OUT / "gazetteer_unmatched.csv", index=False)
        print(f"UNMATCHED {len(unmatched)}:")
        for d, u, why in unmatched:
            print(f"  {d} / {u}  ({why})")
        return 1
    print("all BARC pairs matched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
