"""Measure candidate HS6 products in one BACI year (read-only; nothing is filtered into a slice).

Writes two tables to data/intermediate/:
  - candidate_measurements_*.csv : each code alone + each configured combination
  - candidate_flows_*.csv        : the candidate rows only, as the input for the 490/n.e.s. rule

All columns are read as strings, then converted explicitly, so leading zeros in `k` survive.
"""
import csv
import sys

import pandas as pd

raw_csv = snakemake.input.raw
out_measure = snakemake.output.measurements
out_flows = snakemake.output.flows
products = [str(p) for p in snakemake.config["products"]]
combos = [[str(c) for c in combo] for combo in snakemake.config["measurement"]["combinations"]]
row_limit = int(snakemake.config["measurement"]["row_limit"])

for combo in combos:
    missing = [c for c in combo if c not in products]
    if missing:
        sys.exit(f"Combination {combo} uses codes not in `products`: {missing}")

# Stream the big file in chunks; keep only candidate rows.
parts = []
total_rows = 0
for chunk in pd.read_csv(raw_csv, dtype=str, keep_default_na=False, chunksize=2_000_000):
    total_rows += len(chunk)
    parts.append(chunk[chunk["k"].isin(products)])
flows = pd.concat(parts, ignore_index=True)

# Header check (quality gate from PROJECT_CONTEXT section 10).
assert list(flows.columns) == ["t", "i", "j", "k", "v", "q"], f"unexpected header: {list(flows.columns)}"
assert flows["k"].str.len().eq(6).all(), "k is not always 6 characters"

flows["v_num"] = pd.to_numeric(flows["v"], errors="raise")
# q: how missing shows up is not documented, so keep the raw token and classify explicitly.
q_raw = flows["q"].str.strip()
flows["q_num"] = pd.to_numeric(q_raw, errors="coerce")
flows["q_blank"] = q_raw.eq("")
flows["q_unparsable"] = flows["q_num"].isna() & ~flows["q_blank"]
flows["q_zero"] = flows["q_num"].eq(0)
flows["q_neg"] = flows["q_num"].lt(0)

flows.drop(columns=["v_num", "q_num", "q_blank", "q_unparsable", "q_zero", "q_neg"]).to_csv(
    out_flows, index=False, quoting=csv.QUOTE_NONNUMERIC
)


def describe(label, codes):
    d = flows[flows["k"].isin(codes)]
    n = len(d)
    bad_q = d["q_blank"] | d["q_unparsable"] | d["q_zero"]
    return {
        "scope": label,
        "codes": "+".join(codes),
        "rows": n,
        "over_limit_by": max(0, n - row_limit),
        "exceeds_limit": n > row_limit,
        "distinct_exporters": d["i"].nunique(),
        "distinct_importers": d["j"].nunique(),
        "distinct_dyads": d[["i", "j"]].drop_duplicates().shape[0],
        "distinct_pairs_with_product": d[["i", "j", "k"]].drop_duplicates().shape[0],
        "total_value_kUSD": round(d["v_num"].sum(), 3),
        "q_blank_rows": int(d["q_blank"].sum()),
        "q_unparsable_rows": int(d["q_unparsable"].sum()),
        "q_zero_rows": int(d["q_zero"].sum()),
        "q_negative_rows": int(d["q_neg"].sum()),
        "share_q_missing_or_zero": round(bad_q.mean(), 6) if n else None,
        "duplicate_t_k_i_j_rows": int(d.duplicated(["t", "k", "i", "j"]).sum()),
        "distinct_years": d["t"].nunique(),
    }


rows = [describe(f"alone:{c}", [c]) for c in products]
rows += [describe("combo:" + "+".join(c), c) for c in combos]
pd.DataFrame(rows).to_csv(out_measure, index=False)
print(f"scanned {total_rows:,} raw rows; candidate rows kept: {len(flows):,}")
