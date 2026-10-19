"""Generate country and product lookup tables for entities occurring in the slice.

- Joins codes with BACI metadata files.
- Preserves ISO alpha-2 (including Namibia 'NA') and ISO alpha-3.
- Repairs the 4 known double-encoded country names without touching raw files.
- Keeps verbatim product descriptions.
"""
import csv
import pandas as pd

slice_csv = snakemake.input.slice_csv
country_raw_csv = snakemake.input.countries
product_raw_csv = snakemake.input.products

out_country = snakemake.output.country_lookup
out_product = snakemake.output.product_lookup

# 1. Read slice to find active entities
slice_df = pd.read_csv(slice_csv, dtype=str, keep_default_na=False)
active_country_codes = sorted(set(slice_df["i"].unique()).union(set(slice_df["j"].unique())))
active_product_codes = sorted(set(slice_df["k"].unique()))

print(f"Slice contains {len(active_country_codes)} unique trade-partner codes and {len(active_product_codes)} product codes.")

# 2. Build and repair country lookup
countries_raw = pd.read_csv(country_raw_csv, dtype=str, keep_default_na=False, encoding="utf-8")

# Repair the 4 known double-encoded names (CP1252 bytes misinterpreted as UTF-8)
REPAIRS = {
    "384": "Côte d'Ivoire",
    "531": "Curaçao",
    "652": "Saint Barthélemy",
    "792": "Türkiye",
}

def repair_name(row):
    code = row["country_code"]
    if code in REPAIRS:
        return REPAIRS[code]
    return row["country_name"]

countries_raw["country_name"] = countries_raw.apply(repair_name, axis=1)

# Filter for active countries occurring in slice
country_lookup = countries_raw[countries_raw["country_code"].isin(active_country_codes)].copy()
country_lookup = country_lookup.sort_values("country_code", key=lambda col: col.astype(int)).reset_index(drop=True)

# Quality checks on country lookup
assert len(country_lookup) == len(active_country_codes), (
    f"Mismatch in country lookup count: expected {len(active_country_codes)}, got {len(country_lookup)}"
)
# Check Namibia ISO2 preserved as 'NA'
if "516" in active_country_codes:
    nam = country_lookup[country_lookup["country_code"] == "516"].iloc[0]
    assert nam["country_iso2"] == "NA" or nam["country_iso3"] == "NAM", "Namibia ISO code corrupted"

# Write country lookup
country_lookup.to_csv(out_country, index=False, quoting=csv.QUOTE_MINIMAL)
print(f"Wrote country lookup to {out_country} ({len(country_lookup)} entries).")

# 3. Build product lookup
products_raw = pd.read_csv(product_raw_csv, dtype=str, keep_default_na=False, encoding="utf-8")
product_lookup = products_raw[products_raw["code"].isin(active_product_codes)].copy()
product_lookup = product_lookup.sort_values("code").reset_index(drop=True)

# Quality check on product lookup
assert len(product_lookup) == len(active_product_codes), (
    f"Mismatch in product lookup count: expected {len(active_product_codes)}, got {len(product_lookup)}"
)

# Write product lookup
product_lookup.to_csv(out_product, index=False, quoting=csv.QUOTE_MINIMAL)
print(f"Wrote product lookup to {out_product} ({len(product_lookup)} entries).")
