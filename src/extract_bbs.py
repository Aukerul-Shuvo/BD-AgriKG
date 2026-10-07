"""Extract district x crop x year area/production (and yield where given)
from BBS Yearbook of Agricultural Statistics PDFs.

Usage: python src/extract_bbs.py 2024 [2025 ...]
Reads  data/external/bbs_yearbooks/yearbook_<ed>.pdf
Writes data/processed/bbs/yield_<ed>.csv plus a validation report to stdout.

Two table families:
  A "Estimates of <crop>":       2 crop years x (area acres, area ha,
                                 yield maund/acre, yield mt/ha, production mt)
  B "Area and Production of ...": 3 crop years x (area acres, production mt)

Every table ends in a national row; division subtotal rows are interleaved.
Both are used as checksums, never as data.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "external" / "bbs_yearbooks"
OUT_DIR = ROOT / "data" / "processed" / "bbs"

# (edition, crop) pairs whose printed unit label is wrong in the source.
#
# 2021/Jute: the table header reads "Production (M. Ton)", but the figures
# are 400 lb bales. Evidence: crop year 2018-19 appears in both the 2020 and
# 2021 editions; for Bagerhat the 2020 edition reports 2,314 MT while the
# 2021 edition reports 12,063, a ratio of 5.21 against the bale constant of
# 5.511. Applying the conversion to the 2021 figure gives 2,189 MT, within
# 5% of the 2020 edition (provisional versus revised). Every other crop year
# covered by two editions agrees at a ratio of exactly 1.000. Left
# unconverted, the 2018-19 and 2019-20 jute rows enter the panel at about
# 11 t/ha against a national norm near 2.2 t/ha. Crop year 2019-20 appears
# in this edition only, so nothing else cross-checks it.
# Editions arrive as strings from the command line, so key on strings.
UNIT_OVERRIDE_BALES = {("2021", "Jute")}

# Physically implausible yields, in metric tons per hectare. These are
# detection thresholds, deliberately well above real national maxima, not
# correction factors: a cell above the ceiling is reported, never silently
# rescaled.
YIELD_CEILING = {
    "Aus": 6, "Aman": 6, "Boro": 8, "Wheat": 7, "Maize": 16, "Potato": 45,
    "Jute": 5, "Lentil": 3, "Mustard": 3, "Onion": 30, "Garlic": 20,
    "Chili": 8, "Groundnut": 6, "Mung": 3, "Gram": 3, "Sugarcane": 90,
}

# crop -> (format, title regex). Chili comes as two tables that get summed.
SPECS = {
    "Aus": ("A", r"Estimates? of (Total\s?Aus|Aus\s?\(\s?TOTAL)"),
    "Aman": ("A", r"(Estimates of Total Aman|Estimated area.{0,40}of Total Aman)"),
    "Boro": ("A", r"Estimates? of (Total\s?Boro|Boro\s?\(\s?TOTAL)"),
    "Wheat": ("A", r"Estimates? of Wheat"),
    "Potato": ("A", r"Estimates? of (Total\s?Potato|Potato\s?\(\s?TOTAL)"),
    "Jute": ("A", r"(Estimates? of Jute|Ar\s?ea and Production of Jute by)"),
    "Boro/Local": ("A", r"Estimates? of Local Boro"),
    "Boro/HYV": ("A", r"Estimates? of HYV Boro"),
    "Boro/Hybrid": ("A", r"Estimates? of Hybrid Boro"),
    "Maize": ("B", r"Area and Production of Maize \(Rabi\s*&\s*Kharif\)"),
    "Gram": ("B", r"Area and Production of\s?Gram\s?by"),
    "Lentil": ("B", r"Area and Production of Lentil"),
    "Mung": ("B", r"Area and Production of Green gram"),
    "Mustard": ("B", r"Ar\s?ea and Production of Rape (and|&) M\s?usta?rd"),
    "Groundnut": ("B", r"Area and Production of Groundnut \(Rabi\s*&\s*[Kk]harif\)"),
    "Chili/Kharif": ("B", r"Area and Production of Kharif Chili"),
    "Chili/Robi": ("B", r"Area and Production of R[ao]bi Chili"),
    "Onion": ("B", r"Area and Production of\s?Onion\s?by"),
    "Garlic": ("B", r"Area and Production of\s?Garlic\s?by"),
    "Sugarcane": ("B", r"Area and Production of\s?Sugarcane\s?by"),
}

YEAR_RE = re.compile(r"20\d\d\s*-\s*(?:20)?\d\d")


def norm_year(y):
    """'2012-2013' or '2012 - 13' -> '2012-13'."""
    a, b = re.split(r"\s*-\s*", y)
    return f"{a}-{b[-2:]}"
NATIONAL_RE = re.compile(
    r"^(bangladesh|total|grand total|national|all bangladesh)\b", re.I)
DIVISION_RE = re.compile(r"divisi?on|divison", re.I)  # incl. source typos

# BBS district spellings (any edition) -> COD-AB adm2 name. Keys are matched
# with all spaces and punctuation stripped.
ALIASES = {
    "jhallokati": "Jhalokati", "jhalakati": "Jhalokati",
    "jhalokathi": "Jhalokati", "jalakati": "Jhalokati",
    "jhalakathi": "Jhalokati",
    "coxsbazar": "Cox's Bazar", "cox": "Cox's Bazar",
    "chapainawabganj": "Chapainababganj", "chapainawabganj": "Chapainababganj",
    "nawabganj": "Chapainababganj", "nawabgonj": "Chapainababganj",
    "chapainawabgonj": "Chapainababganj",
    "barisal": "Barishal", "bogra": "Bogura",
    "chittagong": "Chattogram", "chittagang": "Chattogram",
    "chattagram": "Chattogram",
    "comilla": "Cumilla", "jessore": "Jashore",
    "maulvibazar": "Moulvibazar", "moulvibazar": "Moulvibazar",
    "maulavibazar": "Moulvibazar", "maulovibazar": "Moulvibazar",
    "netrokona": "Netrakona", "khagrachari": "Khagrachhari",
    "sathkhira": "Satkhira", "sirajgonj": "Sirajganj",
    "hobiganj": "Habiganj", "hobigonj": "Habiganj", "habigonj": "Habiganj",
    "monshiganj": "Munshiganj", "munsiganj": "Munshiganj",
    "munsigonj": "Munshiganj",
    "narayangonj": "Narayanganj", "narayangoj": "Narayanganj",
    "mymensing": "Mymensingh", "mymenshing": "Mymensingh",
    "mymensinghh": "Mymensingh",
    "panchagar": "Panchagarh",
    "tahkurgaon": "Thakurgaon",
    "laxmipur": "Lakshmipur", "laksmipur": "Lakshmipur",
    "gopalgonj": "Gopalganj", "kishoregonj": "Kishoreganj",
    "kishorganj": "Kishoreganj", "manikgonj": "Manikganj",
    "gaibanda": "Gaibandha", "kustia": "Kushtia",
    "noagaon": "Naogaon", "perojpur": "Pirojpur",
    "sunamgonj": "Sunamganj",
}

# division names as they can appear on bare-named subtotal rows
DIVISION_NAMES = {"Barishal", "Chattogram", "Dhaka", "Khulna", "Mymensingh",
                  "Rajshahi", "Rangpur", "Sylhet"}


def canon_district(name, adm2_by_norm):
    n = re.sub(r"[^a-z]", "", name.lower())
    if n in ALIASES:
        return ALIASES[n]
    return adm2_by_norm.get(n)


def num(cell):
    if cell is None:
        return None
    s = str(cell).replace("\n", "").replace(",", "").replace(" ", "").strip()
    s = s.replace("-", "0") if s in {"-", "--"} else s
    while ".." in s:
        s = s.replace("..", ".")  # BBS typo like 1114..00
    if s in {"", ".", "..", "...", "*", "**", "***"}:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def find_tables(ed):
    """Scan the edition once with pypdf; return {spec_key: page_index}."""
    reader = PdfReader(PDF_DIR / f"yearbook_{ed}.pdf")
    found = {}
    for i, page in enumerate(reader.pages):
        head = " ".join((page.extract_text() or "").split())[:300]
        for key, (_, pat) in SPECS.items():
            if key not in found and re.search(r"Table.{0,40}?" + pat, head, re.I):
                found[key] = i
    return found


def parse_values(values, ncols, partial=False):
    """Cell-joined parse first; if the count is off, retry by splitting every
    cell on whitespace (fixes cells holding two merged numbers). Returns the
    list of ncols floats or None. With partial=True (national rows, which
    sometimes have an empty trailing cell in the source), up to 2 missing
    trailing values are padded with None."""
    nums = [num(v) for v in values if str(v).strip() != ""]
    nums = [v for v in nums if v is not None]
    if len(nums) >= ncols:
        return nums[:ncols]
    tokens = []
    for v in values:
        tokens += str(v).split()
    toks = [num(t) for t in tokens]
    toks = [v for v in toks if v is not None]
    if len(toks) >= ncols:
        return toks[:ncols]
    best = max((nums, toks), key=len)
    if partial and len(best) >= ncols - 2:
        return best + [None] * (ncols - len(best))
    return None


def year_filter(years):
    """Keep the longest run of consecutive crop years, drop typo tokens like
    2007-18 or 2020-22, return chronologically ascending."""
    good = {}
    for y in years:
        a, b = int(y[:4]), int(y[-2:])
        if (a + 1) % 100 == b:
            good.setdefault(a, y)
    if not good:
        return years
    starts = sorted(good)
    best, cur = [starts[0]], [starts[0]]
    for a in starts[1:]:
        cur = cur + [a] if a == cur[-1] + 1 else [a]
        if len(cur) > len(best):
            best = cur
    return [good[a] for a in best][-3:]


def parse_table(pdf, start_page, fmt, key, ed, problems, pat=""):
    """Parse one logical table starting at start_page, following continuation
    pages until the national row. Returns (years, stride, events); events is
    an ordered list of ('district'|'division'|'national', label, nums).

    Phase 1 gathers raw rows and year tokens. Phase 2 infers the per-year
    column stride from the modal numeric-token count of numbered rows
    (A tables: 5 = acres/ha/two yields/production, 3 = old style;
    B tables: 2 = area/production, 3 = area/yield/production). Phase 3
    classifies rows, using number-sequence tracking to spot old-style
    subtotal rows that carry a bare division name, and joins label-only
    rows with the values-only row that follows them."""
    raw_rows, years = [], []
    seen_data = False
    for pg in range(start_page, min(start_page + 6, len(pdf.pages))):
        if pg > start_page:
            head = " ".join((pdf.pages[pg].extract_text() or "").split())[:200]
            if (re.search(r"Table\s*[:\d]", head)
                    and "contd" not in head.lower()
                    and not (pat and re.search(pat, head, re.I))):
                break  # a DIFFERENT table starts; ours ended
        table = pdf.pages[pg].extract_table()
        if table is None:
            continue
        hit_national = False
        for raw in table:
            cells = [(c or "").strip() for c in raw]
            flat = " ".join(c.replace("\n", " ") for c in cells)
            if not seen_data:
                for y in YEAR_RE.findall(flat):
                    y = norm_year(y)
                    if y not in years:
                        years.append(y)
            m = re.fullmatch(r"\d{1,2}", cells[0] or "") if cells else None
            if m and len(cells) >= 2:
                raw_rows.append(("numbered", int(cells[0]),
                                 cells[1].replace("\n", " ").strip(), cells[2:]))
                seen_data = True
            elif any(DIVISION_RE.search(c or "") for c in cells[:2]):
                raw_rows.append(("division", None,
                                 flat.split("Divis")[0].strip(), cells[1:]))
            elif cells and any(NATIONAL_RE.match(c.replace("\n", " ").strip())
                               for c in cells[:2] if c):
                raw_rows.append(("national", None, "NATIONAL", cells[1:]))
                hit_national = True
            else:
                raw_rows.append(("other", None, "", cells))
        if hit_national:
            break

    years = year_filter(years)
    nyears = max(len(years), 2)
    counts = {}
    for kind, n, label, values in raw_rows:
        if kind != "numbered":
            continue
        toks = [num(t) for v in values for t in str(v).split()]
        toks = [t for t in toks if t is not None]
        counts[len(toks)] = counts.get(len(toks), 0) + 1
    stride = 5 if fmt == "A" else 2
    if counts:
        mode = max(counts, key=counts.get)
        cand = mode / nyears
        if cand == int(cand) and int(cand) in ((5, 3) if fmt == "A" else (2, 3)):
            stride = int(cand)
    ncols = nyears * stride

    events = []
    pending = None  # (kind, label) awaiting a values-only row
    last_num = 0
    for kind, n, label, values in raw_rows:
        if kind == "other":
            if pending is not None:
                nums = parse_values(values, ncols,
                                    partial=(pending[0] == "national"))
                if nums is not None:
                    events.append((pending[0], pending[1], nums))
                    pending = None
                elif any(str(c).strip() for c in values):
                    pending = None
            continue
        if kind == "numbered":
            if re.search(r"region", label, re.I):
                # 'Tangail Region' is the Tangail district row in some
                # editions (single-district greater district); a true region
                # subtotal has a resetting row number instead
                if n > last_num:
                    label = re.sub(r"\s*region\s*$", "", label, flags=re.I)
                else:
                    continue
            if DIVISION_RE.search(label):
                nums = parse_values(values, ncols, partial=True)
                if nums is not None:
                    events.append(("division", label, nums))
                pending = None
                continue
            nums = parse_values(values, ncols)
            if nums is None:
                pending = ("district", label)
                continue
            if n > last_num:
                events.append(("district", label, nums))
                last_num = n
            elif label.strip() in DIVISION_NAMES or (
                    canon_district(label, {}) in DIVISION_NAMES):
                events.append(("division", label, nums))
            else:
                events.append(("district", label, nums))
                problems.append(f"{ed}/{key}: row number {n} after {last_num} "
                                f"('{label}') - check for a subtotal leak")
                last_num = n
            pending = None
            continue
        nums = parse_values(values, ncols, partial=(kind == "national"))
        if nums is None:
            pending = (kind, label)
            continue
        events.append((kind, label, nums))
        pending = None
    if pending and pending[0] == "district":
        problems.append(f"{ed}/{key}: row '{pending[1]}' never got values")
    return years, stride, events


def check_divisions(key, events, ncols, idx, problems, ed):
    """Compare each division subtotal against the district rows above it,
    additive columns only. Returns True if every division checks out (then a
    national-row mismatch is a source misprint, not an extraction error)."""
    ndiv = sum(1 for k, _, _ in events if k == "division")
    if ndiv < 8:
        problems.append(f"{ed}/{key}: only {ndiv} division rows detected, "
                        "division checks skipped")
        return False
    ok = True
    acc = [0.0] * ncols
    for kind, label, nums in events:
        if kind == "district":
            for j in range(ncols):
                acc[j] += nums[j]
        elif kind == "division":
            for j in idx:
                if nums[j] and abs(acc[j] - nums[j]) / max(nums[j], 1) > 0.02:
                    problems.append(
                        f"{ed}/{key} {label} col{j}: districts {acc[j]:.1f} "
                        f"vs subtotal {nums[j]:.1f}")
                    ok = False
            acc = [0.0] * ncols
    return ok


def rows_from_table(key, fmt, stride, years, data, adm2_by_norm, ed, problems,
                    bales=False):
    crop = key.split("/")[0]
    bale = 0.18144  # metric tons per standard 400 lb jute bale
    out = []
    for name, nums in data:
        dist = canon_district(name, adm2_by_norm)
        if dist is None:
            problems.append(f"{ed}/{key}: unknown district '{name}'")
            continue
        for yi, yr in enumerate(years):
            a = nums[yi * stride: (yi + 1) * stride]
            if len(a) < stride:
                problems.append(f"{ed}/{key} {name}: short row for {yr}")
                continue
            if fmt == "A" and stride == 5:
                # acres, hectares, maund/acre, mt/ha, production
                r = {"area_acres": a[0], "area_ha": a[1],
                     "yield_mt_per_ha": a[3], "production_mt": a[4]}
            elif stride == 3:
                # acres, yield per acre (kg), production
                ymtha = (a[1] * 2.4711 / 1000) if a[1] is not None else None
                r = {"area_acres": a[0], "area_ha": None,
                     "yield_mt_per_ha": round(ymtha, 3) if ymtha else None,
                     "production_mt": a[2]}
            else:
                # acres, production
                r = {"area_acres": a[0], "area_ha": None,
                     "yield_mt_per_ha": None, "production_mt": a[1]}
            if bales:
                # The printed yield-rate column is in the same unit as the
                # production column, so both need converting. Only
                # production was converted before, which left the per-edition
                # yield column 5.5x high for every jute table; the panel
                # masked it by rederiving yield from production and area.
                if r["production_mt"] is not None:
                    r["production_mt"] = round(r["production_mt"] * bale, 1)
                if r["yield_mt_per_ha"] is not None:
                    r["yield_mt_per_ha"] = round(r["yield_mt_per_ha"] * bale, 3)
            r.update({"crop": crop, "crop_year": yr, "district": dist,
                      "edition": ed, "src": key})
            out.append(r)
    return out


def validate(key, fmt, stride, years, events, problems, ed):
    nyears = max(len(years), 2)
    ncols = nyears * stride
    if stride == 5:
        idx = [y * 5 + k for y in range(nyears) for k in (0, 1, 4)]
    elif stride == 3:
        idx = [y * 3 + k for y in range(nyears) for k in (0, 2)]
    else:
        idx = list(range(ncols))
    data = [(l, n) for k, l, n in events if k == "district"]
    national = next((n for k, _, n in events if k == "national"), None)
    div_ok = check_divisions(key, events, ncols, idx, problems, ed)
    if national is None:
        problems.append(f"{ed}/{key}: national row not found")
    else:
        sums = [0.0] * ncols
        for _, nums in data:
            for j in range(ncols):
                sums[j] += nums[j]
        for j in idx:
            nat = national[j]
            if nat is not None and nat and abs(sums[j] - nat) / max(nat, 1) > 0.02:
                tag = ("source misprint in national row, divisions agree"
                       if div_ok else "MISMATCH")
                problems.append(
                    f"{ed}/{key} col{j}: districts {sums[j]:.0f} vs national "
                    f"{nat:.0f} ({(sums[j]-nat)/nat:+.1%}) [{tag}]")
    if len(data) != 64:
        problems.append(f"{ed}/{key}: {len(data)} district rows (expect 64)")


def run_edition(ed, adm2_by_norm):
    problems, all_rows = [], []
    pages = find_tables(ed)
    missing = set(SPECS) - set(pages)
    for m in missing:
        problems.append(f"{ed}: table not found for {m}")
    with pdfplumber.open(PDF_DIR / f"yearbook_{ed}.pdf") as pdf:
        for key, pg in sorted(pages.items(), key=lambda kv: kv[1]):
            fmt = SPECS[key][0]
            years, stride, events = parse_table(pdf, pg, fmt, key, ed,
                                                problems, pat=SPECS[key][1])
            data = [(l, n) for k, l, n in events if k == "district"]
            if not years or not data:
                problems.append(f"{ed}/{key} p{pg}: no rows parsed")
                continue
            page_text = " ".join((pdf.pages[pg].extract_text() or "").split())
            bales = bool(re.search(r"bale", page_text, re.I))
            if (str(ed), key.split("/")[0]) in UNIT_OVERRIDE_BALES:
                if not bales:
                    problems.append(
                        f"{ed}/{key}: header declares metric tons but the "
                        "figures are bales; applying the documented unit "
                        "override (see UNIT_OVERRIDE_BALES)")
                bales = True
            if bales:
                problems.append(f"{ed}/{key}: production in bales, "
                                "converted at 181.44 kg/bale")
            validate(key, fmt, stride, years, events, problems, ed)
            all_rows += rows_from_table(key, fmt, stride, years, data,
                                        adm2_by_norm, ed, problems,
                                        bales=bales)
    df = pd.DataFrame(all_rows)
    if len(df):
        # a table printed across two pages repeats its rows: keep one copy
        df = df.drop_duplicates(subset=["crop", "crop_year", "district", "src"],
                                keep="first")
        # Boro: prefer the Total table unless the component tables cover
        # more districts (some editions have no or a truncated Total table)
        tot = df[df["src"] == "Boro"]
        comp = df[df["src"].str.startswith("Boro/")]
        if len(tot) or len(comp):
            if tot["district"].nunique() >= comp["district"].nunique():
                df = df[~df["src"].str.startswith("Boro/")]
            else:
                df = df[df["src"] != "Boro"]
        # merge the two chili tables by summing
        agg = df.groupby(["crop", "crop_year", "district", "edition"],
                         as_index=False).agg(
            area_acres=("area_acres", "sum"),
            area_ha=("area_ha", lambda s: s.sum(min_count=1)),
            yield_mt_per_ha=("yield_mt_per_ha", "mean"),
            production_mt=("production_mt", "sum"),
            n_tables=("src", "nunique"))
        # Plausibility guard. A whole crop-year sitting above its ceiling is
        # the signature of a unit error (a mislabelled bale column reads about
        # 5.5x high), which no checksum catches because the printed totals are
        # internally consistent in the wrong unit.
        for (crop, yr), grp in agg.groupby(["crop", "crop_year"]):
            ceiling = YIELD_CEILING.get(crop)
            if ceiling is None:
                continue
            # Derive yield from production and area rather than trusting the
            # printed column, so the guard still works when that column is
            # missing or carries a mislabelled unit.
            ha = grp["area_ha"].where(grp["area_ha"].notna(),
                                      grp["area_acres"] * 0.404686)
            ylds = (grp["production_mt"] / ha).replace([float("inf")], None)
            ylds = ylds.dropna()
            ylds = ylds[ylds > 0]
            if len(ylds) < 5:
                continue
            over = (ylds > ceiling).mean()
            if over > 0.5:
                problems.append(
                    f"{ed}/{crop} {yr}: UNIT SUSPECT, {over:.0%} of "
                    f"{len(ylds)} districts exceed {ceiling} t/ha "
                    f"(median {ylds.median():.1f}); check the printed unit")
            elif (ylds > ceiling).any():
                n = int((ylds > ceiling).sum())
                problems.append(
                    f"{ed}/{crop} {yr}: {n} district cell(s) above "
                    f"{ceiling} t/ha (max {ylds.max():.1f}), likely garbled")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        agg.to_csv(OUT_DIR / f"yield_{ed}.csv", index=False)
    else:
        agg = df
    return agg, problems


def main():
    eds = sys.argv[1:] or ["2024"]
    adm2 = pd.read_excel(ROOT / "data" / "external" / "bgd_admin_boundaries.xlsx",
                         sheet_name="bgd_admin2")
    adm2_by_norm = {re.sub(r"[^a-z]", "", n.lower()): n
                    for n in adm2["adm2_name"]}
    for ed in eds:
        agg, problems = run_edition(ed, adm2_by_norm)
        crops = agg["crop"].nunique() if len(agg) else 0
        yrs = sorted(agg["crop_year"].unique()) if len(agg) else []
        print(f"== {ed}: {len(agg)} rows, {crops} crops, years {yrs}")
        for p in problems:
            print("   !", p)


if __name__ == "__main__":
    main()
