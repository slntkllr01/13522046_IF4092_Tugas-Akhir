# Extracted results: 7 models x 2 domains (culinary, instrument)

Every number in this folder was read from the printed output (stdout) of the notebook cells by `scripts/extract_results.py`. No number was typed by hand.
The values are rounded the way the notebooks print them. For the original, unrounded layer-wise files see [`../layerwise/`](../layerwise/README.md).

In the data, the domain names are the Indonesian labels `kuliner` (culinary) and `musik` (instrument). Column suffixes such as `_err` mean the mean great-circle error in degrees.

## Re-running

From the repository root (PowerShell or bash):

```
python scripts/extract_results.py notebooks/culinary notebooks/instrument -o _tmp_tables --xlsx
python scripts/verify_numbers.py   notebooks/culinary notebooks/instrument _tmp_tables   # check 1: multiset of numbers
python scripts/check_consistency.py notebooks/culinary notebooks/instrument _tmp_tables  # check 2: column/row position and cross-checks
```

The input can be a zip file, a folder with `.ipynb` files, or a single `.ipynb` file. The extraction writes all CSV files into one flat folder (`_tmp_tables`);
in this folder they are split into the root (`00_`, `01_`, `semua_hasil.xlsx`) and `tables/` (all other CSV files). The CSV files of a fresh extraction are byte-identical to the 34 CSV files here.

## Verification (last run)

1. **Line audit.** Every output line that contains a number is either captured by the parser or ignored with a written reason (pip progress bars, extraction timings, file paths, lists of zip files).
   See `tables/_audit_ignored_lines.csv`. `tables/_audit_unparsed_lines.csv` contains a single status row (0 lines escaped). An unknown table header stops the script.
2. **`verify_numbers.py`.** For each notebook, the multiset of all numbers in the output equals the multiset of numbers in the CSV files
   (0 numbers missing, 0 numbers added). Numbers that are not results (section numbers, thresholds in explanatory text, progress counters) are excluded explicitly through a list of regular expressions in the script.
   Last line of the run: `HASIL: OK: setiap angka di CSV benar-benar ada di output notebook`.
3. **`check_consistency.py`.** 4815 checks, 0 failures. The checks are:
   - All pandas tables are parsed a second time by a different method (split from the right) and compared cell by cell. This catches values that were swapped between columns or rows, which the multiset check cannot catch.
   - Cross-checks: the same value in several tables must be identical (`Avg_Error`, `Centroid_Distance`, `Bias_Ratio`, `N_Artifacts`); the length of the bias vector must equal `Centroid_Distance`;
     the layer-wise summary must equal the argmin of the table; the sum of the regional `Count` must equal n; the list of regions must equal the `Mechanism` column.
   - Mutation test (swapping two cells, or shifting one number by 0.01, must be detected): this was stated for an earlier version of this README, but the test is not part of the scripts in `scripts/`.
     `[TODO: add the mutation-test script, or remove this statement]`

## Files in this folder

Files in the root:

| File | Content |
|---|---|
| `00_ringkasan_per_model.csv` | One row per model x domain (14 rows, 52 columns): main metrics of all conditions and the layer-wise summary. |
| `01_semua_skalar_long.csv` | All single numbers in long format (1920 rows): `model, model_id, domain, section, metric, value, cell_idx, source_line`; `source_line` is the original output line. |
| `semua_hasil.xlsx` | All tables in one workbook. |

Files in `tables/` (every table has the columns `model, model_id, domain` first; `row_order` keeps the printed order):

| File | Content |
|---|---|
| `regional_kontrol.csv`, `regional_agregat.csv`, `regional_eksklusif.csv` | Accuracy by region for the control condition, the inclusive Aggregate condition (Experiment A) and the exclusive baseline (single-country artefacts): `Count`, `Avg_Error_Deg`, `Std_Error_Deg` (not in the exclusive table), `MAE_Lat`, `MAE_Lon`. |
| `c1_centroid.csv`, `c1_centroid_distance.csv`, `c1_mekanisme.csv` | Experiment C.1: predicted and actual regional centroids, `Pred_Spread`, `Centroid_Distance`, and the `Mechanism` label. |
| `c2_bias_ratio.csv`, `c2_klasifikasi_2x2.csv`, `c2_ranking.csv` | Experiment C.2: `Bias_Ratio`, its 2x2 classification, and the ranks of `Avg_Error` versus `Bias_Ratio`. |
| `c3_bias_vector.csv`, `c3_confusion_target.csv`, `c3_salah_kira.csv` | Experiment C.3: bias vector (north, east, angle), closest confusion target per region, and the narrative lines "region was guessed as ..." (rounded to 1 decimal; checked against the full-precision tables). |
| `c4_normalized_error.csv`, `c4_structure_correlation.csv`, `c4_rank_shift.csv`, `c4_gabungan.csv`, `c4_low_error_low_discrim.csv` | Experiment C.4: normalised error, structure correlation with Mantel p-value, rank shift, the combined table, and the narrative lines on regions with low error and low discrimination (rounded to 2 and 3 decimals). |
| `d_bobot_region.csv`, `d_perbandingan.csv`, `d_effect_size.csv`, `d_ranking.csv`, `d_top10_original.csv`, `d_top10_balanced.csv` | Experiment D (region-balanced probe): weights per region, original versus balanced comparison, effect size and status, ranking, and top-10 lists. |
| `null_jarak_region.csv` | Distance of the null-predictor mean to the actual regional centroid, per region. |
| `layerwise_agregat.csv`, `layerwise_individual.csv` | Per-layer curves in the printed rounding (layer 0 = embedding output). Column meanings are in [`../layerwise/README.md`](../layerwise/README.md). |
| `layerwise_individual_progress.csv` | Progress log per layer (`Err_2dp`, cumulative seconds); only for notebooks that print a per-layer log. |
| `daftar_region.csv` | All printed lists of regions (quadrants, high/low error, `Bias_Ratio` > 0.4, and so on). |
| `kontrol_sanity_top5.csv` | The five top candidates per country in the sanity-check cell. |
| `_sumber_notebook.csv` | Source file and `MODEL_ID` of every notebook (read from the cell code). |
| `_audit_ignored_lines.csv`, `_audit_unparsed_lines.csv` | Audit of the output lines (see "Verification"). |

## Notes for reading the tables

- `Agregat_err` (Experiment A cell) is the result for seed 42. `LW_agg_last_err_mean5seed` is the mean over 5 seeds at the last layer. The two values differ by design.
- `LW_replik_*_layerwise` and `LW_replik_*_asli` are the last-layer values from the layer-wise cell and from the original cell. For Ministral-3-3B (`mistral`) they are not equal; see below.
- `Prob_as_printed` in the sanity check is the number printed with the label "Prob". Its values are larger than 1, so it is a logit or score, not a probability.
- `setup.params_B_as_printed` is the parameter count computed after 4-bit quantisation (for example Qwen 3B prints 1.70B).
- `b.n_titik` is printed twice in the culinary notebooks (same value); the conflict detector confirms that no metric has two different values.

## Known limitations

These are findings from the data, not extraction problems.

### RidgeCV alpha at the grid bound

The alpha grid is `[0.1, 1, 10, 50, 150, 500]`. The selected alpha reaches the upper bound (500) for all models, not only for Qwen:

- Main experiment, Individual mode: the selected alpha is 500 in 14 of 14 runs (`Individual_alpha` in `00_ringkasan_per_model.csv`).
- Layer-wise, Individual mode: 86% to 100% of the fold-layer combinations are at 500 (`LW_ind_pct_alpha_at_500`; 100% for 12 of the 14 pairs, 90% for sarvam culinary, 86% for sarvam instrument).
- Layer-wise, Aggregate mode (alpha fitted once on all countries): the share of layers with alpha equal to 500 ranges from 0% to 92% across the 14 pairs
  (computed from the `Alpha` column of `tables/layerwise_agregat.csv`).

### Ministral-3-3B replication mismatch

For `mistral`, the last layer in the layer-wise cell differs from the features used in the main experiments.
The maximum difference between the layer-wise features and the cache is 44.8 (culinary) and 52.2 (instrument); the other models are at most 9.8.

| | Aggregate (layer-wise vs original cell) | Individual (layer-wise vs original cell) |
|---|---|---|
| Culinary | 15.19° vs 16.26° | 37.81° vs 41.92° |
| Instrument | 21.32° vs 22.59° | 39.96° vs 41.31° |

In the culinary notebook, the "LAYER-WISE 0" cell prints "Cache lama tidak cocok ... Ekstraksi ulang" (the old cache does not match, re-extracting).
In that notebook the cache file name is `sarvam_pure_food_alllayers_fp16.npy` (see [`../../data_external/README.md`](../../data_external/README.md)).
The layer-wise curve of Ministral-3-3B is therefore not tied to its main-experiment numbers.

### Layer-wise evaluation seeds

- Aggregate mode: five cross-validation seeds (42, 43, 44, 45, 46) per layer; `Err_sd` is the standard deviation across these seeds. The main experiment uses seed 42 only.
- Individual mode: `GroupKFold(5)` is deterministic, so there is one evaluation per layer and no seed variation.
- The "best layer" columns (`LW_agg_best_*`, `LW_ind_best_*`) are the minimum over layers of the same cross-validated error that is reported, so the layer is selected and evaluated on the same data.
  The notebook prints a warning to the same effect.
