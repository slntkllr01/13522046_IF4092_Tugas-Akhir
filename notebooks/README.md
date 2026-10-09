# Notebooks

Fourteen Google Colab notebooks: one per model and domain. The two domains share the same probing pipeline and differ in the data identifiers (food versus instrument) and in a few cells listed below.
The section titles inside the notebooks are in Indonesian; they are quoted as written, with an English gloss.

## Notebook index

All 14 notebooks contain stored outputs. The last column counts code cells with at least one output.

| Model | Domain | Notebook | `MODEL_ID` (read from the code) | Cells with output |
|---|---|---|---|---|
| Qwen2.5-3B | culinary | `culinary/qwen_kuliner_with_SD_layerwise.ipynb` | `Qwen/Qwen2.5-3B` | 35 of 37 |
| Llama-3.2-3B | culinary | `culinary/llama_kuliner_with_SD_layerwise.ipynb` | `meta-llama/Llama-3.2-3B` | 36 of 38 |
| gemma-3-4b-pt | culinary | `culinary/gemma_kuliner_with_SD_layerwise.ipynb` | `google/gemma-3-4b-pt` | 36 of 38 |
| sarvam-1 | culinary | `culinary/sarvam_kuliner_with_SD_layerwise.ipynb` | `sarvamai/sarvam-1` | 35 of 37 |
| Ministral-3-3B-Base-2512 | culinary | `culinary/mistral_kuliner_with_SD_layerwise.ipynb` | `mistralai/Ministral-3-3B-Base-2512` | 35 of 37 |
| kanana-nano-2.1b-base | culinary | `culinary/kanana_kuliner_with_SD_layerwise.ipynb` | `kakaocorp/kanana-nano-2.1b-base` | 35 of 37 |
| CroissantLLMBase | culinary | `culinary/croissantLLM_kuliner_with_SD_layerwise.ipynb` | `croissantllm/CroissantLLMBase` | 35 of 37 |
| Qwen2.5-3B | instrument | `instrument/qwen_musik_with_SD_layerwise.ipynb` | `Qwen/Qwen2.5-3B` | 33 of 34 |
| Llama-3.2-3B | instrument | `instrument/llama_musik_with_SD_layerwise.ipynb` | `meta-llama/Llama-3.2-3B` | 34 of 35 |
| gemma-3-4b-pt | instrument | `instrument/gemma_musik_with_SD_layerwise.ipynb` | `google/gemma-3-4b-pt` | 34 of 35 |
| sarvam-1 | instrument | `instrument/sarvam_musik_with_SD_layerwise.ipynb` | `sarvamai/sarvam-1` | 33 of 34 |
| Ministral-3-3B-Base-2512 | instrument | `instrument/mistral_musik_with_SD_layerwise.ipynb` | `mistralai/Ministral-3-3B-Base-2512` | 33 of 34 |
| kanana-nano-2.1b-base | instrument | `instrument/kanana_musik_with_SD_layerwise.ipynb` | `kakaocorp/kanana-nano-2.1b-base` | 33 of 34 |
| CroissantLLMBase | instrument | `instrument/croissantLLM_musik_with_SD_layerwise.ipynb` | `croissantllm/CroissantLLMBase` | 33 of 34 |

The model IDs agree with `results/summary/tables/_sumber_notebook.csv`. All cells are code cells.

## Cell order

The same sequence is used in every notebook (titles as printed in the first comment lines of each cell):

| Block | Section title | Content |
|---|---|---|
| Setup | SETUP — Instalasi Pustaka | `pip install` of the libraries (see "Runtime" for model-specific differences). |
| Setup | SETUP — login hugging-face (gemma and llama only) | `notebook_login()` for gated models. |
| Setup | SETUP — Mount Google Drive | Mounts Drive. |
| Setup | SETUP — Import dan Konfigurasi Global | `MODEL_ID`, Drive file IDs of the datasets, prompt template, `SAVE_DIR`, cache file names. |
| Setup | SETUP — Pemuatan Model dan Tokenizer | Loads the model in 4-bit NF4. |
| Setup | SETUP — Pemuatan Dataset | Loads the dataset CSVs, parses country labels, tokenises artefact names. |
| Setup | SETUP — Utilitas Bersama | `safe_forward` and other shared helpers. |
| Setup | SETUP — Utilitas Probing Sferis (culinary only) | Latitude/longitude to 3D vector helpers and great-circle error. |
| Control | EKSPERIMEN KONTROL — Ekstraksi Representasi Berbasis Prompt, Pemeriksaan Sanity, Probing Linear (Agregat-Negara), Analisis Akurasi Regional, Visualisasi Peta | Prompt-based condition. |
| A | EKSPERIMEN A — Ekstraksi Pure Embedding dan Clustering, Probing Linear (Inklusif, Agregat-Negara), Analisis Akurasi Regional, Visualisasi Peta | Name-only embeddings; Aggregate probe. |
| Baseline | BASELINE EKSKLUSIF — Probing Linear, Analisis Akurasi Regional | Artefacts with a single country only. |
| B | EKSPERIMEN B — Probing Linear (Individual), Konstruksi DataFrame, Visualisasi Peta, Fungsi Visualisasi Peta Per-Negara | Individual probe. |
| C | EKSPERIMEN C.1 to C.4 (with a spherical-geometry helper cell) | Regional centroid, bias ratio, bias direction, normalised error and structure correlation. |
| D | EKSPERIMEN D — Probing Region-Balanced, Visualisasi Perbandingan, Ringkasan Effect Size and Ranking (the last two: culinary only) | Region-balanced probe and comparison. |
| Baselines | BASELINE — Prediktor Nihil; BASELINE — Static Embedding; summary print | Null predictor and static-embedding baselines. |
| Layer-wise | LAYER-WISE 0 — Ekstraksi Pure Embedding SEMUA Layer | Stores all hidden states and applies the final norm to layers 0 to N-1. |
| Layer-wise | LAYER-WISE 1 — Linear Probing per Layer (Agregat + Individual) | Per-layer probes, tables and figures. |
| Export | final cell | Zips all PNG files in the working directory and triggers a download. |

### Differences between the two domains

Found by comparing the section titles of `qwen_kuliner_with_SD_layerwise.ipynb` (37 cells) and `qwen_musik_with_SD_layerwise.ipynb` (34 cells):

- The culinary notebooks have a separate "Utilitas Probing Sferis (versi awal)" cell and a "HELPER: Koordinat Sferis" cell; the instrument notebooks have one "EKSPERIMEN C — Utilitas Geometri Sferis" cell.
- The culinary notebooks have two extra Experiment D cells ("Ringkasan Effect Size per Wilayah", "Ranking Perbandingan Centroid_Distance").
- Data names differ: `food_kb_df` / `countries` column versus `instrument_df` / `country` column (long format), and `pure_food_cache` versus `pure_instrument_cache`.
- The prompt template differs: "The most popular traditional food in {country} is" versus "The most iconic traditional musical instrument from {country} is".
- The gemma and llama notebooks (both domains) have one extra cell for the Hugging Face login.

## Runtime

- Colab GPU: the stored output of every notebook prints `GPU: Tesla T4` and `VRAM: 15.6 GB`; the notebook metadata lists a T4 accelerator.
- Models are loaded with `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)`.
- Installation cell: most notebooks run `pip install transformers accelerate bitsandbytes pandas matplotlib scipy`.
  The kanana notebooks add `-U "huggingface_hub<0.30"`. The mistral notebooks uninstall `transformers`, install it from the Hugging Face GitHub repository, and install `mistral-common`.
  No library versions are pinned in the notebooks. `geopandas` is imported in the probing cells and is not in the installation cell.
- Where the extraction ran, the cell "LAYER-WISE 0" printed its duration: between 99 s (CroissantLLMBase, instrument) and 352 s (gemma, culinary).

## Inputs and outputs

**Inputs.** The dataset CSV files are downloaded from Google Drive file IDs set in "SETUP — Import dan Konfigurasi Global" (copies are in [`../dataset/`](../dataset/README.md)).
Cached features are read from `SAVE_DIR` if present: `/content/drive/MyDrive/Percobaan TA/Food KB/Data/` (culinary) or `/content/drive/MyDrive/Percobaan TA/Instrument/Data/` (instrument).
Gated models (gemma, llama) require a Hugging Face account with access to the model.

**Outputs written to `SAVE_DIR`:**

| File | Written by |
|---|---|
| `<model>_country_layer_repr.pkl` or `<model>_country_instrument_repr.pkl` | EKSPERIMEN KONTROL — Ekstraksi Representasi Berbasis Prompt |
| `<model>_pure_food_cache.pkl` or `<model>_pure_instrument_cache.pkl` | EKSPERIMEN A — Ekstraksi Pure Embedding dan Clustering |
| `<model>_pure_food_alllayers_fp16.npy` or `<model>_pure_instrument_alllayers_fp16.npy`, and `*_names.json` | LAYER-WISE 0 |
| `<ModelName>_<domain>_layerwise_{agregat,individual}.csv` and `_{error,r2,region_heatmap}.png` | LAYER-WISE 1 (see [`../results/layerwise/`](../results/layerwise/README.md)) |

Large-file details: [`../data_external/README.md`](../data_external/README.md).

**Outputs written to the Colab working directory (`/content/`):** figure PNG files (culinary: `pure_embedding_geography.png`, `food_concept_world_map.png`, `control_map_<region>.png`, `flavor_map_full_<region>.png`, `pure_probing_<region>.png`, `robustness_balanced_probing.png`;
instrument: `pure_embedding_geography_instrument.png`, `instrument_concept_world_map.png`, `control_map_instrument_<region>.png`, `instrument_map_full_<region>.png`, `pure_probing_<region>.png`,
`robustness_balanced_probing_instrument.png`) and, from the last cell, `<model>_all_visualization_maps.zip` (culinary) or `<model>_musik_all_visualization_maps.zip` (instrument), which the cell downloads.
The PNG files are stored under [`../results/figures/`](../results/figures/).

**Known detail.** `mistral_kuliner_with_SD_layerwise.ipynb` sets the all-layer cache file name to `sarvam_pure_food_alllayers_fp16.npy`; see [`../data_external/README.md`](../data_external/README.md).

## Opening in Colab

Either upload the `.ipynb` file at <https://colab.research.google.com> (File, Upload notebook), or open it from GitHub, for example:

```
https://colab.research.google.com/github/slntkllr01/13522046_IF4092_Tugas-Akhir/blob/main/notebooks/culinary/qwen_kuliner_with_SD_layerwise.ipynb
```

Select a T4 GPU runtime, then run the cells in order. The notebooks expect the data and cache folders under `MyDrive/Percobaan TA/` as described above;
to run elsewhere, change `SAVE_DIR` and the dataset loading in "SETUP — Import dan Konfigurasi Global".
