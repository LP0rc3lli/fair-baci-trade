"""Extract the confirmed BACI slice and run acceptance checks.

Reads raw BACI flow file, filters strictly by the configured explicit HS6 product list,
preserves all columns as strings, and writes the original data distribution CSV.
"""
import csv
import sys
import pandas as pd

raw_csv = snakemake.input.raw
out_slice = snakemake.output.slice_csv
products = [str(p) for p in snakemake.params.products]
expected_year = str(snakemake.params.year)

print(f"Filtering {raw_csv} for products {products} and year {expected_year}...")

# Stream in chunks to be memory-efficient
parts = []
total_scanned = 0
for chunk in pd.read_csv(raw_csv, dtype=str, keep_default_na=False, chunksize=2_000_000):
    total_scanned += len(chunk)
    matched = chunk[(chunk["k"].isin(products)) & (chunk["t"] == expected_year)]
    parts.append(matched)

df = pd.concat(parts, ignore_index=True)
print(f"Scanned {total_scanned:,} raw rows; matched {len(df):,} rows.")

# ── Quality Gate Acceptance Checks ──────────────────────────────────────────
# 1. Header and columns
expected_cols = ["t", "i", "j", "k", "v", "q"]
assert list(df.columns) == expected_cols, f"Unexpected header: {list(df.columns)}"

# 2. Row count matches reference measurement
expected_rows = 3184
assert len(df) == expected_rows, f"Expected {expected_rows} rows, got {len(df)}"

# 3. Product code format (6 chars, leading zeros preserved)
assert df["k"].str.len().eq(6).all(), "Found product codes with length != 6"
assert set(df["k"].unique()) == set(products), f"Unexpected product codes: {set(df['k'].unique())}"

# 4. Single year
assert set(df["t"].unique()) == {expected_year}, f"Found multiple years: {set(df['t'].unique())}"

# 5. No duplicates on (t, i, j, k)
dups = df.duplicated(["t", "i", "j", "k"]).sum()
assert dups == 0, f"Found {dups} duplicate trade flow rows on (t, i, j, k)"

# 6. Value v must be positive numeric
v_num = pd.to_numeric(df["v"], errors="coerce")
assert v_num.notna().all(), "Found non-numeric values in v"
assert v_num.gt(0).all(), "Found non-positive values in v"

# 7. Quantity q: blank or positive numeric (never negative)
q_clean = df["q"].str.strip()
q_num = pd.to_numeric(q_clean[q_clean != ""], errors="coerce")
assert q_num.notna().all(), "Found unparsable non-empty values in q"
assert q_num.ge(0).all(), "Found negative values in q"

# Write slice CSV with standard formatting preserving strings
df.to_csv(out_slice, index=False, quoting=csv.QUOTE_MINIMAL)
print(f"Slice written successfully to {out_slice} ({len(df):,} rows).")
