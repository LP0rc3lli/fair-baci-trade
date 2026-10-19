"""For each candidate product: rank and value share of code 490 and of every other
non-sovereign / n.e.s. / historical code, as exporter and as importer.

Reads the candidate rows written by measure_candidates.py and the country metadata file.
Nothing is mapped to any country; this only reports.
"""
import pandas as pd

flows = pd.read_csv(snakemake.input.flows, dtype=str, keep_default_na=False)
countries = pd.read_csv(snakemake.input.countries, dtype=str, keep_default_na=False, encoding="utf-8")
products = [str(p) for p in snakemake.config["products"]]
flows["v"] = pd.to_numeric(flows["v"])

# Classification of country codes. This is a judgement list, so it is written to the output for review.
# Category 'nes': name contains ", nes" (not elsewhere specified).
# Category 'historical': name contains "(..." i.e. a "(...YYYY)" validity marker.
# Category 'territory_or_dependency': listed by exact BACI code. Review these; the student decides.
TERRITORY_OR_DEPENDENCY = {
    16, 60, 86, 92, 136, 162, 166, 175, 184, 238, 258, 260, 275, 292, 304, 316, 344, 446, 500, 531,
    533, 534, 535, 540, 570, 574, 580, 612, 652, 654, 660, 666, 772, 796, 849, 876,
}
def classify(row):
    code, name = int(row["country_code"]), row["country_name"]
    if ", nes" in name:
        return "nes"
    if "(..." in name:
        return "historical"
    if code in TERRITORY_OR_DEPENDENCY:
        return "territory_or_dependency"
    return "sovereign_or_other"

countries["category"] = countries.apply(classify, axis=1)
countries["country_code"] = countries["country_code"].astype(str)
cat = countries.set_index("country_code")
name_of = cat["country_name"].to_dict()
cat_of = cat["category"].to_dict()

out = []
for k in products:
    d = flows[flows["k"] == k]
    total = d["v"].sum()
    for role, col in (("exporter", "i"), ("importer", "j")):
        g = d.groupby(col)["v"].agg(value="sum", rows="count").reset_index().rename(columns={col: "country_code"})
        g = g.sort_values("value", ascending=False).reset_index(drop=True)
        g["rank"] = g.index + 1
        g["share_pct"] = (100 * g["value"] / total).round(3)
        g["country_name"] = g["country_code"].map(name_of)
        g["category"] = g["country_code"].map(cat_of).fillna("NOT_IN_COUNTRY_FILE")
        g["n_countries_in_role"] = len(g)
        g["product"] = k
        g["role"] = role
        out.append(g[g["category"] != "sovereign_or_other"])
res = pd.concat(out, ignore_index=True)[
    ["product", "role", "country_code", "country_name", "category", "rank", "n_countries_in_role", "rows", "value", "share_pct"]
]
res.to_csv(snakemake.output.special, index=False)

# Also store the classification itself, so the list is reviewable and reproducible.
countries[["country_code", "country_name", "country_iso2", "country_iso3", "category"]].to_csv(
    snakemake.output.classification, index=False
)
