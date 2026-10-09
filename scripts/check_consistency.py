#!/usr/bin/env python3
"""Cek semantik hasil ekstraksi:
 (A) re-parse independen setiap tabel pandas dengan cara BERBEDA (split dari kanan, bukan posisi kolom)
     lalu bandingkan sel per sel dengan CSV (menangkap salah kolom/salah baris, bukan cuma salah angka);
 (B) cek silang antar-angka yang seharusnya identik (replikasi, pembulatan, tabel yang mengulang kolom).
"""
import csv, collections, json, math, os, re, sys, zipfile

zips, out = sys.argv[1:-1], sys.argv[-1]

def iter_nbs(inputs):
    """Yield (nama_file, notebook_dict) dari zip / folder / .ipynb (sama seperti extract_results.py)."""
    import glob as _g
    for inp in inputs:
        if os.path.isdir(inp):
            for p in sorted(_g.glob(os.path.join(inp, "**", "*.ipynb"), recursive=True)):
                if not os.path.basename(p).startswith("."):
                    yield os.path.basename(p), json.load(open(p, encoding="utf-8"))
        elif inp.endswith(".ipynb"):
            yield os.path.basename(inp), json.load(open(inp, encoding="utf-8"))
        else:
            with zipfile.ZipFile(inp) as zf:
                for n in zf.namelist():
                    if n.endswith(".ipynb") and not os.path.basename(n).startswith("."):
                        yield os.path.basename(n), json.loads(zf.read(n))
def rd(name):
    p = os.path.join(out, name + ".csv")
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if os.path.exists(p) else []
def f(x): return float(x)

fails, n_checks = [], 0
def check(cond, msg):
    global n_checks
    n_checks += 1
    if not cond:
        fails.append(msg)

# ---------------------------------------------------------------- (A) re-parse independen
REGIONS = sorted({r["Region"] for r in rd("c1_centroid")}, key=len, reverse=True)
TEXT_TAIL = {"Mechanism", "Mechanism_2x2"}
def reparse(line, cols):
    """parse baris tabel: kolom pertama = nama region (bisa berspasi); kolom teks lain dikenali via daftar region
    atau sebagai ekor teks bebas (Mechanism)."""
    s = line.strip()
    if cols[0] == "Layer":
        v = s.split()
        return v if len(v) == len(cols) else None
    reg = next((r for r in REGIONS if s.startswith(r + " ")), None)
    if reg is None:
        return None
    rest = s[len(reg):].split()
    vals = [reg]
    for c in cols[1:]:
        if c in TEXT_TAIL:
            vals.append(" ".join(rest)); rest = []
        elif c == "Closest_Confusion_Target":
            tgt = next(r for r in REGIONS if " ".join(rest).startswith(r))
            vals.append(tgt); rest = " ".join(rest)[len(tgt):].split()
        else:
            vals.append(rest.pop(0))
    return vals if not rest else None

TABLES = ["regional_kontrol", "regional_agregat", "regional_eksklusif", "c1_centroid", "c1_centroid_distance",
          "c1_mekanisme", "c2_bias_ratio", "c2_ranking", "c2_klasifikasi_2x2", "c3_bias_vector",
          "c3_confusion_target", "c4_normalized_error", "c4_rank_shift", "c4_structure_correlation",
          "c4_gabungan", "d_perbandingan", "d_top10_original", "d_top10_balanced", "null_jarak_region",
          "layerwise_agregat", "layerwise_individual"]
src_text = {}
for fname, nb in iter_nbs(zips):
    m = re.match(r"(.+?)_(kuliner|musik)_", fname)
    src_text[(m.group(1), m.group(2))] = "\n".join(
        "".join("".join(o["text"]) for o in c.get("outputs", []) if o.get("output_type") == "stream"
                and o.get("name") == "stdout") for c in nb["cells"] if c["cell_type"] == "code")

for t in TABLES:
    rows = rd(t)
    by_nb = collections.defaultdict(list)
    for r in rows:
        by_nb[(r["model"], r["domain"])].append(r)
    for key, rs in by_nb.items():
        cols = [c for c in rs[0] if c not in ("model", "model_id", "domain", "row_order")]
        lines = src_text[key].split("\n")
        # temukan blok header di sumber yang kolomnya persis sama
        hdr_idx = [i for i, l in enumerate(lines) if l.split() == cols]
        # jika header sama muncul >1x (tidak terjadi kecuali regional), cocokkan blok dengan jumlah baris
        matched = False
        for hi in hdr_idx:
            blk = lines[hi + 1: hi + 1 + len(rs)]
            parsed = [reparse(l, cols) for l in blk]
            if any(p is None for p in parsed):
                continue
            ok = all(
                (abs(f(p[j]) - f(r[c])) == 0 if re.fullmatch(r"[-+\d.e]+", p[j]) else p[j] == r[c])
                for p, r in zip(parsed, rs) for j, c in enumerate(cols))
            if ok:
                matched = True
                break
        check(matched, f"(A) {t} {key}: re-parse independen TIDAK cocok dengan CSV")

# ---------------------------------------------------------------- (B) cek silang
S = collections.defaultdict(dict)
for r in rd("01_semua_skalar_long"):
    S[(r["model"], r["domain"])][r["metric"]] = r["value"]
def r2(x, d): return round(float(x) + 0.0, d)
def near(a, b, d):  # a sudah dibulatkan d desimal di output; b nilai presisi lebih tinggi
    return abs(float(a) - float(b)) <= 0.5 * 10 ** (-d) + 1e-9

def idx(rows, *keys):
    o = collections.defaultdict(dict)
    for r in rows:
        o[(r["model"], r["domain"])][tuple(r[k] for k in keys)] = r
    return o

LA, LI, PR = idx(rd("layerwise_agregat"), "Layer"), idx(rd("layerwise_individual"), "Layer"), idx(rd("layerwise_individual_progress"), "Layer")
for key, s in S.items():
    la, li = LA[key], LI[key]
    L = sorted(int(k[0]) for k in la)
    last = str(L[-1])
    check(L == list(range(len(L))), f"{key} layer agregat tidak kontinu")
    check(sorted(int(k[0]) for k in li) == L, f"{key} layer individual != agregat")
    check(len(L) == int(s["lw0.n_layer_plus_emb"]) == int(s["lw1.agg_n_layer"]) == int(s["lw1.ind_n_layer"]),
          f"{key} jumlah layer tidak konsisten")
    check(int(s["setup.n_layers"]) + 1 == len(L), f"{key} n_layers model + 1 != jumlah layer probing")
    # replikasi
    check(near(s["lw1.replikasi_agg_layerwise"], la[(last,)]["Err_s42"], 2), f"{key} replikasi agg vs tabel")
    check(near(s["lw1.replikasi_ind_layerwise"], li[(last,)]["Err"], 2), f"{key} replikasi ind vs tabel")
    check(near(s["lw1.replikasi_agg_cell_asli"], s["a.err"], 2) or s["lw1.replikasi_agg_cell_asli"] == s["a.err"],
          f"{key} replikasi agg 'Cell asli' != a.err ({s['lw1.replikasi_agg_cell_asli']} vs {s['a.err']})")
    check(s["lw1.replikasi_ind_cell_asli"] == s["b.err"], f"{key} replikasi ind 'Cell asli' != b.err")
    # ringkasan layerwise
    em = {int(k[0]): float(v["Err_mean"]) for k, v in la.items()}
    ei = {int(k[0]): float(v["Err"]) for k, v in li.items()}
    check(near(s["lw1.agg_err_layer0"], em[0], 2) and near(s["lw1.agg_last_err"], em[L[-1]], 2), f"{key} ringkasan agg L0/last")
    check(int(s["lw1.agg_best_layer"]) == min(em, key=em.get), f"{key} best layer agg != argmin Err_mean")
    check(near(s["lw1.agg_best_err"], em[int(s["lw1.agg_best_layer"])], 2), f"{key} best err agg")
    check(near(s["lw1.agg_seed_sd_at_best"], la[(s["lw1.agg_best_layer"],)]["Err_sd"], 2), f"{key} SD seed at best")
    check(near(s["lw1.ind_err_layer0"], ei[0], 2) and near(s["lw1.ind_last_err"], ei[L[-1]], 2), f"{key} ringkasan ind L0/last")
    check(int(s["lw1.ind_best_layer"]) == min(ei, key=ei.get), f"{key} best layer ind != argmin Err")
    pct = sum(float(v["Alpha_di_batas"]) for v in li.values()) / len(li) * 100
    check(abs(pct - float(s["lw1.pct_fold_layer_alpha_di_batas"])) <= 0.5 + 1e-9, f"{key} % alpha di batas ({pct:.1f})")
    for k, v in PR[key].items():
        check(near(v["Err_2dp"], li[k]["Err"], 2), f"{key} progress layer {k} != tabel")
    # baseline & ringkasan kondisi
    check(s["ringkasan.probe_b_err"] == s["b.err"] and s["ringkasan.null_err"] == s["null.err"]
          and s["ringkasan.static_err"] == s["static.err"], f"{key} tabel ringkasan kondisi")
    check(s["null.n"] == s["static.n"] == s["b.n"], f"{key} n null/static/B beda")
    # eksklusif
    check(s["eksklusif.err_inclusive_ref"] == s["a.err"] and s["eksklusif.err_exclusive_ref"] == s["eksklusif.err"],
          f"{key} eksklusif ref")
    d = float(s["eksklusif.err"]) - float(s["a.err"])
    check(abs(abs(d) - float(s.get("eksklusif.err_naik", s.get("eksklusif.err_turun", "nan")))) <= 0.011, f"{key} selisih eksklusif")

# antar tabel per region
def by_reg(t):
    return idx(rd(t), "Region")
C1, C1D, C1M, C2, C2R, C2K, C3, C3C, C4N, C4R, C4G, C4S, DP, DE, DR, DB, SK, LD = map(by_reg, [
    "c1_centroid", "c1_centroid_distance", "c1_mekanisme", "c2_bias_ratio", "c2_ranking", "c2_klasifikasi_2x2",
    "c3_bias_vector", "c3_confusion_target", "c4_normalized_error", "c4_rank_shift", "c4_gabungan",
    "c4_structure_correlation", "d_perbandingan", "d_effect_size", "d_ranking", "d_bobot_region", "c3_salah_kira",
    "c4_low_error_low_discrim"])
for key in S:
    for (reg,), r in C1[key].items():
        ae = r["Avg_Error"]
        check(C1D[key][(reg,)]["Avg_Error"] == ae == C1M[key][(reg,)]["Avg_Error"] == C2[key][(reg,)]["Avg_Error"]
              == C2R[key][(reg,)]["Avg_Error"] == C2K[key][(reg,)]["Avg_Error"] == C4N[key][(reg,)]["Avg_Error"]
              == C4R[key][(reg,)]["Avg_Error"], f"{key} {reg} Avg_Error beda antar tabel")
        cd = C1D[key][(reg,)]["Centroid_Distance"]
        check(cd == C2[key][(reg,)]["Centroid_Distance"] == C3[key][(reg,)]["Centroid_Distance"]
              == C3C[key][(reg,)]["Centroid_Distance_to_Self"] == DP[key][(reg,)]["CentDist_Original"],
              f"{key} {reg} Centroid_Distance beda antar tabel")
        check(r["Pred_Spread"] == C1D[key][(reg,)]["Pred_Spread"] == C2[key][(reg,)]["Pred_Spread"], f"{key} {reg} spread")
        check(r["N_Artifacts"] == C2[key][(reg,)]["N_Artifacts"] == C1M[key][(reg,)]["N_Artifacts"]
              == DB[key][(reg,)]["N"], f"{key} {reg} N_Artifacts/N bobot beda")
        br = C2[key][(reg,)]["Bias_Ratio"]
        check(br == C2R[key][(reg,)]["Bias_Ratio"] == C2K[key][(reg,)]["Bias_Ratio"] == C3[key][(reg,)]["Bias_Ratio"]
              == DP[key][(reg,)]["BiasRatio_Original"], f"{key} {reg} Bias_Ratio beda")
        # magnitude vektor bias == centroid distance (great-circle) -> sqrt(N^2+E^2) ~ distance
        bv = C3[key][(reg,)]
        mag = math.hypot(float(bv["Bias_Vec_North"]), float(bv["Bias_Vec_East"]))
        check(abs(mag - float(cd)) < 1e-3, f"{key} {reg} |bias vec| != Centroid_Distance ({mag} vs {cd})")
        check(abs(math.degrees(math.atan2(float(bv["Bias_Vec_North"]), float(bv["Bias_Vec_East"]))) - float(bv["Bias_Angle_Deg"])) < 1e-3,
              f"{key} {reg} sudut bias")
        de, dr, dp = DE[key][(reg,)], DR[key][(reg,)], DP[key][(reg,)]
        check(near(de["Orig"], dp["BiasRatio_Original"], 3) and near(de["Bal"], dp["Bias_Ratio_Bal"], 3), f"{key} {reg} effect size vs perbandingan")
        check(near(dr["Orig_deg"], dp["CentDist_Original"], 2) and near(dr["Bal_deg"], dp["CentDist_Balanced"], 2), f"{key} {reg} ranking vs perbandingan")
        check(abs(float(dp["CentDist_Balanced"]) - float(dp["CentDist_Original"]) - float(dp["CentDist_Change"])) < 1e-5, f"{key} {reg} CentDist_Change")
        check(int(dr["Rank_Orig"]) - int(dr["Rank_Bal"]) == int(dr["DeltaRank_naik_positif"]), f"{key} {reg} ΔRank")
        if (reg,) in SK[key]:
            sk, cc = SK[key][(reg,)], C3C[key][(reg,)]
            check(sk["Dikira_dari"] == cc["Closest_Confusion_Target"] and near(sk["Jarak_ke_target_1dp"], cc["Distance_to_Target"], 1)
                  and near(sk["Jarak_ke_asli_1dp"], cc["Centroid_Distance_to_Self"], 1) and float(cc["Improvement_vs_Self"]) > 0,
                  f"{key} {reg} salah-kira vs confusion table")
        if (reg,) in C4G[key]:
            g = C4G[key][(reg,)]
            check(g["Normalized_Error"] == C4N[key][(reg,)]["Normalized_Error"] and g["Bias_Ratio"] == br
                  and g["Structure_Correlation"] == C4S[key][(reg,)]["Structure_Correlation"], f"{key} {reg} c4 gabungan")
        if (reg,) in LD[key]:
            check(near(LD[key][(reg,)]["Avg_Error_2dp"], ae, 2), f"{key} {reg} low-discrim list")
    # semua region dengan Improvement>0 harus muncul di daftar salah-kira
    pos = {r for (r,), v in C3C[key].items() if float(v["Improvement_vs_Self"]) > 0}
    check(pos == {r for (r,) in SK[key]}, f"{key} daftar salah-kira != Improvement>0")
    # c1 n_baris = jumlah N_Artifacts
    check(sum(int(v["N_Artifacts"]) for v in C1[key].values()) == int(S[key]["c1.n_baris"]) == int(S[key]["b.n"]),
          f"{key} jumlah N_Artifacts != n individual")
    # regional kontrol / agregat: jumlah Count == n
    for t, nm in [("regional_kontrol", "kontrol.n"), ("regional_agregat", "a.n")]:
        tot = sum(int(r["Count"]) for r in rd(t) if (r["model"], r["domain"]) == key)
        check(tot == int(S[key][nm]), f"{key} jumlah Count {t} ({tot}) != {nm} ({S[key][nm]})")
    tot = sum(int(r["Count"]) for r in rd("regional_eksklusif") if (r["model"], r["domain"]) == key)
    check(tot == int(S[key]["eksklusif.n_negara"]), f"{key} jumlah Count eksklusif ({tot}) != n_negara eksklusif")

# daftar region vs tabel
DF = collections.defaultdict(lambda: collections.defaultdict(set))
for r in rd("daftar_region"):
    if r["Region"] != "(kosong)":
        DF[(r["model"], r["domain"])][(r["section"], r["daftar"])].add(r["Region"])
for key in S:
    lists = DF[key]
    for (reg,), v in C1M[key].items():
        check(reg in lists[("c1", v["Mechanism"])], f"{key} {reg} tidak di daftar c1 '{v['Mechanism']}'")
    for (reg,), v in C2K[key].items():
        check(reg in lists[("c2", v["Mechanism_2x2"])], f"{key} {reg} tidak di daftar c2 '{v['Mechanism_2x2']}'")
    sysb = {r for (r,), v in C2K[key].items() if "Systematic Bias" in v["Mechanism_2x2"]}
    check(sysb == lists[("c3", "Region dengan Systematic Bias")], f"{key} daftar Systematic Bias C.3")
    check({r for (r,), v in DP[key].items() if float(v["BiasRatio_Original"]) > 0.4} == lists[("d", "Region Bias_Ratio > 0.4 (original)")], f"{key} D >0.4 original")
    check({r for (r,), v in DP[key].items() if float(v["Bias_Ratio_Bal"]) > 0.4} == lists[("d", "Region Bias_Ratio > 0.4 (balanced)")], f"{key} D >0.4 balanced")
    hi, lo = lists[("c1", "High-error regions")], lists[("c1", "Low-error regions")]
    check(not (hi & lo) and (hi | lo) == {r for (r,) in C1[key]}, f"{key} high/low error partisi")
    check(min(float(C1[key][(r,)]["Avg_Error"]) for r in hi) >= max(float(C1[key][(r,)]["Avg_Error"]) for r in lo), f"{key} high>=low error")

# 00_ringkasan == skalar
for r in rd("00_ringkasan_per_model"):
    key = (r["model"], r["domain"])
    for col, v in r.items():
        if col in ("model", "model_id", "domain") or v == "":
            continue
    check(r["Individual_err"] == S[key]["b.err"] and r["Agregat_err"] == S[key]["a.err"], f"{key} ringkasan wide")

print(f"{n_checks} cek dijalankan, {len(fails)} gagal")
for m in fails:
    print("  GAGAL:", m)
