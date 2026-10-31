# Competency questions

## CQ1 — answerable from the dataset alone

> Which trade-partner areas were the top exporters of doped wafers (HS 381800) and
> chip-making machinery (HS 848620) in 2023?

Runs entirely against the FAIRified data (GraphDB repository `fdp`), no external
source needed. See [`top_exporters.sparql`](top_exporters.sparql).

**Run against the live data**, both products. Top 10 exporters by value
(thousands of current USD):

Chip-making machinery (HS 848620):

| Rank | Area | Value |
|---|---|---|
| 1 | Netherlands | 18,209,612.747 |
| 2 | Japan | 16,388,948.511 |
| 3 | USA | 10,953,573.993 |
| 4 | Singapore | 10,901,725.416 |
| 5 | Malaysia | 3,267,317.876 |
| 6 | Other Asia, nes | 2,534,255.015 |
| 7 | China | 2,141,071.947 |
| 8 | Rep. of Korea | 2,039,025.428 |
| 9 | Germany | 1,579,751.762 |
| 10 | Austria | 1,191,507.130 |

Doped wafers / chemical compounds (HS 381800):

| Rank | Area | Value |
|---|---|---|
| 1 | China | 7,031,332.491 |
| 2 | Japan | 4,922,772.090 |
| 3 | USA | 1,741,677.131 |
| 4 | Other Asia, nes | 1,560,268.577 |
| 5 | Rep. of Korea | 1,086,338.919 |
| 6 | Singapore | 1,034,679.464 |
| 7 | Germany | 1,003,549.444 |
| 8 | France | 694,982.094 |
| 9 | Viet Nam | 594,804.496 |
| 10 | Malaysia | 306,632.190 |

## CQ2 — requires integration with Wikidata

> Which of the top importers of doped wafers (HS 381800) and chip-making
> machinery (HS 848620) also have the highest GDP?

Not answerable from BACI alone since BACI has no economic-indicator data at all. It
becomes answerable once `TradePartnerArea` entities are joined to Wikidata through
their `owl:sameAs` links, pulling nominal GDP (`wdt:P2131`).

**Linking point**: `TradePartnerArea --owl:sameAs/skos:closeMatch--> Wikidata entity`.

### A real obstacle, and how it was actually resolved

The "obvious" approach is a single federated query with a `SERVICE
<https://query.wikidata.org/sparql>` clause, run directly in GraphDB — see
[`gdp_federated.sparql`](gdp_federated.sparql). **This was actually tried and it
fails**: GraphDB's outbound HTTP client doesn't send a `User-Agent` header, and
Wikidata's query service rejects anonymous requests per its bot policy
(`org.eclipse.rdf4j.query.QueryEvaluationException: Please set a user-agent...`,
see https://w.wiki/4wJS). This isn't a mistake in the query itself — it's an
infrastructure limitation of this GraphDB instance's federation client.

**Working two-step alternative**, actually run end to end:

1. Query the local data for the top 10 importers of 848620 and their Wikidata
   `owl:sameAs` links (see the local-only half of the query, same pattern as
   `top_exporters.sparql` but on `ex:importerArea`).
2. Of those 10, 8 have a clean `owl:sameAs` match (2 don't: "Other Asia, nes",
   code 490, no link at all by design, and Hong Kong SAR, which only has
   `skos:closeMatch`, correctly excluded from a `sameAs`-only join). Query those
   8 Wikidata IDs directly against `query.wikidata.org`, with a real `User-Agent`
   header this time, for `wdt:P2131` (nominal GDP).

**Results** (GDP in current USD, taking the highest reported value
per country — several countries have more than one non-deduplicated GDP statement
in Wikidata for different years, which is itself worth noting as a data-quality
observation):

Chip-making machinery (HS 848620):

| Importer | Import value (thousands USD) | Nominal GDP (USD) |
|---|---|---|
| USA | 9,644,312.933 | 28,750,956,130,000 |
| China | 26,909,332.562 | 17,963,170,521,080 |
| Japan | 2,708,677.532 | 5,005,536,736,792 |
| Germany | 808,637.478 | 4,121,200,000,000 |
| France | 1,181,938.468 | 2,782,905,325,625 |
| Rep. of Korea | 12,467,016.912 | 1,810,955,871,381 |
| Ireland | 2,201,821.465 | 529,244,870,223 |
| Singapore | 2,860,567.817 | 466,788,539,652 |
| Other Asia, nes | 11,400,621.334 | (no Wikidata link, code 490) |
| China, Hong Kong SAR | 1,032,447.678 | (skos:closeMatch only, not owl:sameAs) |

Doped wafers / chemical compounds (HS 381800):

| Importer | Import value (thousands USD) | Nominal GDP (USD) |
|---|---|---|
| China | 2,476,025.647 | 17,963,170,521,080 |
| Rep. of Korea | 2,344,586.008 | 1,810,955,871,381 |
| Malaysia | 2,155,966.821 | 406,305,924,656 |
| USA | 1,532,346.172 | 28,750,956,130,000 |
| Thailand | 1,516,758.387 | 505,568,057,004 |
| Singapore | 1,368,882.035 | 466,788,539,652 |
| Viet Nam | 1,243,269.849 | 408,802,379,068 |
| Japan | 1,122,780.817 | 5,005,536,736,792 |
| Germany | 765,885.155 | 4,121,200,000,000 |
| Other Asia, nes | 3,155,338.110 | (no Wikidata link, code 490) |

**Answer**: in both products, the USA has by far the highest GDP among the top-10
importers, despite not always being the single largest importer by value — for
machinery it ranks 1st by value, for doped wafers only 5th. China ranks highly on
both value and GDP in both cases. Across both tables there is no strong overall
correlation between import volume and GDP: Ireland, Singapore, Malaysia, Thailand
and Viet Nam are all significant importers of one product or the other with
comparatively small GDPs, showing that import volume of these specific product
categories does not simply track overall economic size.

## Running these

1. Import `data/fairified/baci_hs22_2023_chipmaking-inputs.ttl` into a GraphDB
   repository (Import → RDF → Upload RDF files).
2. Open the repository's SPARQL tab and paste in `top_exporters.sparql`.
3. For the GDP question, use the two-step method above rather than
   `gdp_federated.sparql` directly, unless your GraphDB instance is configured to
   send a `User-Agent` on outbound `SERVICE` calls.
