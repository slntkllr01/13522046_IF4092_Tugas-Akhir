# Dataset

Input data for both domains. This folder holds four CSV files. The notebooks read the same four files from Google Drive; see "Provenance" for what is and is not verified.

| File | Size (bytes) | Rows | Domain | Role |
|---|---|---|---|---|
| `cleaned_food_kb.csv` | 2,689,149 | 2414 | culinary | One row per food item with its claiming countries. |
| `country_instrument.csv` | 47,106 | 2354 | instrument | One row per country-instrument pair (long format). |
| `country_region.csv` | 4,866 | 192 | both | Country to region label (19 distinct regions). |
| `countries_coordinates.csv` | 7,839 | 245 | both | Country to latitude and longitude. |

Row counts are data rows (header excluded), read with `pandas.read_csv`.

## Provenance

- Source of the raw food knowledge base and the instrument list: `[TODO: dataset source and citation]`.
- Licence of the raw data: `[TODO: licence]`. The `images` column of `cleaned_food_kb.csv` stores a licence string for each image (for example `CC-BY-SA 4.0`); these refer to the images only.
- The notebooks do not read this folder. The cell "SETUP 2 — Import dan Konfigurasi Global" defines Google Drive file IDs (`FOOD_KB_ID` or `INSTRUMENT_ID`, `REGION_CSV_ID`, `COORD_CSV_ID`) and the cell "SETUP 4 — Pemuatan Dataset" downloads them.
  `[CHECK: confirm that the Drive files are identical to the files in this folder]`.

## `cleaned_food_kb.csv`

2414 rows, 43 columns, 2414 unique values in `name`. Columns that hold lists are stored as strings (for example `["Indonesia"]`) and are parsed in the notebooks.
Only `name` and `countries` are used by the notebooks. "Non-null" is the number of rows that have a value.

| Column | dtype | Non-null | Used | Description |
|---|---|---|---|---|
| `name` | string | 2414 | yes | Food name (2414 unique values). Input text for the embedding. |
| `coarse_categories` | string | 2414 | no | List-string of coarse food categories. |
| `fine_categories` | string | 2414 | no | List-string of fine food categories. |
| `cuisines` | string | 2414 | no | List-string of cuisines. |
| `associated_cuisines` | string | 2414 | no | List-string of associated cuisines. |
| `area` | string | 2414 | no | List-string of area names (for example cities or provinces). |
| `countries` | string | 2414 | yes | List of claiming countries, stored as a string such as `["Indonesia"]`. Parsed by `_safe_parse_all`; the geographic label. |
| `region_1` | string | 2414 | no | First region label given in the KB (the notebooks use `country_region.csv` instead). |
| `region_2` | string | 339 | no | Second region label (mostly empty). |
| `region_3` | string | 135 | no | Third region label (mostly empty). |
| `region_4` | string | 58 | no | Fourth region label (mostly empty). |
| `region_5` | string | 18 | no | Fifth region label (mostly empty). |
| `text_description` | string | 2410 | no | Free-text description of the food. |
| `has_alias` | bool | 2414 | no | Boolean; equals `alias_count > 0` in every row. |
| `alias_words` | string | 2414 | no | List-string of alias spellings. |
| `alias_languages` | string | 2414 | no | List-string of alias languages. |
| `alias_count` | int64 | 2414 | no | Number of aliases. |
| `alias_raw_type` | string | 2407 | no | Label for how the alias field was recorded. |
| `alias_primary_word` | string | 1821 | no | First alias. |
| `alias_primary_language` | string | 1821 | no | Language of the first alias. |
| `name_normalized` | string | 2414 | no | Name after a normalisation step (equal to `name` in 54% of rows). |
| `desc_word_count` | int64 | 2414 | no | Word count of `text_description`. |
| `desc_is_too_short` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `desc_is_placeholder` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `desc_is_empty` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `desc_is_valid` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `desc_has_local_terms` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `name_has_local_terms` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `region_completeness_score` | int64 | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `has_detailed_region` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `region_has_gap` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `images` | string | 2414 | no | List-string of image records (`filename`, `url`, `license`). |
| `image_count` | int64 | 2414 | no | Number of image records. |
| `has_image` | bool | 2414 | no | Boolean; equals `image_count > 0` in every row. |
| `has_critical_missing` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `cuisine_count` | int64 | 2414 | no | Number of cuisines. |
| `is_multi_cuisine` | bool | 2414 | no | Boolean; equals `cuisine_count > 1` in every row. |
| `is_mono_national` | bool | 2414 | no | Boolean; equals `country_count == 1` in every row. |
| `country_count` | int64 | 2414 | no | Number of claiming countries. |
| `cultural_specificity_score` | float64 | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |
| `primary_area` | string | 2414 | no | Area label used as the primary one. |
| `primary_cuisine` | string | 2414 | no | Cuisine label used as the primary one. |
| `is_mi_ready` | bool | 2414 | no | Derived quality flag or score. [TODO: definition not found in this repository] |

`region_1` to `region_5` are not used: the notebooks take the region of a country from `country_region.csv`.
The `countries` column contains `Global` in 80 rows; the notebooks drop the label `Global`.

## `country_instrument.csv`

2354 data rows. The header has three fields (`country`, `name`, and an empty third name that pandas reads as `Unnamed: 2`). `country` and `name` are used.
The file is in long format: one row per country-instrument pair, so an instrument claimed by several countries appears in several rows (the largest case is `Oud`, 21 countries).
It has 1766 unique instrument names and 189 distinct values in `country`.

## `country_region.csv`

Columns `country` (192 unique) and `region`. The 19 region labels with the number of countries in each:
Western Asia 16, Western Africa 16, Caribbean 15, Eastern Africa 15, Southern Europe 13, Eastern Europe 13, Northern Europe 13, Southern America 12,
Western Europe 11, South Eastern Asia 11, Central Africa 10, Southern Asia 8, Eastern Asia 8, Northern Africa 7, Central America 7, Southern Africa 6,
Central Asia 5, Oceania 3, Northern America 3.
The notebooks use `region_mapping.get(country, "Other")`, so a country that is missing from this file gets the label `Other`.

## `countries_coordinates.csv`

Columns `name`, `latitude`, `longitude` (degrees); 245 rows with 245 unique names. The row for `U.S. Minor Outlying Islands` has empty latitude and longitude.
The notebooks build `country_coords[name] = {lat, lon}` from it. The file has entries for `North Korea` and `South Korea` but none for `Korea`, so the
manual override in the notebooks (`if "Korea" in country_coords`) does not run.

## From country labels to coordinates

1. The country labels of an item are parsed by `_safe_parse_all` (cell "SETUP 4 — Pemuatan Dataset"): list-strings are unpacked, `Korea` is split into `North Korea` and `South Korea`,
   `England`, `Wales` and `Scotland` are merged into `United Kingdom`, and duplicates are removed. The label `Global` is dropped.
2. A country is used only if it has an entry in `countries_coordinates.csv` (`country_coords`). The latitude and longitude of that entry are the target.
3. The probe predicts a 3D unit vector computed from latitude and longitude. The error is the great-circle distance in degrees (`great_circle_deg`, cell "SETUP 6 — Utilitas Probing Sferis" in the culinary notebooks).

## How the evaluation tables are built

The counts below were recomputed from the files in this folder with the parsing rules above. They agree with `Agregat_n`, `Individual_n` and `Kontrol_n` in `results/summary/00_ringkasan_per_model.csv`.

| | Culinary | Instrument |
|---|---|---|
| Rows of the input file | 2414 | 2354 (1766 unique names) |
| Countries after parsing, without `Global` | 187 | 187 |
| Of these with coordinates (control experiment, `Kontrol_n`) | 184 | 181 |
| **Aggregate** table (`Agregat_n`): countries with coordinates and at least 5 artefacts | 151 | 176 |
| **Individual** table (`Individual_n`): artefact-country pairs with coordinates | 4872 | 2314 |
| Unique artefacts in the individual table | 2333 | 1742 |
| Artefacts that appear with more than one country | 653 | 310 |

- **Aggregate.** The feature of a country is the mean of the final-layer embeddings of its artefacts; an artefact listed for several countries enters each of them.
  The threshold is `MIN_FOODS_THRESHOLD = 5` (culinary) and `MIN_INST_THRESHOLD = 5` (instrument). Evaluation: `KFold(5, shuffle=True)`, seed 42 in the main experiment and seeds 42 to 46 in the layer-wise cell.
- **Individual.** One row per artefact-country pair. Evaluation: `GroupKFold(5)` grouped by artefact name, so all copies of an artefact are in the same fold. The row weight is `1 / (number of valid countries parsed from that row)`.

## Known issues

- **Multi-country artefacts.** 653 food items (of 2333 in the individual table) and 310 instruments (of 1742) are tied to more than one country. The largest cases are `Pilaf` (34 countries) and `Oud` (21).
- **Weights differ by domain.** For food, the recomputed row weights range from 0.0294 to 1 (they are not all equal). For instruments, each row of the long-format file holds one country,
  so the same expression gives 1.0 for every row (the recomputed weights contain only the value 1.0). In the instrument individual table, an instrument with 21 countries therefore contributes 21 rows with weight 1 each.
- **Countries without coordinates are dropped:** `Eswatini`, `North Macedonia`, `South Sudan` (culinary) and `Cape Verde`, `Côte dIvoire`, `Eswatini`, `North Macedonia`, `Sao Tome and Príncipe`, `South Sudan` (instrument).
- **Extra field in `country_instrument.csv`.** Five rows (countries `Congo` and `Costa Rica`) have a third field (`Akonting`, `Simbing`, `Balafon`, `Sabaro`, `Tama`). The notebooks read only `country` and `name`, so this field is ignored.
- **Repeated pairs.** `country_instrument.csv` has 32 repeated `(country, name)` pairs.
- **Region labels.** `Cape Verde` and `Sao Tome and Príncipe` occur in the instrument file but not in `country_region.csv`.
