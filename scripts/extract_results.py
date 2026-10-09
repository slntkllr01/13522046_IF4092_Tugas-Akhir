#!/usr/bin/env python3
"""
extract_results.py: ambil SEMUA angka dari output notebook Colab (layer-wise probing)
dan simpan sebagai CSV yang rapi. Angka dibaca langsung dari output sel (stdout),
tidak ada yang diketik ulang.

Pemakaian:
    python extract_results.py Culinary.zip Music.zip -o hasil_csv
    python extract_results.py folder_berisi_ipynb/ -o hasil_csv
    python extract_results.py a.ipynb b.ipynb -o hasil_csv

Prinsip "tidak boleh ada angka yang hilang":
  * Tabel pandas dibaca dengan posisi kolom (fixed-width), lalu divalidasi:
    token hasil split harus identik dengan token baris aslinya.
  * Setiap baris output yang mengandung angka HARUS tertangkap oleh salah satu
    parser (tabel / skalar / daftar / verdict) ATAU masuk daftar abaikan dengan
    alasan eksplisit (progress bar, timing, path, pip). Baris lain yang lolos
    dicatat di _audit_unparsed_lines.csv dan skrip keluar dengan status error.
  * Header tabel yang tidak dikenal juga membuat skrip gagal (tidak diam-diam).
"""
import argparse, ast, collections, csv, glob, io, json, os, re, sys, zipfile

# ----------------------------------------------------------------------------
# 1. Membaca notebook
# ----------------------------------------------------------------------------
SECTION_MAP = [  # (substring judul sel, kunci seksi); urutan penting (pertama yang cocok)
    ("SETUP", "setup"),
    ("KONTROL — Ekstraksi", "kontrol_ekstraksi"),
    ("KONTROL — Pemeriksaan Sanity", "kontrol_sanity"),
    ("KONTROL — Probing Linear", "kontrol_probe"),
    ("KONTROL — Analisis Akurasi Regional", "kontrol_regional"),
    ("KONTROL — Visualisasi", "kontrol_viz"),
    ("EKSPERIMEN A — Ekstraksi", "a_ekstraksi"),
    ("EKSPERIMEN A — Probing Linear", "a_probe"),
    ("EKSPERIMEN A — Analisis Akurasi Regional", "a_regional"),
    ("EKSPERIMEN A — Visualisasi", "a_viz"),
    ("BASELINE EKSKLUSIF — Probing", "eksklusif_probe"),
    ("BASELINE EKSKLUSIF — Analisis", "eksklusif_regional"),
    ("EKSPERIMEN B — Probing Linear", "b_probe"),
    ("EKSPERIMEN B — Konstruksi", "b_df"),
    ("EKSPERIMEN B — Visualisasi", "b_viz"),
    ("EKSPERIMEN B — Fungsi", "b_viz_negara"),
    ("HELPER: Koordinat", "helper"),
    ("EKSPERIMEN C — Utilitas", "helper"),
    ("EKSPERIMEN C.1", "c1"),
    ("EKSPERIMEN C.2", "c2"),
    ("EKSPERIMEN C.3", "c3"),
    ("EKSPERIMEN C.4", "c4"),
    ("EKSPERIMEN D — Probing", "d"),
    ("EKSPERIMEN D — Visualisasi", "d_viz"),
    ("EKSPERIMEN D — Ringkasan Effect", "d"),
    ("EKSPERIMEN D — Ranking", "d"),
    ("BASELINE — Prediktor Nihil", "null"),
    ("BASELINE — Static Embedding", "static"),
    ("print(f\"{'Kondisi'", "ringkasan_kondisi"),
    ("LAYER-WISE 0", "lw0"),
    ("LAYER-WISE 1", "lw1"),
    ("import os", "zip"),
]


def cell_title(src):
    for l in src.splitlines():
        if l.strip() and not l.startswith("# ==="):
            return l.strip()
    return ""


def section_of(title):
    for sub, key in SECTION_MAP:
        if sub in title:
            return key
    raise KeyError(f"Judul sel tidak dikenal: {title!r}")


def iter_notebooks(inputs):
    """Yield (nama_file, dict_notebook) dari zip / folder / .ipynb."""
    for inp in inputs:
        if os.path.isdir(inp):
            for p in sorted(glob.glob(os.path.join(inp, "**", "*.ipynb"), recursive=True)):
                yield os.path.basename(p), json.load(open(p, encoding="utf-8"))
        elif inp.lower().endswith(".zip"):
            with zipfile.ZipFile(inp) as z:
                for n in sorted(z.namelist()):
                    if n.endswith(".ipynb") and not os.path.basename(n).startswith("."):
                        yield os.path.basename(n), json.loads(z.read(n).decode("utf-8"))
        elif inp.endswith(".ipynb"):
            yield os.path.basename(inp), json.load(open(inp, encoding="utf-8"))
        else:
            raise SystemExit(f"Input tidak dikenal: {inp}")


def load_cells(nb):
    cells = []
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c.get("source", ""))
        title = cell_title(src)
        out = "".join("".join(o["text"]) for o in c.get("outputs", [])
                      if o.get("output_type") == "stream" and o.get("name") == "stdout")
        n_err = sum(1 for o in c.get("outputs", []) if o.get("output_type") == "error")
        cells.append(dict(idx=i, title=title, section=section_of(title), stdout=out, src=src,
                          n_errors=n_err, exec_count=c.get("execution_count")))
    return cells


# ----------------------------------------------------------------------------
# 2. Tabel pandas (fixed-width, rata kanan)
# ----------------------------------------------------------------------------
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")
HEADER_RE = re.compile(r"^\s*[A-Za-z_][\w%]*(\s+[A-Za-z_0-9][\w%()°]*)+\s*$")


def split_fixed(header, line):
    ends = [m.end() for m in re.finditer(r"\S+", header)]
    if len(ends) < 2 or len(line.rstrip()) > ends[-1]:
        return None
    cells, prev = [], 0
    for e in ends:
        cells.append(line[prev:e].strip())
        prev = e
    if " ".join(c for c in cells if c).split() != line.split():
        return None
    for e in ends[:-1]:
        if e < len(line) and line[e - 1] != " " and line[e] != " ":
            return None
    if any(c == "" for c in cells):
        return None
    return cells


def find_tables(lines):
    out, i = [], 0
    while i < len(lines):
        h = lines[i]
        if HEADER_RE.match(h) and not NUM_RE.fullmatch(h.split()[0]):
            rows, j = [], i + 1
            while j < len(lines):
                cells = split_fixed(h, lines[j])
                if cells is None:
                    break
                rows.append(cells)
                j += 1
            if rows and all(any(NUM_RE.fullmatch(c) for c in r) for r in rows):
                out.append((i, j, h.split(), rows))
                i = j
                continue
        i += 1
    return out


# (seksi, kolom) -> nama tabel keluaran. Header yang tidak ada di sini = error.
REG6 = ("Region", "Count", "Avg_Error_Deg", "Std_Error_Deg", "MAE_Lat", "MAE_Lon")
TABLE_MAP = {
    ("kontrol_regional", REG6): "regional_kontrol",
    ("a_regional", REG6): "regional_agregat",
    ("eksklusif_regional", ("Region", "Count", "Avg_Error_Deg", "MAE_Lat", "MAE_Lon")): "regional_eksklusif",
    ("c1", ("Region", "N_Artifacts", "Pred_Centroid_Lat", "Pred_Centroid_Lon", "Actual_Centroid_Lat",
            "Actual_Centroid_Lon", "Pred_Spread", "Avg_Error", "Std_Error")): "c1_centroid",
    ("c1", ("Region", "Centroid_Distance", "Pred_Spread", "Avg_Error")): "c1_centroid_distance",
    ("c1", ("Region", "N_Artifacts", "Avg_Error", "Pred_Spread", "Mechanism")): "c1_mekanisme",
    ("c2", ("Region", "N_Artifacts", "Avg_Error", "Centroid_Distance", "Pred_Spread", "Bias_Ratio")): "c2_bias_ratio",
    ("c2", ("Region", "Avg_Error", "Rank_AvgError", "Bias_Ratio", "Rank_BiasRatio", "Rank_Diff")): "c2_ranking",
    ("c2", ("Region", "Avg_Error", "Bias_Ratio", "Mechanism_2x2")): "c2_klasifikasi_2x2",
    ("c3", ("Region", "Bias_Vec_North", "Bias_Vec_East", "Bias_Angle_Deg", "Centroid_Distance", "Bias_Ratio")): "c3_bias_vector",
    ("c3", ("Region", "Centroid_Distance_to_Self", "Closest_Confusion_Target", "Distance_to_Target",
            "Improvement_vs_Self")): "c3_confusion_target",
    ("c4", ("Region", "N_Countries", "Avg_Error", "Actual_Spread", "Normalized_Error")): "c4_normalized_error",
    ("c4", ("Region", "Avg_Error", "Rank_AvgError", "Normalized_Error", "Rank_NormError", "Rank_Shift")): "c4_rank_shift",
    ("c4", ("Region", "N_Countries", "N_Pairs", "Structure_Correlation", "Structure_P_Mantel",
            "Max_Permutations")): "c4_structure_correlation",
    ("c4", ("Region", "N_Countries", "Avg_Error", "Normalized_Error", "Bias_Ratio",
            "Structure_Correlation")): "c4_gabungan",
    ("d", ("Region", "CentDist_Original", "CentDist_Balanced", "CentDist_Change", "BiasRatio_Original",
           "Bias_Ratio_Bal", "BiasRatio_Change")): "d_perbandingan",
    ("d", ("Region", "CentDist_Original")): "d_top10_original",
    ("d", ("Region", "CentDist_Balanced")): "d_top10_balanced",
    ("null", ("Region", "Dist_NullMean_to_ActualCentroid")): "null_jarak_region",
    ("lw1", ("Layer", "Depth", "Err_s42", "Err_mean", "Err_sd", "SD_titik", "R2_lat", "R2_lon",
             "Alpha")): "layerwise_agregat",
    ("lw1", ("Layer", "Depth", "Err", "SD_titik", "R2_lat", "R2_lon", "Alpha_med",
             "Alpha_di_batas")): "layerwise_individual",
}


def to_num(s):
    try:
        v = float(s)
        return int(v) if re.fullmatch(r"[-+]?\d+", s) else v
    except ValueError:
        return s


# ----------------------------------------------------------------------------
# 3. Skalar: (seksi, regex, [nama metrik untuk tiap grup])
#    Nama metrik bernilai None = grup itu diabaikan (mis. nomor sel).
# ----------------------------------------------------------------------------
F = r"([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)"
SCALARS = [
    # setup
    ("setup", rf"^Loaded (?:Food|Instrument) KB: {F} rows\.$", ["setup.kb_rows"]),
    ("setup", rf"^Region mapping loaded: {F} countries\.$", ["setup.region_mapping_countries"]),
    ("setup", rf"^Filtered {F} countries for experiment(?: \(Excluded 'Global'\))?\.$", ["setup.countries_filtered"]),
    ("setup", rf"^- Total Negara: {F}$", ["setup.total_negara"]),
    ("setup", rf"^- Total (?:Makanan|Instrumen Unik): {F}$", ["setup.total_artefak"]),
    ("setup", rf"^⏳ Tokenizing {F} (?:food|instrument) names.*$", ["setup.n_names_tokenized"]),
    ("setup", rf"^Model loaded — {F}B params, {F} layers$", ["setup.params_B_as_printed", "setup.n_layers"]),
    ("setup", rf"^VRAM \[post-load\]: {F} GB allocated, {F} GB reserved$", ["setup.vram_alloc_GB", "setup.vram_reserved_GB"]),
    # kontrol
    ("kontrol_ekstraksi", rf"^Berhasil memuat {F} negara\. \(Inference di-skip\)$", ["kontrol.n_negara_cache"]),
    ("kontrol_probe", rf"^Loaded coordinates for {F} countries from CSV\.$", ["kontrol.n_coord_countries"]),
    ("kontrol_probe", rf"^Latitude\s+\| MAE: {F}°$", ["kontrol.mae_lat"]),
    ("kontrol_probe", rf"^Longitude \| MAE: {F}°$", ["kontrol.mae_lon"]),
    ("kontrol_probe", rf"^AVERAGE GLOBAL ERROR: {F} derajat \(SD: {F}°, n={F}\)$", ["kontrol.err", "kontrol.err_sd", "kontrol.n"]),
    ("kontrol_probe", rf"^Latitude R² \(Kontrol\): {F}$", ["kontrol.r2_lat"]),
    ("kontrol_probe", rf"^Longitude R² \(Kontrol\): {F}$", ["kontrol.r2_lon"]),
    # A (agregat)
    ("a_ekstraksi", rf"^Berhasil memuat {F} (?:data ringan \(Layer Terakhir\)|instrumen)\.$", ["a.n_artefak_cache"]),
    ("a_ekstraksi", rf"^Berhasil (?:mencocokkan|memetakan) {F} (?:makanan|instrumen) untuk visualisasi\.$", ["a.n_artefak_tsne"]),
    ("a_probe", rf"^⏳ Menghitung rata-rata embedding per negara \(Threshold: {F}\)\.\.\.$", ["a.min_artefak_threshold"]),
    ("a_probe", rf"^Data siap: {F} negara dianalisis\.$", ["a.n_negara"]),
    ("a_probe", rf"^Average Global Error: {F} derajat \(SD: {F}°, n={F}\)$", ["a.err", "a.err_sd", "a.n"]),
    ("a_probe", rf"^Latitude R²: {F}$", ["a.r2_lat"]),
    ("a_probe", rf"^Longitude R²: {F}$", ["a.r2_lon"]),
    # eksklusif
    ("eksklusif_probe", rf"^Negara yang memenuhi syarat \(min {F} (?:makanan|instrumen) unik\): {F}$", ["eksklusif.min_unik", "eksklusif.n_negara"]),
    ("eksklusif_probe", rf"^Average Global Error \(Unique\): {F} derajat$", ["eksklusif.err"]),
    ("eksklusif_probe", rf"^Latitude R² Score: {F}$", ["eksklusif.r2_lat"]),
    ("eksklusif_probe", rf"^Longitude R² Score: {F}$", ["eksklusif.r2_lon"]),
    ("eksklusif_probe", rf"^Error Inclusive \(Exp {F}\): {F}°$", [None, "eksklusif.err_inclusive_ref"]),
    ("eksklusif_probe", rf"^Error Exclusive \(Exp {F}\): {F}°$", [None, "eksklusif.err_exclusive_ref"]),
    ("eksklusif_probe", rf"^Hasil: Error naik sebesar {F}° saat menggunakan hanya (?:makanan|instrumen) unik\.$", ["eksklusif.err_naik"]),
    ("eksklusif_probe", rf"^Hasil: Error turun sebesar {F}° saat menggunakan hanya (?:makanan|instrumen) unik\.$", ["eksklusif.err_turun"]),
    ("eksklusif_probe", rf"^Baseline Dataframe created for {F} exclusive countries\.$", ["eksklusif.n_negara_df"]),
    ("eksklusif_probe", rf"^BASELINE EKSKLUSIF — PROBING LINEAR \(HANYA (?:MAKANAN|INSTRUMEN) {F}-NEGARA\)$", [None]),
    ("eksklusif_probe", rf"^Logika: Hanya menggunakan (?:makanan|instrumen) yang memiliki {F} negara eksklusif$", [None]),
    # B (individual)
    ("b_probe", rf"^Data siap: {F} titik data (?:makanan|instrumen)-negara\.$", ["b.n_titik"]),
    ("b_probe", rf"^- Artefak unik: {F}$", ["b.n_artefak_unik"]),
    ("b_probe", rf"^- Instrumen unik\s*: {F}$", ["b.n_artefak_unik"]),
    ("b_probe", rf"^- Artefak multi-negara \(diklaim >{F} negara\): {F} \({F}%\)$", [None, "b.n_multi_negara", "b.pct_multi_negara"]),
    ("b_probe", rf"^- Multi-negara\s*: {F} \({F}%\)$", ["b.n_multi_negara", "b.pct_multi_negara"]),
    ("b_probe", rf"^- Outlier terbesar: (.+?) \({F} negara\)$", ["b.outlier_terbesar_nama", "b.outlier_terbesar_n_negara"]),
    ("b_probe", rf"^df_inst_points created: {F} baris\.$", ["b.n_df_points"]),
    ("b_probe", rf"^⏳ Probing {F} titik dengan GroupKFold\(n={F}\)\.\.\.$", ["b.n_titik_probe", "b.n_folds"]),
    ("b_probe", rf"^Latitude R² \(Eksperimen B\): {F}$", ["b.r2_lat"]),
    ("b_probe", rf"^Longitude R² \(Eksperimen B\): {F}$", ["b.r2_lon"]),
    ("b_probe", rf"^Alpha dipilih RidgeCV: {F}$", ["b.alpha"]),
    ("b_probe", rf"^Average Global Error: {F} derajat \(SD: {F}°, n={F}\)$", ["b.err", "b.err_sd", "b.n"]),
    ("b_df", rf"^Dataframe df_inst_points berhasil dibuat dengan {F} baris\.$", ["b.n_df_points_konstruksi"]),
    # C.1
    ("c1", rf"^Data individual prediction: {F} baris artefak\.$", ["c1.n_baris"]),
    ("c1", rf"^High-error regions: {F}°$", ["c1.mean_dist_antar_centroid_high_error"]),
    ("c1", rf"^Low-error regions : {F}°$", ["c1.mean_dist_antar_centroid_low_error"]),
    ("c1", rf"^EKSPERIMEN C\.{F} — .*$", [None]),
    ("c1", rf"^EXPERIMENT {F} SELESAI\.$", [None]),
    # C.2
    ("c2", rf"^Korelasi Spearman Avg_Error vs Bias_Ratio: r={F} \(p={F}\)$", ["c2.spearman_r_err_vs_biasratio", "c2.spearman_p"]),
    ("c2", rf"^Avg_Error median = {F}°$", ["c2.median_avg_error"]),
    ("c2", rf"^Bias_Ratio median = {F}$", ["c2.median_bias_ratio"]),
    ("c2", rf"^EKSPERIMEN C\.{F} — .*$", [None]),
    ("c2", rf"^EXPERIMENT {F} SELESAI\.$", [None]),
    ("c2", rf"^KLASIFIKASI {F}x{F} \(Avg_Error x Bias_Ratio\):$", [None, None]),
    ("c2", rf"^Bias_Ratio = bias²/MSE .*range \[{F},{F}\] eksak\.$", [None, None]),
    ("c2", rf"^Ratio -> {F}\+?\s+: .*$", [None]),
    ("c2", rf"^\(Rank_Diff = {F} -> .*$", [None]),
    # C.3
    ("c3", rf"^Direction Consistency \(R\) untuk region Systematic Bias: {F}$", ["c3.direction_consistency_R"]),
    ("c3", rf"^Mean bias direction: {F}°$", ["c3.mean_bias_direction_deg"]),
    ("c3", rf"^EKSPERIMEN C\.{F} — .*$", [None]),
    ("c3", rf"^EXPERIMENT {F} SELESAI\.$", [None]),
    ("c3", rf"^\(R mendekati {F} -> .*$", [None]),
    ("c3", rf"^\(Improvement_vs_Self > {F} -> .*$", [None]),
    # C.4
    ("c4", rf"^Korelasi Avg_Error vs Normalized_Error: r={F} \(p={F}\)$", ["c4.corr_err_vs_normerr_r", "c4.corr_err_vs_normerr_p"]),
    ("c4", rf"^Avg_Error median = {F}°$", ["c4.median_avg_error"]),
    ("c4", rf"^Structure_Correlation median = {F}$", ["c4.median_structure_corr"]),
    ("c4", rf"^REGION 'LOW ERROR TAPI LOW DISCRIMINABILITY' \(n={F}\):$", ["c4.n_low_error_low_discrim"]),
    ("c4", rf"^EKSPERIMEN C\.{F} — .*$", [None]),
    ("c4", rf"^EXPERIMENT {F} SELESAI\.$", [None]),
    ("c4", rf"^Tinggi \(-> {F}\) : .*$", [None]),
    ("c4", rf"^- Normalized_Error tinggi \(>{F}\): .*$", [None]),
    ("c4", rf"^bukan karena model benar-benar mengenali negara{F} di dalamnya\.$", [None]),
    # D
    ("d", rf"^Alpha dipilih: {F}$", ["d.alpha_balanced"]),
    ("d", rf"^Original : \({F}°, {F}°\)\s+Centroid_Dist={F}°$", ["d.oceania_pred_lat_original", "d.oceania_pred_lon_original", "d.oceania_centdist_original"]),
    ("d", rf"^Balanced : \({F}°, {F}°\)\s+Centroid_Dist={F}°$", ["d.oceania_pred_lat_balanced", "d.oceania_pred_lon_balanced", "d.oceania_centdist_balanced"]),
    ("d", rf"^→ {F} region KELUAR dari kategori sistematis setelah balancing$", ["d.n_region_keluar_sistematis"]),
    ("d", rf"^{F} region terbaik di kondisi (?:ORIGINAL|BALANCED):$", [None]),
    ("d", rf"^CentDist_Change [<>] {F} = .*$", [None]),
    # baselines
    ("null", rf"^Prediktor Nihil — Average Global Error: {F} derajat \(SD: {F}°, n={F}\)$", ["null.err", "null.err_sd", "null.n"]),
    ("null", rf"^Lokasi rata-rata data latih: \({F}, {F}\)$", ["null.mean_lat", "null.mean_lon"]),
    ("static", rf"^Static Embedding \(char n-gram\) — Average Global Error: {F} derajat \(SD: {F}°, n={F}\)$", ["static.err", "static.err_sd", "static.n"]),
    ("ringkasan_kondisi", rf"^Prediktor Nihil\s+{F}$", ["ringkasan.null_err"]),
    ("ringkasan_kondisi", rf"^Static Embedding \(char n-gram\)\s+{F}$", ["ringkasan.static_err"]),
    ("ringkasan_kondisi", rf"^Probe LLM \(Eksperimen B\)\s+{F}$", ["ringkasan.probe_b_err"]),
    # layer-wise 0
    ("lw0", rf"^Final norm: (\S+)\s+\(dtype (\S+)\) \| {F} artefak x {F} layer x {F} dim$",
     ["lw0.final_norm_path", "lw0.norm_dtype", "lw0.n_artefak", "lw0.n_layer_plus_emb", "lw0.dim"]),
    ("lw0", rf"^Cek asumsi OK: hidden_states\[-1\] == keluaran final norm \(selisih maks {F}\)\.$", ["lw0.cek_final_norm_maxdiff"]),
    ("lw0", rf"^Cache semua-layer ditemukan: \({F}, {F}, {F}\) \(fp16\)\. Ekstraksi di-skip\.$", ["lw0.n_artefak", "lw0.n_layer_plus_emb", "lw0.dim"]),
    ("lw0", rf"^Selesai {F}s\. Disimpan: (\S.*) \({F} MB\)$", ["lw0.ekstraksi_detik", "lw0.file", "lw0.file_MB"]),
    ("lw0", rf"^Selisih maks layer terakhir vs pure_\w+_cache: {F}\s+\((OK|PERIKSA!)\)$", ["lw0.maxdiff_last_vs_cache", "lw0.maxdiff_status"]),
    ("lw0", rf"^F_all: \({F}, {F}, {F}\) -> \(artefak, layer {F}\.\.{F}, dim\)$", ["lw0.F_all_n_artefak", "lw0.F_all_n_layer", "lw0.F_all_dim", None, None]),
    ("lw0", rf"^LAYER-WISE {F} — .*$", [None]),
    # layer-wise 1
    ("lw1", rf"^Cek fitur layer terakhir vs Cell {F}: selisih maks {F}$", ["@cekfitur", None]),  # ditangani khusus
    ("lw1", rf"^Agregat selesai: {F} layer x {F} seed, {F}s$", ["lw1.agg_n_layer", "lw1.agg_n_seed", "lw1.agg_detik"]),
    ("lw1", rf"^Individual selesai: {F} layer(?: \({F} baru dihitung\))?, {F}s$", ["lw1.ind_n_layer", "lw1.ind_n_baru", "lw1.ind_detik"]),
    ("lw1", rf"^Agregat\s+: {F}°\s+vs Cell {F} = {F}°$", ["lw1.replikasi_agg_layerwise", None, "lw1.replikasi_agg_cell_asli"]),
    ("lw1", rf"^Individual : {F}°\s+vs Cell {F} = {F}°$", ["lw1.replikasi_ind_layerwise", None, "lw1.replikasi_ind_cell_asli"]),
    ("lw1", rf"^Agregat\s+: layer {F} = {F}° \| terbaik = layer {F} \({F}% kedalaman\) {F}° \| terakhir = {F}°$",
     [None, "lw1.agg_err_layer0", "lw1.agg_best_layer", "lw1.agg_best_depth_pct", "lw1.agg_best_err", "lw1.agg_last_err"]),
    ("lw1", rf"^Individual: layer {F} = {F}° \| terbaik = layer {F} \({F}% kedalaman\) {F}° \| terakhir = {F}°$",
     [None, "lw1.ind_err_layer0", "lw1.ind_best_layer", "lw1.ind_best_depth_pct", "lw1.ind_best_err", "lw1.ind_last_err"]),
    ("lw1", rf"^Noise CV Agregat pada layer terbaik: SD antar-seed = {F}° \(selisih < ~{F} SD .*$", ["lw1.agg_seed_sd_at_best", None]),
    ("lw1", rf"^PERINGATAN: alpha Individual menyentuh batas atas grid \({F}\) pada {F}% fold-layer;.*$", ["lw1.alpha_grid_max", "lw1.pct_fold_layer_alpha_di_batas"]),
    ("lw1", rf"^AGREGAT \(Err_s{F} = seed laporan;.*$", [None]),
    ("lw1", rf"^LAYER-WISE {F} — .*$", [None]),
]
SCALARS = [(s, re.compile(r), names) for s, r, names in SCALARS]

# Verdict (teks kesimpulan yang dicetak notebook)
VERDICTS = [
    ("c1", r"^High-error regions' centroids (TIDAK lebih berdekatan|LEBIH berdekatan.*)$", "c1.verdict_fallback_zone"),
    ("c2", r"^-> (Region dengan error tinggi .*)$", "c2.verdict_spearman"),
    ("c3", r"^(Indikasi kuat ada GRAVITATIONAL CENTER global\.|Tidak ada gravitational center tunggal yang jelas;)$", "c3.verdict_gravitational_center"),
    ("c4", r"^-> (Ranking .*)$", "c4.verdict_rank_normalisasi"),
    ("d", r"^→ (Centroid .*)$", "d.verdict_oceania_centroid"),
    ("d", r"^→ (\d+ region KELUAR .*|Pola berubah .*|POLA SISTEMATIS BERTAHAN .*)$", "d.verdict_pola_sistematis"),
]
VERDICTS = [(s, re.compile(r), n) for s, r, n in VERDICTS]

# Baris berangka yang sengaja DIABAIKAN (alasan dicatat)
IGNORE = [
    (None, r"\x1b\[|━|\[\?25h|\[\?25l", "progress bar / ANSI pip"),
    (None, r"requires .* but you have .* which is incompatible", "konflik versi pip"),
    ("setup", r"^GPU: |^VRAM: \d", "info hardware"),
    ("setup", r"^\[.*\.pkl", "daftar file Drive"),
    ("setup", r"^- Contoh: ", "contoh tokenisasi"),
    ("setup", r"^⏳ Loading .* in 4-bit NF4", "nama model (diambil dari MODEL_ID)"),
    ("setup", r"Building wheel|Getting requirements|Installing build|Preparing metadata", "pip"),
    ("lw0", r"^\[\d+/\d+\] \d+s$", "progress ekstraksi (timing)"),
    ("lw1", r"^Tersimpan di ", "path file"),
    ("zip", r".", "daftar file zip"),
    ("kontrol_viz", r"^Saved map to: ", "path gambar"),
    ("b_viz", r"^Berhasil menyimpan: ", "path gambar"),
    ("b_viz", r"^Full-map untuk region ", "status gambar"),
    ("a_viz", r".", "status gambar"),
]
IGNORE = [(s, re.compile(r), why) for s, r, why in IGNORE]

COUNTRY_RE = re.compile(r"^([A-Z][A-Z .'\-()]+):$")
SANITY_RE = re.compile(rf"^- (.+?)\s+\| Prob: {F}$")
DW_RE = re.compile(rf"^(.+?)\s+N=\s*{F}\s+total_w={F}$")
EFF_HDR = re.compile(r"^Region\s+Orig\s+Bal\s+%Change\s+Status$")
EFF_RE = re.compile(rf"^(.+?)\s+{F}\s+{F}\s+{F}%\s+(\w+)$")
RANK_HDR = re.compile(r"^Region\s+Orig\(°\)\s+Rank_Orig\s+Bal\(°\)\s+Rank_Bal\s+ΔRank$")
RANK_RE = re.compile(rf"^(.+?)\s+{F}\s+(\d+)\s+{F}\s+(\d+)\s+(=|↑\d+|↓\d+)$")
LIST_HDR = re.compile(r"^(.+?) \((\d+) region\):$")
LIST_ITEM = re.compile(r"^- ([^:]+)$")
BRACKET_RE = re.compile(r"^(High-error regions|Low-error regions|⏳ Region dengan Systematic Bias|Region Bias_Ratio > ([\d.]+) \((original|balanced)\))\s*(?:\(n=(\d+)\))?\s*:\s*(\[.*\])$")
SALAH_KIRA_RE = re.compile(r"^'(.+)' artefaknya cenderung di-decode model sebagai berasal dari '(.+)'$")
JARAK_RE = re.compile(rf"^\(jarak ke (.+): {F}° vs jarak ke lokasi asli sendiri: {F}°\)$")
LOWDISC_RE = re.compile(rf"^- (.+): Avg_Error={F}°, Structure_Correlation={F}$")
PROG_NEW = re.compile(rf"^Individual layer\s+{F} \({F}/{F}\) \| err\s+{F}° \|\s+{F}s berjalan, sisa ~{F}s$")
PROG_OLD = re.compile(rf"^Individual layer\s+{F} \| err\s+{F}° \|\s+{F}s \(sisa ~{F}s\)$")
MELANJUT_RE = re.compile(r"^Melanjutkan Individual: layer selesai = \[(.*)\]$")


# ----------------------------------------------------------------------------
# 4. Ekstraksi satu notebook
# ----------------------------------------------------------------------------
def parse_notebook(fname, nb):
    m = re.match(r"(.+?)_(kuliner|musik)_", fname)
    if not m:
        raise SystemExit(f"Nama file tidak sesuai pola <model>_<kuliner|musik>_...: {fname}")
    model_key, domain = m.group(1), m.group(2)
    cells = load_cells(nb)
    model_id = None
    for c in cells:
        mm = re.search(r"^MODEL_ID\s*=\s*[\"']([^\"']+)[\"']", c["src"], re.M)
        if mm:
            model_id = mm.group(1)
            break
    base = dict(model=model_key, model_id=model_id, domain=domain)

    tables = collections.defaultdict(list)   # nama -> list of dict
    scalars, audit, ignored = [], [], []
    seen_tables = collections.Counter()

    def add_scalar(sec, metric, value, line, cell):
        scalars.append(dict(base, section=sec, metric=metric, value=to_num(value) if isinstance(value, str) else value,
                            cell_idx=cell["idx"], source_line=line.strip()))

    for cell in cells:
        sec = cell["section"]
        if cell["n_errors"]:
            audit.append(dict(base, cell_idx=cell["idx"], section=sec, line="<SEL BERISI ERROR/TRACEBACK>"))
        lines = cell["stdout"].split("\n")
        used = set()
        # --- tabel pandas
        for (a, b, cols, rows) in find_tables(lines):
            key = (sec, tuple(cols))
            if key not in TABLE_MAP:
                raise SystemExit(f"[{fname}] tabel tidak dikenal di sel {cell['idx']} ({sec}): {cols}")
            name = TABLE_MAP[key]
            seen_tables[name] += 1
            for r_i, r in enumerate(rows):
                d = dict(base, row_order=r_i + 1)
                for col, val in zip(cols, r):
                    d[col] = to_num(val)
                tables[name].append(d)
            used |= set(range(a, b))
        # --- parser per baris
        cur_country, sanity_rank = None, 0
        mode, list_name, list_expected, list_items = None, None, None, []
        pending_salah = None
        cekfitur_n = 0

        def close_list():
            nonlocal list_name, list_items, list_expected
            if list_name is not None:
                if len(list_items) != list_expected:
                    raise SystemExit(f"[{fname}] daftar '{list_name}' jumlah {len(list_items)} != {list_expected}")
                for k, it in enumerate(list_items, 1):
                    tables["daftar_region"].append(dict(base, section=sec, daftar=list_name, urutan=k, Region=it))
                add_scalar(sec, f"{sec}.n_region[{list_name}]", str(list_expected), f"{list_name} ({list_expected} region):", cell)
            list_name, list_items, list_expected = None, [], None

        for k, raw in enumerate(lines):
            if k in used:
                continue
            s = raw.strip()
            if not s:
                continue
            # daftar "Nama (n region):" lalu "- Region"
            if list_name is not None:
                mi = LIST_ITEM.match(s)
                if mi and len(list_items) < list_expected:
                    list_items.append(mi.group(1).strip()); used.add(k); continue
                close_list()
            mh = LIST_HDR.match(s)
            if mh and sec in ("c1", "c2"):
                list_name, list_expected, list_items = mh.group(1), int(mh.group(2)), []
                used.add(k)
                if list_expected == 0:
                    close_list()
                continue
            # sanity kontrol
            if sec == "kontrol_sanity":
                mc = COUNTRY_RE.match(s)
                if mc:
                    cur_country, sanity_rank = mc.group(1), 0; used.add(k); continue
                ms = SANITY_RE.match(s)
                if ms:
                    sanity_rank += 1
                    tables["kontrol_sanity_top5"].append(dict(base, Negara=cur_country, Rank=sanity_rank,
                                                              Artefak=ms.group(1).strip(), Prob_as_printed=to_num(ms.group(2))))
                    used.add(k); continue
            if sec == "d":
                md = DW_RE.match(s)
                if md:
                    tables["d_bobot_region"].append(dict(base, Region=md.group(1).strip(), N=to_num(md.group(2)),
                                                         total_w=to_num(md.group(3))))
                    used.add(k); continue
                if EFF_HDR.match(s):
                    mode = "eff"; used.add(k); continue
                if RANK_HDR.match(s):
                    mode = "rank"; used.add(k); continue
                if re.fullmatch(r"-{20,}", s):
                    used.add(k); continue
                if mode == "eff":
                    me = EFF_RE.match(s)
                    if me:
                        tables["d_effect_size"].append(dict(base, Region=me.group(1).strip(), Orig=to_num(me.group(2)),
                                                            Bal=to_num(me.group(3)), PctChange=to_num(me.group(4)),
                                                            Status=me.group(5)))
                        used.add(k); continue
                    mode = None
                if mode == "rank":
                    mr = RANK_RE.match(s)
                    if mr:
                        dr = mr.group(6)
                        tables["d_ranking"].append(dict(base, Region=mr.group(1).strip(), Orig_deg=to_num(mr.group(2)),
                                                        Rank_Orig=int(mr.group(3)), Bal_deg=to_num(mr.group(4)),
                                                        Rank_Bal=int(mr.group(5)), DeltaRank_raw=dr,
                                                        DeltaRank_naik_positif=0 if dr == "=" else (int(dr[1:]) if dr[0] == "↑" else -int(dr[1:]))))
                        used.add(k); continue
                    mode = None
            mb = BRACKET_RE.match(s)
            if mb:
                label = mb.group(1).replace("⏳ ", "")
                items = ast.literal_eval(mb.group(5))
                if mb.group(4) is not None:
                    if int(mb.group(4)) != len(items):
                        raise SystemExit(f"[{fname}] jumlah list {label} tidak cocok")
                    add_scalar(sec, f"{sec}.n_region[{label}]", mb.group(4), s, cell)
                if not items:
                    tables["daftar_region"].append(dict(base, section=sec, daftar=label, urutan=0, Region="(kosong)"))
                for j, it in enumerate(items, 1):
                    tables["daftar_region"].append(dict(base, section=sec, daftar=label, urutan=j, Region=it))
                used.add(k); continue
            if sec == "c3":
                msk = SALAH_KIRA_RE.match(s)
                if msk:
                    pending_salah = (msk.group(1), msk.group(2)); used.add(k); continue
                mj = JARAK_RE.match(s)
                if mj:
                    if pending_salah is None or pending_salah[1] != mj.group(1):
                        raise SystemExit(f"[{fname}] baris jarak C.3 tanpa pasangan: {s}")
                    tables["c3_salah_kira"].append(dict(base, Region=pending_salah[0], Dikira_dari=pending_salah[1],
                                                        Jarak_ke_target_1dp=to_num(mj.group(2)),
                                                        Jarak_ke_asli_1dp=to_num(mj.group(3))))
                    pending_salah = None; used.add(k); continue
            if sec == "c4":
                ml = LOWDISC_RE.match(s)
                if ml:
                    tables["c4_low_error_low_discrim"].append(dict(base, Region=ml.group(1).strip(),
                                                                   Avg_Error_2dp=to_num(ml.group(2)),
                                                                   Structure_Correlation_3dp=to_num(ml.group(3))))
                    used.add(k); continue
            if sec == "lw1":
                mp = PROG_NEW.match(s)
                if mp:
                    tables["layerwise_individual_progress"].append(dict(base, Layer=int(mp.group(1)), Err_2dp=to_num(mp.group(4)),
                                                                        detik_kumulatif=to_num(mp.group(5))))
                    used.add(k); continue
                mp = PROG_OLD.match(s)
                if mp:
                    tables["layerwise_individual_progress"].append(dict(base, Layer=int(mp.group(1)), Err_2dp=to_num(mp.group(2)),
                                                                        detik_kumulatif=to_num(mp.group(3))))
                    used.add(k); continue
                mm2 = MELANJUT_RE.match(s)
                if mm2:
                    add_scalar(sec, "lw1.resume_layer_selesai", mm2.group(1), s, cell); used.add(k); continue
            # verdict
            hit = False
            for vs, vr, vn in VERDICTS:
                if vs == sec:
                    mv = vr.match(s)
                    if mv:
                        add_scalar(sec, vn, mv.group(1), s, cell); used.add(k); hit = True; break
            if hit:
                continue
            # skalar
            for ss, sr, names in SCALARS:
                if ss != sec:
                    continue
                mx = sr.match(s)
                if mx:
                    if names[0] == "@cekfitur":
                        cekfitur_n += 1
                        nm = "lw1.cek_fitur_maxdiff_agregat" if cekfitur_n == 1 else "lw1.cek_fitur_maxdiff_individual"
                        add_scalar(sec, nm, mx.group(2), s, cell)
                    else:
                        for g, nm in enumerate(names, 1):
                            if nm is not None and mx.group(g) is not None:
                                add_scalar(sec, nm, mx.group(g), s, cell)
                    used.add(k); hit = True; break
            if hit:
                continue
            if re.search(r"\d", s):
                why = next((w for (isec, ir, w) in IGNORE if (isec is None or isec == sec) and ir.search(s)), None)
                if why:
                    ignored.append(dict(base, cell_idx=cell["idx"], section=sec, alasan=why, line=s[:300]))
                else:
                    audit.append(dict(base, cell_idx=cell["idx"], section=sec, line=s[:300]))
        close_list()
        if pending_salah is not None:
            raise SystemExit(f"[{fname}] baris salah-kira C.3 tanpa jarak")
    return base, tables, scalars, audit, ignored, seen_tables


# ----------------------------------------------------------------------------
# 5. Main
# ----------------------------------------------------------------------------
SUMMARY_COLS = [
    ("kontrol.err", "Kontrol_err"), ("kontrol.err_sd", "Kontrol_sd"), ("kontrol.n", "Kontrol_n"),
    ("kontrol.r2_lat", "Kontrol_R2_lat"), ("kontrol.r2_lon", "Kontrol_R2_lon"),
    ("a.err", "Agregat_err"), ("a.err_sd", "Agregat_sd"), ("a.n", "Agregat_n"),
    ("a.r2_lat", "Agregat_R2_lat"), ("a.r2_lon", "Agregat_R2_lon"),
    ("eksklusif.err", "Eksklusif_err"), ("eksklusif.n_negara", "Eksklusif_n_negara"),
    ("eksklusif.r2_lat", "Eksklusif_R2_lat"), ("eksklusif.r2_lon", "Eksklusif_R2_lon"),
    ("b.err", "Individual_err"), ("b.err_sd", "Individual_sd"), ("b.n", "Individual_n"),
    ("b.r2_lat", "Individual_R2_lat"), ("b.r2_lon", "Individual_R2_lon"), ("b.alpha", "Individual_alpha"),
    ("null.err", "Null_err"), ("null.err_sd", "Null_sd"), ("static.err", "Static_err"), ("static.err_sd", "Static_sd"),
    ("d.alpha_balanced", "D_alpha_balanced"),
    ("c2.spearman_r_err_vs_biasratio", "C2_spearman_r"), ("c3.direction_consistency_R", "C3_R"),
    ("c3.mean_bias_direction_deg", "C3_mean_dir_deg"), ("c4.corr_err_vs_normerr_r", "C4_r_err_normerr"),
    ("lw0.n_layer_plus_emb", "LW_n_layer_incl_emb"),
    ("lw1.agg_err_layer0", "LW_agg_err_L0"), ("lw1.agg_best_layer", "LW_agg_best_layer"),
    ("lw1.agg_best_depth_pct", "LW_agg_best_depth_pct"), ("lw1.agg_best_err", "LW_agg_best_err"),
    ("lw1.agg_last_err", "LW_agg_last_err_mean5seed"), ("lw1.agg_seed_sd_at_best", "LW_agg_seed_sd_at_best"),
    ("lw1.ind_err_layer0", "LW_ind_err_L0"), ("lw1.ind_best_layer", "LW_ind_best_layer"),
    ("lw1.ind_best_depth_pct", "LW_ind_best_depth_pct"), ("lw1.ind_best_err", "LW_ind_best_err"),
    ("lw1.ind_last_err", "LW_ind_last_err"), ("lw1.pct_fold_layer_alpha_di_batas", "LW_ind_pct_alpha_at_500"),
    ("lw1.replikasi_agg_layerwise", "LW_replik_agg_layerwise"), ("lw1.replikasi_agg_cell_asli", "LW_replik_agg_asli"),
    ("lw1.replikasi_ind_layerwise", "LW_replik_ind_layerwise"), ("lw1.replikasi_ind_cell_asli", "LW_replik_ind_asli"),
    ("lw1.cek_fitur_maxdiff_agregat", "LW_cekfitur_agg_maxdiff"), ("lw1.cek_fitur_maxdiff_individual", "LW_cekfitur_ind_maxdiff"),
    ("lw0.maxdiff_last_vs_cache", "LW0_maxdiff_vs_cache"),
]


def write_csv(path, rows):
    if not rows:
        return
    cols = []
    for r in rows:
        for c in r:
            if c not in cols:
                cols.append(c)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", default="hasil_csv")
    ap.add_argument("--xlsx", action="store_true", help="juga tulis semua tabel ke satu file .xlsx")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    all_tables = collections.defaultdict(list)
    all_scalars, all_audit, all_ignored, metas = [], [], [], []
    table_counts = {}
    for fname, nb in iter_notebooks(args.inputs):
        base, tables, scalars, audit, ignored, seen = parse_notebook(fname, nb)
        metas.append(dict(base, file=fname))
        for k, v in tables.items():
            all_tables[k].extend(v)
        all_scalars += scalars; all_audit += audit; all_ignored += ignored
        table_counts[(base["model"], base["domain"])] = seen
        print(f"  {fname}: {sum(len(v) for v in tables.values())} baris tabel, {len(scalars)} skalar, "
              f"{len(audit)} baris tak terbaca")

    # skalar duplikat (metrik sama muncul >1x dengan nilai beda) = tanda bahaya
    dup = collections.defaultdict(set)
    for s in all_scalars:
        dup[(s["model"], s["domain"], s["metric"])].add(s["value"])
    conflicts = {k: v for k, v in dup.items() if len(v) > 1}
    for k, v in conflicts.items():
        all_audit.append(dict(model=k[0], domain=k[1], line=f"KONFLIK metrik {k[2]}: {sorted(map(str, v))}"))

    # ringkasan wide: satu baris per model x domain
    summary = []
    for m in metas:
        row = dict(model=m["model"], model_id=m["model_id"], domain=m["domain"])
        vals = {s["metric"]: s["value"] for s in all_scalars if s["model"] == m["model"] and s["domain"] == m["domain"]}
        for met, col in SUMMARY_COLS:
            row[col] = vals.get(met, "")
        summary.append(row)

    write_csv(os.path.join(args.out, "00_ringkasan_per_model.csv"), summary)
    write_csv(os.path.join(args.out, "01_semua_skalar_long.csv"), all_scalars)
    for name in sorted(all_tables):
        write_csv(os.path.join(args.out, f"{name}.csv"), all_tables[name])
    write_csv(os.path.join(args.out, "_audit_unparsed_lines.csv"),
              all_audit or [dict(status="OK: semua baris berangka tertangkap atau diabaikan dengan alasan")])
    write_csv(os.path.join(args.out, "_audit_ignored_lines.csv"), all_ignored)
    write_csv(os.path.join(args.out, "_sumber_notebook.csv"), metas)

    if args.xlsx:
        import pandas as pd
        with pd.ExcelWriter(os.path.join(args.out, "semua_hasil.xlsx")) as xw:
            pd.DataFrame(summary).to_excel(xw, sheet_name="00_ringkasan", index=False)
            pd.DataFrame(all_scalars).to_excel(xw, sheet_name="01_skalar_long", index=False)
            for name in sorted(all_tables):
                pd.DataFrame(all_tables[name]).to_excel(xw, sheet_name=name[:31], index=False)

    print(f"\n{len(metas)} notebook, {len(all_tables)} jenis tabel, {len(all_scalars)} skalar -> {args.out}/")
    if all_audit:
        print(f"PERINGATAN: {len(all_audit)} baris berangka TIDAK terbaca / konflik; lihat _audit_unparsed_lines.csv")
        for a in all_audit[:30]:
            print("   ", a.get("model"), a.get("domain"), a.get("section"), "|", a["line"][:140])
        sys.exit(1)
    print("Audit: semua baris berangka tertangkap (atau diabaikan dengan alasan tertulis).")


if __name__ == "__main__":
    main()
