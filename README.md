# Layer-wise linear probing of geographic information in language models

This repository supports a paper on layer-wise linear probing of geographic information in seven pretrained language models, in two domains:
culinary (food items) and instrument (musical instruments). Each item is linked to one or more countries and therefore to locations on Earth.
A Ridge regression probe predicts a point on the unit sphere from the hidden state of the item name, and the error is the great-circle distance in degrees.
The probe is applied to the final layer (main experiments) and to every layer (layer-wise analysis). This README describes what the repository contains and how to re-run it; it does not report or interpret results.

## Repository layout

```
.
├── README.md
├── dataset/                 4 input CSV files            -> dataset/README.md
├── notebooks/
│   ├── culinary/            7 Colab notebooks            -> notebooks/README.md
│   └── instrument/          7 Colab notebooks
├── scripts/                 extraction and verification scripts -> scripts/README_scripts.md
├── results/
│   ├── layerwise/           original Colab CSV/PNG per model (culinary/, instrument/) -> results/layerwise/README.md
│   ├── summary/             numbers extracted from notebook stdout (CSV in tables/)  -> results/summary/README_summary.md
│   └── figures/             PNG maps and probing figures, <domain>/<model>/
├── data_external/           documentation of large files (pickle/, *.npy) -> data_external/README.md
└── pickle/                  feature caches, 28 files (not published through Git; see data_external/README.md)
```

The figures in `results/figures/` are the PNG files that the notebooks write (maps per region, probing plots, concept maps); there is no separate README for them.

## Models and domains

| Model | Hugging Face model ID | Layers incl. embedding | Notebook (culinary) | Notebook (instrument) |
|---|---|---|---|---|
| Qwen2.5-3B | `Qwen/Qwen2.5-3B` | 37 | `notebooks/culinary/qwen_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/qwen_musik_with_SD_layerwise.ipynb` |
| Llama-3.2-3B | `meta-llama/Llama-3.2-3B` | 29 | `notebooks/culinary/llama_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/llama_musik_with_SD_layerwise.ipynb` |
| gemma-3-4b-pt | `google/gemma-3-4b-pt` | 35 | `notebooks/culinary/gemma_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/gemma_musik_with_SD_layerwise.ipynb` |
| sarvam-1 | `sarvamai/sarvam-1` | 29 | `notebooks/culinary/sarvam_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/sarvam_musik_with_SD_layerwise.ipynb` |
| Ministral-3-3B-Base-2512 | `mistralai/Ministral-3-3B-Base-2512` | 27 | `notebooks/culinary/mistral_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/mistral_musik_with_SD_layerwise.ipynb` |
| kanana-nano-2.1b-base | `kakaocorp/kanana-nano-2.1b-base` | 33 | `notebooks/culinary/kanana_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/kanana_musik_with_SD_layerwise.ipynb` |
| CroissantLLMBase | `croissantllm/CroissantLLMBase` | 25 | `notebooks/culinary/croissantLLM_kuliner_with_SD_layerwise.ipynb` | `notebooks/instrument/croissantLLM_musik_with_SD_layerwise.ipynb` |

Model IDs are read from `results/summary/tables/_sumber_notebook.csv`; layer counts (layer 0 is the embedding output) from `results/summary/tables/layerwise_agregat.csv`.
Models are run in 4-bit NF4 quantisation on a Colab T4 GPU. Domain names in file names and data are `kuliner` (culinary) and `musik` (instrument).

| Setting | Culinary | Instrument |
|---|---|---|
| Aggregate mode (countries) | n = 151 | n = 176 |
| Individual mode (item-country pairs) | n = 4872 | n = 2314 |

Aggregate mode uses the mean embedding per country; Individual mode uses item-country pairs with group-wise cross-validation. Definitions are in [`dataset/README.md`](dataset/README.md#how-the-evaluation-tables-are-built).

## Data

The input data are four CSV files in [`dataset/`](dataset/README.md): the food knowledge base, the country-instrument list, the country-to-region map and the country coordinates.
Their structure, the mapping from country labels to coordinates, and known data issues are documented there. The source and licence of the raw data are listed as open items in that file.

## Where the numbers come from

- `results/layerwise/` contains the original CSV and PNG outputs of the Colab notebooks. It is the **primary source for the layer-wise curves**.
- `results/summary/` contains numbers extracted from the printed output (stdout) of the notebooks, rounded as printed. It is used for the summary table and as a cross-check of the files above.

## Reproducing

**(a) Extraction and verification scripts.** They read the stored outputs of the notebooks. From the repository root, in PowerShell or bash:

```
python scripts/extract_results.py notebooks/culinary notebooks/instrument -o _tmp_tables
python scripts/verify_numbers.py   notebooks/culinary notebooks/instrument _tmp_tables
python scripts/check_consistency.py notebooks/culinary notebooks/instrument _tmp_tables
```

Expected output: `verify_numbers.py` prints `HASIL: OK: setiap angka di CSV benar-benar ada di output notebook` (every number in the CSV files exists in the notebook output), and
`check_consistency.py` prints `4815 cek dijalankan, 0 gagal` (4815 checks, 0 failures). The CSV files in `_tmp_tables` are identical to those in `results/summary/`. See [`scripts/README_scripts.md`](scripts/README_scripts.md).

**(b) Re-running the notebooks.** The notebooks are written for Google Colab with a T4 GPU and read data from Google Drive. See [`notebooks/README.md`](notebooks/README.md).

**(c) Large files.** The feature caches in `pickle/` are described, with sizes and SHA256 values, in [`data_external/README.md`](data_external/README.md). The download link is an open item there.

## Known limitations

Details and numbers are in [`results/summary/README_summary.md`](results/summary/README_summary.md#known-limitations).

- The selected RidgeCV alpha reaches the upper grid bound (500) in all 14 main Individual runs and in 86% to 100% of the layer-wise Individual fold-layer combinations
  ([details](results/summary/README_summary.md#ridgecv-alpha-at-the-grid-bound)).
- For Ministral-3-3B, the last layer in the layer-wise cell differs from the features used in the main experiments; the logged maximum feature difference is 44.8 (culinary) and 52.2 (instrument)
  ([details](results/summary/README_summary.md#ministral-3-3b-replication-mismatch)).
- Layer-wise Aggregate results use five cross-validation seeds; layer-wise Individual results come from one deterministic `GroupKFold(5)` split, so they have no seed variation
  ([details](results/summary/README_summary.md#layer-wise-evaluation-seeds)).
- In the instrument domain every Individual-mode sample weight is 1.0 (the rows are one country each), while in the culinary domain the weights are `1 / (number of countries)`
  ([details](dataset/README.md#known-issues)).

## Citation

`[TODO: paper citation / BibTeX]`

## License

`[TODO: license]` (no `LICENSE` file exists in the repository).
