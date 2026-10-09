# External data (large artefacts)

This folder only documents large files that are produced by the notebooks but are too big for normal use of the Git repository:
the `pickle/` cache folder, the `*.npy` all-layer caches, and the zip archives of figures. The files themselves are not stored here.

## Status of the files

| Item | Where it is | Download link | Notes |
|---|---|---|---|
| `pickle/food/*.pkl`, `pickle/instrument/*.pkl` (28 files, 929,852,102 bytes in total) | local `pickle/` folder; listed in `.gitignore` | `[TODO: Zenodo/HuggingFace DOI or URL]` | See the [CHECK] note on Git history below. |
| `*_pure_food_alllayers_fp16.npy`, `*_pure_instrument_alllayers_fp16.npy` and the matching `*_names.json` | written to Google Drive by the notebooks; not present in this repository | `[TODO: Zenodo/HuggingFace DOI or URL, or state that they are not published]` | Sizes as logged by the notebooks are in the second table. |
| `Culinary.zip`, `Music.zip` (notebook archives) and `*_all_visualization_maps.zip` (figure archives) | kept locally outside Git (`.gitignore` excludes `*.zip`) | `[TODO: decide whether these are published]` | The notebooks inside the zip files have the same file names as in `notebooks/`. |

**[CHECK] Git history.** The 28 pickle files were committed in `4b65f1a` (before `.gitignore` existed), so `git ls-files pickle` still lists them
and they are part of the repository history even though `.gitignore` now names `pickle/`.

## The `pickle/` files

Two files per model and domain. File names come from the `COUNTRY_FILE` and `FOOD_FILE` (instrument notebooks: `INSTRUMENT_FILE`) settings in the cell "SETUP 2 — Import dan Konfigurasi Global" of each notebook.

| File pattern | Content | Written by (section title in the notebook) |
|---|---|---|
| `pickle/food/<model>_country_layer_repr.pkl` | Prompt-based control representations for each country (`country_layer_repr`; the cell describes them as log-probability vectors over the food vocabulary, per layer) | "EKSPERIMEN KONTROL — Ekstraksi Representasi Berbasis Prompt" (culinary notebooks) |
| `pickle/food/<model>_pure_food_cache.pkl` | Dict `food name -> final-layer hidden-state vector` (`pure_food_cache`) | "EKSPERIMEN A — Ekstraksi Pure Embedding dan Clustering" (culinary notebooks) |
| `pickle/instrument/<model>_country_instrument_repr.pkl` | Same as `country_layer_repr`, for instruments | "EKSPERIMEN KONTROL — Ekstraksi Representasi Berbasis Prompt" (instrument notebooks) |
| `pickle/instrument/<model>_pure_instrument_cache.pkl` | Dict `instrument name -> final-layer hidden-state vector` (`pure_instrument_cache`) | "EKSPERIMEN A — Ekstraksi Pure Embedding dan Clustering" (instrument notebooks) |

`<model>` is one of `croissantLLM`, `gemma`, `kanana`, `llama`, `mistral`, `qwen`, `sarvam`.
Each notebook loads the file if it exists in `SAVE_DIR` and skips the extraction; otherwise it runs the model and writes the file.
Cell numbers are not given because the gemma and llama notebooks contain one extra cell (Hugging Face login), which shifts the indices.

### Files, sizes and SHA256

Computed on the local files (commands below).

| File | Content | Size (bytes) | SHA256 |
|---|---|---|---|
| `pickle/food/croissantLLM_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 43,345,302 | `58efffbe71dc67f8504637d183292572c2740f8602794233eb53508ff42c3754` |
| `pickle/food/croissantLLM_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 19,873,132 | `cb499dfd291a51ccd64d37012896a46f4d12c8483f338c30893b276f1a6cb952` |
| `pickle/food/gemma_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 61,402,022 | `57b1fe41e8250463ffeff7f9b846db89fb4e7679e8ed46dbfc6fb44cb2f3ef64` |
| `pickle/food/gemma_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 24,817,391 | `c6a02e45c9914e314ac573708bce9461fb8f6929dacb5d0eef71de0081e36311` |
| `pickle/food/kanana_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 57,790,678 | `fd26d484d47add1a46dec3c5b0f769baf73a0e981062d08c6fe7ffcda3067052` |
| `pickle/food/kanana_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 17,400,656 | `1aba98bcac1da086684fc4121ad5a7ac19e053f1d1f63f62eaf6d0426611bc26` |
| `pickle/food/llama_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 50,567,990 | `a504ed40d88baa1285b1f5ecfdf3a5d05d426e98afab649e5add339a9a830687` |
| `pickle/food/llama_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 29,761,785 | `57f21dc5b42945d64968066e7f2a0496b45bb4e1e38d1f90522419f34760e08b` |
| `pickle/food/mistral_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 46,956,646 | `d8965bcbe303914facd101edcce9105e6530c2437eddbe8808912168a7b4127e` |
| `pickle/food/mistral_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 29,761,785 | `d5b7ea2de673614ad0a3923f765ed2798449876f66aa7c65b11a8a1b8f6907e2` |
| `pickle/food/qwen_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 65,013,366 | `c1cfd0ac1b12770addfd7d8df1b185fc6e1ddffd4614f0ad0278b56900e9fc94` |
| `pickle/food/qwen_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 19,873,132 | `b3274a3571e86c4343cc8a4ab8d568052abb1e0dc42b2bc756543d378722c1a7` |
| `pickle/food/sarvam_country_layer_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 50,567,990 | `3b665e420cce677e9db7efbb86697c5bcb2af342135d21e8c597de2fdbf19ae0` |
| `pickle/food/sarvam_pure_food_cache.pkl` | Final-layer hidden state of each food name (`pure_food_cache`, dict: name -> vector) | 19,873,132 | `24879472f34b27e236e56276aa0834e925ee4a85f3085e5a830e05fff1df18d3` |
| `pickle/instrument/croissantLLM_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 31,712,423 | `db3cd11a7e8be84c285c3bc278a1561d977f3918036bb86a43717f53a8136357` |
| `pickle/instrument/croissantLLM_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 14,534,962 | `75fd3ecd48ddc9af1b82421c481a4a6a3232b5ae30dc171eb9648b73a2284309` |
| `pickle/instrument/gemma_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 44,922,103 | `9450f433a5cf4d23a94184ec2797f1f7a42f6cae84622d914c453476f732caf0` |
| `pickle/instrument/gemma_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 18,152,018 | `d45480da1afc96f3136729dddd156930f47acfce5c1bd1b128fb179f01967209` |
| `pickle/instrument/kanana_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 42,280,167 | `80c058bd321d7c303a5f184b30e56a86b43a7a4773e9055ef40c4906ee4f5813` |
| `pickle/instrument/kanana_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 12,726,182 | `bfa3bb1d4665aa4ce8503db371819c9af9ed70d533249754941c3dbf796f88cd` |
| `pickle/instrument/llama_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 36,996,295 | `01a9b782ea37d1f1397a54befa4e4e8d10fdab8d223d689ad48b49ae2969274a` |
| `pickle/instrument/llama_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 21,769,164 | `5da8f54c2212fefc7f41babae18e75035022bd5f5d00d28c1bfc18053edd1ea1` |
| `pickle/instrument/mistral_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 34,354,359 | `abcc854c5863c130c5f22a1b6ece43910ed5abef28e28c7623a67771235d1de2` |
| `pickle/instrument/mistral_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 21,769,164 | `2d8cc91154b8234d930a07d15912c0fd0fe0e03ca4bae343b6a5cc0662b2e8f0` |
| `pickle/instrument/qwen_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 47,564,039 | `c6722620cc6473e5e2a402aa266376b4b1161d261c73778de870bb119eed1819` |
| `pickle/instrument/qwen_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 14,534,962 | `f68d9fd8fc97c27dce203dfaf7154143a0a669235999817e1bc7bad83f28d98b` |
| `pickle/instrument/sarvam_country_instrument_repr.pkl` | Prompt-based control representations per country, all layers (`country_layer_repr`) | 36,996,295 | `99556694c0c2887db3b85ca10e211747862312ddb6b1541ce5249ae7792ddc18` |
| `pickle/instrument/sarvam_pure_instrument_cache.pkl` | Final-layer hidden state of each instrument name (`pure_instrument_cache`, dict: name -> vector) | 14,534,962 | `ea49a3071792545e55ff24f3c38205771110c9b99798f9988ba000804358a4ee` |

### Files not in the repository (all-layer caches)

Written by the cell "LAYER-WISE 0 — Ekstraksi Pure Embedding SEMUA Layer": a `float16` array of shape `(artifacts, layers incl. embedding, hidden size)`
and a JSON list with the artifact names in the same order. The size below is the value printed by the notebook when it ran the extraction
(`results/summary/01_semua_skalar_long.csv`, metrics `lw0.file` and `lw0.file_MB`). Notebooks that loaded an existing cache did not print a size, so those rows are absent.

| File name as printed | Size printed (MB) | Notebook |
|---|---|---|
| `gemma_pure_food_alllayers_fp16.npy` | 433 | gemma, culinary |
| `llama_pure_food_alllayers_fp16.npy` | 430 | llama, culinary |
| `sarvam_pure_food_alllayers_fp16.npy` | 400 | **mistral**, culinary (see [CHECK] below) |
| `sarvam_pure_food_alllayers_fp16.npy` | 287 | sarvam, culinary |
| `qwen_pure_food_alllayers_fp16.npy` | 366 | qwen, culinary |
| `croissantLLM_pure_instrument_alllayers_fp16.npy` | 181 | croissantLLM, instrument |
| `gemma_pure_instrument_alllayers_fp16.npy` | 316 | gemma, instrument |
| `kanana_pure_instrument_alllayers_fp16.npy` | 209 | kanana, instrument |
| `llama_pure_instrument_alllayers_fp16.npy` | 315 | llama, instrument |
| `mistral_pure_instrument_alllayers_fp16.npy` | 293 | mistral, instrument |
| `qwen_pure_instrument_alllayers_fp16.npy` | 268 | qwen, instrument |
| `sarvam_pure_instrument_alllayers_fp16.npy` | 210 | sarvam, instrument |

## Restoring the files

1. Download the archive from the link above `[TODO]` and extract it in the repository root.
2. The final tree must be:

```
pickle/
├── food/          14 files: <model>_country_layer_repr.pkl, <model>_pure_food_cache.pkl
└── instrument/    14 files: <model>_country_instrument_repr.pkl, <model>_pure_instrument_cache.pkl
```

3. Verify the checksums with one of the commands below and compare with the table above.
4. To reuse the caches inside the notebooks, copy the files to the `SAVE_DIR` set in each notebook
   (`/content/drive/MyDrive/Percobaan TA/Food KB/Data/` for culinary, `/content/drive/MyDrive/Percobaan TA/Instrument/Data/` for instrument).

### Computing SHA256

PowerShell (Windows):

```powershell
Get-ChildItem pickle -Recurse -Filter *.pkl | ForEach-Object { "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), ($_.FullName | Resolve-Path -Relative) }
```

bash (Linux/macOS/Git Bash):

```bash
find pickle -name '*.pkl' | sort | xargs sha256sum
```

## [CHECK] items

- **Equal file sizes.** Several files have exactly the same size but different SHA256, so they are not byte-identical:
  `llama_country_layer_repr.pkl` and `sarvam_country_layer_repr.pkl` (50,567,990 bytes), the same two for instruments (36,996,295 bytes),
  `llama_pure_food_cache.pkl` and `mistral_pure_food_cache.pkl` (29,761,785 bytes), `croissantLLM`, `qwen` and `sarvam` `pure_food_cache` (19,873,132 bytes),
  and the corresponding instrument caches (21,769,164 and 14,534,962 bytes). Why the sizes coincide has not been investigated.
- **Shared all-layer cache name in the Mistral culinary notebook.** In `notebooks/culinary/mistral_kuliner_with_SD_layerwise.ipynb`,
  `ALL_LAYERS_FILE` and `ALL_LAYERS_NAMES` point to `sarvam_pure_food_alllayers_*` instead of `mistral_pure_food_alllayers_*`.
  The stored output of that cell prints "Cache lama tidak cocok … Ekstraksi ulang" and then saves 400 MB to `sarvam_pure_food_alllayers_fp16.npy`;
  the sarvam culinary notebook prints a save of 287 MB to the same name. These files are not in the repository, so which model's array remains on Drive is not known.
- **Git history.** See the note under "Status of the files".
