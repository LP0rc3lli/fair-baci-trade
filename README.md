# fair-baci-trade

FAIRification project for the *FAIR Data Engineering* course (University of Twente, Group 13): turning a slice of the CEPII-BACI international trade dataset into FAIR(er) linked data, with an RDF mapping, a mini ontology, W3ID persistent identifiers, and a FAIR Data Point holding the metadata.

## The dataset

[CEPII BACI](https://www.cepii.fr/CEPII/en/bdd_modele/presentation.asp?id=37) is a bilateral international trade database built by CEPII from UN Comtrade, giving trade flows between ~200 countries at the HS 6-digit product level. This project uses release **202601** (22 January 2026), HS revision **HS22**, year **2023**.

**Slice**: world trade in **semiconductor manufacturing inputs — doped wafers and chip-making machinery**, defined by two HS6 codes:

- `381800` — *"Chemical elements: doped for use in electronics, in the form of discs, wafers or similar forms: chemical compounds doped for use in electronics"* (quoted verbatim from the HS22 product nomenclature)
- `848620` — *"Machines and apparatus of a kind used solely or principally for the manufacture of semiconductor devices or of electronic integrated circuits"*

3,184 trade flows total (119 exporting trade-partner areas, 180 importing, 2,198 distinct pairs), world → world, no exporter/importer filtering. The slice contains **no finished chips** and makes no claims about specific firms, equipment types, or the effects of export controls — BACI cannot identify any of those, and a single year cannot show cause. Code `490` ("Asia, not elsewhere specified"), CEPII's documented proxy for Taiwan, is kept as its own trade-partner area and never mapped to a country.

The exact slice definition lives in [`workflow/config.yaml`](workflow/config.yaml) — changing it should only require editing that file.

## What's in this repository

| Path | Contents |
|---|---|
| `data/original/` | The original (non-FAIR) BACI slice and lookup tables, as downloaded/extracted |
| `data/fairified/` | The FAIRified RDF/Turtle output (one combined graph) |
| `ontology/` | A small Protégé-authored ontology (`TradeFlow`, `TradePartnerArea` classes and their properties) |
| `mapping/` | OpenRefine operation-history exports and the RDF skeletons used to triplify the data |
| `metadata/schemas/` | The Dataset and Distribution SHACL metadata schemas, exported from the FAIR Data Point |
| `metadata/records/` | The 4 metadata records (1 catalog + 1 dataset + 2 distributions), exported as Turtle from the FAIR Data Point |
| `fdp/` | Docker Compose + config for running a local FAIR Data Point against a GraphDB triple store |
| `workflow/` | The Snakemake pipeline (slice definition, lookups, measurements) |
| `queries/` | Competency questions and (optional) SPARQL |
| `report/` | The project report |

## Identifiers

Persistent identifiers use [W3ID](https://w3id.org/), under the course's namespace `FAIR-course-UT/2026/group13/`:

- **Ontology**: `https://w3id.org/FAIR-course-UT/2026/group13/ont`
- **Data base URI**: `https://w3id.org/FAIR-course-UT/2026/group13/data#`
- **Original distribution**: `https://w3id.org/FAIR-course-UT/2026/group13/dataset/original`
- **FAIRified distribution**: `https://w3id.org/FAIR-course-UT/2026/group13/dataset/fairified`

All four resolve (303 See Other) to the corresponding raw files in this GitHub repository. The redirect rules live in the course's [`pid-relay`](https://github.com/luizbonino/pid-relay) repository, under `rules/FAIR-course-UT/2026/group13/`.

## FAIR Data Point

A local [FAIR Data Point](https://github.com/FAIRDataTeam/FAIRDataPoint) (v1.18) holds the Dataset and Distribution metadata records. To run it locally:

1. Install [GraphDB Desktop](https://graphwise.ai/components/graphdb/) (free, requires a license key) and create a repository named `fdp`, plus a user `fdp`/`fdp` with write access to it.
2. From `fdp/`, run:
   ```bash
   docker compose up -d
   ```
3. Open the client at [http://localhost](http://localhost).

See `fdp/docker-compose.yml` and `fdp/application.yml` for the exact configuration.

## Licensing

- **Code** (`workflow/`): MIT — see [`LICENSE`](LICENSE).
- **Data distributions derived from BACI** (original and FAIRified): [Etalab Open Licence 2.0](https://spdx.org/licenses/etalab-2.0), the source dataset's own licence, with attribution.
- **Attribution**: *CEPII BACI, release 202601 (22 January 2026), downloaded from [cepii.fr](https://www.cepii.fr/CEPII/en/bdd_modele/presentation.asp?id=37). Licensed under Etalab Open Licence 2.0.*
- Cite as: Gaulier, G. and Zignago, S. (2010), *BACI: International Trade Database at the Product-Level. The 1994-2007 Version.* CEPII Working Paper N°2010-23.

## Reproducing the slice

1. Download the BACI HS22 release 202601 zip from the [CEPII BACI page](https://www.cepii.fr/CEPII/en/bdd_modele/presentation.asp?id=37) and unzip it into `data/raw/` (not committed — see `.gitignore`), so that `data/raw/BACI_HS22_Y2023_V202601.csv`, `data/raw/country_codes_V202601.csv`, and `data/raw/product_codes_HS22_V202601.csv` exist.
2. From the repository root (the `Snakefile` and `config.yaml` use paths relative to it):
   ```bash
   pip install -r workflow/requirements.txt
   snakemake -s workflow/Snakefile --cores 1
   ```

This regenerates `data/original/` (the slice and lookup tables) from the raw files, using the parameters in `workflow/config.yaml`.
