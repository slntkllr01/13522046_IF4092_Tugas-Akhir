# Hasil ekstraksi: 7 model × 2 domain (kuliner, musik)

Semua angka di folder `hasil_csv/` dibaca langsung dari output sel notebook (stdout) oleh `extract_results.py`.
Tidak ada angka yang diketik manual.

## Cara menjalankan ulang
```
python extract_results.py Culinary.zip Music.zip -o hasil_csv --xlsx
python verify_numbers.py   Culinary.zip Music.zip hasil_csv   # cek 1: multiset angka
python check_consistency.py Culinary.zip Music.zip hasil_csv  # cek 2: posisi kolom/baris + cek silang
```
Input boleh berupa zip, folder berisi .ipynb, atau file .ipynb satuan.

## Verifikasi (hasil run terakhir)
1. **Audit baris**: setiap baris output yang mengandung angka tertangkap parser, atau diabaikan dengan alasan tertulis
   (progress bar pip, timing ekstraksi, path file, daftar file zip). Lihat `_audit_ignored_lines.csv`.
   `_audit_unparsed_lines.csv` = OK (0 baris lolos). Header tabel yang tidak dikenal membuat skrip berhenti.
2. **`verify_numbers.py`**: untuk tiap notebook, multiset semua angka di output sama persis dengan multiset angka di CSV
   (0 angka hilang, 0 angka "karangan"). Angka non-hasil (nomor seksi, ambang di teks penjelas, penghitung progress)
   dikeluarkan secara eksplisit lewat daftar regex di skrip.
3. **`check_consistency.py`**: 4815 cek, 0 gagal. Isinya:
   - Semua tabel pandas di-parse ulang dengan metode lain (split dari kanan) lalu dibandingkan sel per sel.
     Cek ini menangkap nilai yang tertukar kolom atau baris, yang tidak bisa ditangkap cek multiset.
   - Cek silang: nilai yang sama di beberapa tabel harus identik (Avg_Error, Centroid_Distance, Bias_Ratio, N_Artifacts);
     |vektor bias| harus sama dengan Centroid_Distance; ringkasan layer-wise sama dengan argmin tabel;
     jumlah Count regional sama dengan n; daftar region sama dengan kolom Mechanism.
   - Uji mutasi: menukar dua sel atau menggeser satu angka sebesar 0.01 terbukti terdeteksi.

## Isi folder
| File | Isi |
|---|---|
| `00_ringkasan_per_model.csv` | 1 baris per model×domain: metrik utama semua kondisi + ringkasan layer-wise |
| `01_semua_skalar_long.csv` | semua angka tunggal (format long) + `source_line` = baris asli output-nya |
| `regional_kontrol / regional_agregat / regional_eksklusif` | tabel akurasi per wilayah |
| `c1_* , c2_* , c3_* , c4_*` | Eksperimen C (centroid, mekanisme, bias ratio, arah bias, confusion, galat ternormalisasi, korelasi struktur) |
| `c3_salah_kira`, `c4_low_error_low_discrim` | baris naratif (dibulatkan 1–3 desimal; sudah dicek terhadap tabel presisi penuh) |
| `d_*` | Eksperimen D (bobot, perbandingan original vs balanced, effect size, ranking, top-10) |
| `null_jarak_region` | baseline prediktor nihil per wilayah |
| `layerwise_agregat`, `layerwise_individual` | kurva per layer (layer 0 = embedding) |
| `layerwise_individual_progress` | log progress per layer (Err 2 desimal + detik kumulatif); hanya notebook dengan log per layer |
| `daftar_region` | semua daftar region yang dicetak (kuadran, high/low error, Bias_Ratio>0.4, dll.) |
| `kontrol_sanity_top5` | 5 kandidat teratas per negara di sel sanity |
| `semua_hasil.xlsx` | semua tabel di atas dalam satu workbook |
| `_sumber_notebook.csv` | file sumber + MODEL_ID (diambil dari kode sel) |

## Catatan agar tidak salah baca
- `Agregat_err` (Cell Eksperimen A) = seed 42. `LW_agg_last_err_mean5seed` = rata-rata 5 seed pada layer terakhir.
  Keduanya memang berbeda.
- `LW_replik_*_layerwise` dan `LW_replik_*_asli` adalah angka layer terakhir dari sel layer-wise dan dari sel aslinya.
  Pada Mistral (Ministral-3-3B) keduanya TIDAK sama (lihat bawah).
- `Prob_as_printed` di sanity check adalah nilai yang dicetak dengan label "Prob". Nilainya >1, jadi itu logit/skor,
  bukan probabilitas.
- `setup.params_B_as_printed` adalah jumlah parameter yang dihitung setelah kuantisasi 4-bit (mis. Qwen 3B tercetak 1.70B).
- `b.n_titik` tercetak dua kali di notebook kuliner (nilainya sama); detektor konflik memastikan tidak ada metrik
  ganda dengan nilai berbeda.

## Temuan dari data (bukan masalah ekstraksi)
- **Mistral tidak lolos replikasi.** Layer terakhir di sel layer-wise berbeda dari fitur yang dipakai eksperimen utama.
  Selisih maks fitur vs cache: 44.8 (kuliner) dan 52.2 (musik); model lain ≤ 9.8.
  Agregat 15.19° vs 16.26° dan Individual 37.81° vs 41.92° (kuliner); 21.32° vs 22.59° dan 39.96° vs 41.31° (musik).
  Di kuliner, sel Layer-wise 0 mencetak "Cache lama tidak cocok … Ekstraksi ulang".
  Jadi kurva layer-wise Mistral tidak tersambung ke angka utama Mistral.
- **Alpha mentok di batas grid untuk SEMUA model, bukan hanya Qwen.** Alpha Individual di eksperimen utama = 500
  di 14/14 run. Di layer-wise, 86–100% fold-layer berada di batas 500.
