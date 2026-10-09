# Layer-wise results (original Colab outputs)

This folder holds the files that the cell "LAYER-WISE 1 — Linear Probing per Layer (Agregat + Individual)" of each notebook saved to Google Drive (`SAVE_DIR`); they were copied here without editing.
**These are the primary source for the layer-wise curves.**
`results/summary/` holds numbers that were parsed from the printed output of the same notebooks (rounded as printed); it is used for cross-checking only. See [`../summary/README_summary.md`](../summary/README_summary.md).

```
results/layerwise/
├── culinary/     35 files: 7 models x (2 CSV + 3 PNG)
└── instrument/   35 files: 7 models x (2 CSV + 3 PNG)
```

## File naming

`<ModelName>_<domain>_layerwise_<kind>.<ext>`

- `<ModelName>` is the last part of the Hugging Face model ID (`MODEL_ID.split('/')[-1]` in the notebook).
- `<domain>` is `kuliner` (in `culinary/`) or `musik` (in `instrument/`); it is the `DOMAIN_TAG` set in the notebook.
- `<kind>` is `agregat`, `individual`, `error`, `r2` or `region_heatmap`.

| Model | `<ModelName>` | Rows per CSV (layers incl. embedding) |
|---|---|---|
| Qwen2.5-3B | `Qwen2.5-3B` | 37 |
| Llama-3.2-3B | `Llama-3.2-3B` | 29 |
| gemma-3-4b-pt | `gemma-3-4b-pt` | 35 |
| sarvam-1 | `sarvam-1` | 29 |
| Ministral-3-3B-Base-2512 | `Ministral-3-3B-Base-2512` | 27 |
| kanana-nano-2.1b-base | `kanana-nano-2.1b-base` | 33 |
| CroissantLLMBase | `CroissantLLMBase` | 25 |

## What each file contains

All CSV files have one row per layer; there are no per-fold rows. Fold-level information is only summarised in the two alpha columns of the Individual file.
Only the embedding-based conditions are evaluated per layer (Aggregate and Individual, on the pure name embeddings); the prompt-based control condition is not.

**Layer index.** `Layer` runs from 0 to N, where 0 is the embedding output and N is the last hidden state. The notebook applies the final RMSNorm to layers 0 to N-1, because
`hidden_states[-1]` is already normalised (the extraction cell "LAYER-WISE 0" asserts this when it runs the extraction). `Depth` is `Layer / N`, a number between 0 and 1.

**Units.** Errors (`Err*`, `SD_titik`) are great-circle distances in degrees of arc. `R2_*` are cross-validated R² values of the predicted latitude and longitude. `Alpha*` are RidgeCV penalties from the grid `[0.1, 1, 10, 50, 150, 500]`.

### `*_layerwise_agregat.csv` (one row per layer, Aggregate mode)

| Column | Meaning |
|---|---|
| `Layer`, `Depth` | Layer index and relative depth. |
| `Err_s42` | Mean great-circle error over all countries, `KFold(5, shuffle=True, random_state=42)`. This is the seed used in the main experiment. |
| `Err_mean` | Mean of the per-seed mean errors over seeds 42, 43, 44, 45, 46. |
| `Err_sd` | Standard deviation (ddof=1) of the five per-seed mean errors. |
| `SD_titik` | Standard deviation of the per-country errors for seed 42. |
| `R2_lat`, `R2_lon` | R² for latitude and longitude, averaged over the five seeds. |
| `Alpha` | Alpha that RidgeCV selects when it is fitted once on all countries (not per fold). |

### `*_layerwise_individual.csv` (one row per layer, Individual mode)

| Column | Meaning |
|---|---|
| `Layer`, `Depth` | Layer index and relative depth. |
| `Err` | Mean great-circle error over all artefact-country pairs, `GroupKFold(5)` grouped by artefact name with sample weights (deterministic split, no random seed). |
| `SD_titik` | Standard deviation of the per-pair errors. |
| `R2_lat`, `R2_lon` | R² for latitude and longitude. |
| `Alpha_med` | Median of the alpha values that RidgeCV selected in the five folds. |
| `Alpha_di_batas` | Fraction of the five folds in which the selected alpha equals the upper grid bound (500). |

The notebook parameter `LAYER_STEP_IND = 1`, so the Individual file contains every layer.

### Figures (PNG, 300 dpi; titles and axis labels are in Indonesian)

| File | Content |
|---|---|
| `*_layerwise_error.png` | Left: error per layer for both modes (Aggregate with ±1 SD across seeds), with the null-predictor and static-embedding levels when available. Right: Individual minus Aggregate error per layer. |
| `*_layerwise_r2.png` | Latitude R² and longitude R² per layer for both modes. |
| `*_layerwise_region_heatmap.png` | Mean error by region and layer, one panel per mode. |

## How to load

Run from the repository root:

```python
import pandas as pd

agg = pd.read_csv("results/layerwise/culinary/Qwen2.5-3B_kuliner_layerwise_agregat.csv")
ind = pd.read_csv("results/layerwise/culinary/Qwen2.5-3B_kuliner_layerwise_individual.csv")

best_agg = agg.loc[agg["Err_mean"].idxmin()]
best_ind = ind.loc[ind["Err"].idxmin()]
print("Aggregate : best layer", int(best_agg["Layer"]), "mean error", round(best_agg["Err_mean"], 2), "deg")
print("Individual: best layer", int(best_ind["Layer"]), "mean error", round(best_ind["Err"], 2), "deg")
print(len(agg), "layers (0 = embedding output)")
```

Output when this snippet was run:

```
Aggregate : best layer 13 mean error 15.72 deg
Individual: best layer 36 mean error 32.74 deg
37 layers (0 = embedding output)
```

## Relation to `results/summary/`

`results/summary/tables/layerwise_agregat.csv` and `layerwise_individual.csv` contain the same per-layer rows for all 14 model-domain pairs in one file each, parsed from the notebook output
(prefixed with `model`, `model_id`, `domain`, `row_order`). Values there are rounded as printed. The best layer, best error, layer-0 error, layer count and alpha-at-bound share
computed from the files in this folder agree with `00_ringkasan_per_model.csv` for all 14 pairs (to the two decimals that the notebook prints).

## Caveats

See [Known limitations](../summary/README_summary.md#known-limitations). In particular, the last-layer values of the Ministral-3-3B curves differ from the features of the main experiments
([details](../summary/README_summary.md#ministral-3-3b-replication-mismatch)).
