# 13522046_IF4092_Tugas-Akhir

[ISI: satu paragraf tujuan penelitian.] Repo ini memuat notebook, data, dan hasil untuk paper tentang linear probing per layer
pada 7 model bahasa di dua domain: kuliner (Culinary) dan musik (Instrument).

## Model dan domain

| Model | Model ID | Kuliner | Musik |
|---|---|---|---|
| Qwen2.5-3B | `Qwen/Qwen2.5-3B` | `notebooks/culinary/qwen_*` | `notebooks/instrument/qwen_*` |
| Llama-3.2-3B | `meta-llama/Llama-3.2-3B` | `notebooks/culinary/llama_*` | `notebooks/instrument/llama_*` |
| gemma-3-4b-pt | `google/gemma-3-4b-pt` | `notebooks/culinary/gemma_*` | `notebooks/instrument/gemma_*` |
| sarvam-1 | `sarvamai/sarvam-1` | `notebooks/culinary/sarvam_*` | `notebooks/instrument/sarvam_*` |
| Ministral-3-3B-Base-2512 | `mistralai/Ministral-3-3B-Base-2512` | `notebooks/culinary/mistral_*` | `notebooks/instrument/mistral_*` |
| kanana-nano-2.1b-base | `kakaocorp/kanana-nano-2.1b-base` | `notebooks/culinary/kanana_*` | `notebooks/instrument/kanana_*` |
| CroissantLLMBase | `croissantllm/CroissantLLMBase` | `notebooks/culinary/croissantLLM_*` | `notebooks/instrument/croissantLLM_*` |

## Struktur folder

```
README.md
dataset/                      data masukan (cleaned_food_kb, country_instrument, country_region, countries_coordinates)
notebooks/culinary/           7 notebook Colab, domain kuliner
notebooks/instrument/         7 notebook Colab, domain musik
scripts/                      extract_results.py, verify_numbers.py, check_consistency.py (lihat scripts/README_scripts.md)
results/layerwise/<domain>/   CSV dan PNG asli dari Colab; sumber utama kurva di paper
results/summary/              hasil ekstraksi dari stdout notebook (00_ringkasan_per_model.csv, 01_semua_skalar_long.csv,
                              semua_hasil.xlsx, tables/, README_summary.md)
results/figures/<domain>/<model>/   PNG peta dan probing per model
data_external/                tempat tautan data besar (pickle); lihat data_external/README.md
pickle/                       cache fitur (besar; masuk .gitignore)
```

## Menjalankan ulang skrip

Jalankan dari root repo:

```
python scripts/extract_results.py notebooks/culinary notebooks/instrument -o _tmp_tables
python scripts/verify_numbers.py   notebooks/culinary notebooks/instrument _tmp_tables
python scripts/check_consistency.py notebooks/culinary notebooks/instrument _tmp_tables
```

Hasil yang diharapkan: `verify_numbers.py` mencetak "OK: setiap angka di CSV benar-benar ada di output notebook",
dan `check_consistency.py` mencetak "4815 cek dijalankan, 0 gagal".
CSV di `_tmp_tables/` identik dengan `results/summary/` (`tables/` serta dua CSV di root).

## Catatan sumber data

- `results/layerwise/` adalah sumber utama kurva di paper (CSV dan PNG asli dari Colab).
- `results/summary/` adalah hasil ekstraksi dari stdout notebook. Angkanya dibulatkan sesuai cetakan notebook dan dipakai untuk cross-check.

## Data besar

Cache fitur (`pickle/`, sekitar 930 MB) tidak ikut GitHub. Lokasi: [ISI: tautan Zenodo/HuggingFace]. Checksum ada di `data_external/README.md`.

## Batasan yang diketahui

1. Alpha RidgeCV mentok di batas grid 500 pada semua model.
2. Ministral-3-3B: layer terakhir di sel layer-wise tidak sama dengan fitur yang dipakai eksperimen utama,
   jadi kurva layer-wise Ministral tidak tersambung ke angka utamanya. Rinciannya ada di `results/summary/README_summary.md`.
