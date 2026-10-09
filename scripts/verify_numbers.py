#!/usr/bin/env python3
"""Verifikasi independen: bandingkan multiset angka di output notebook (sumber)
dengan multiset angka di CSV hasil ekstraksi, per model x domain.
Tidak memakai kode parser extract_results.py (hanya membaca CSV-nya)."""
import collections, csv, glob, json, os, re, sys, zipfile

zips, outdir = sys.argv[1:-1], sys.argv[-1]

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
TOK = re.compile(r"(?<![A-Za-z_\d.])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")
META = {"model", "model_id", "domain", "row_order", "urutan", "Rank", "DeltaRank_naik_positif", "cell_idx",
        "section", "metric", "source_line", "daftar", "file", "alasan", "line", "status"}

# baris yang diabaikan extractor (ambil dari _audit_ignored_lines.csv) -> dikecualikan dari sumber
ignored = collections.Counter()
for r in csv.DictReader(open(os.path.join(outdir, "_audit_ignored_lines.csv"), encoding="utf-8-sig")):
    ignored[(r["model"], r["domain"], r["line"])] += 1

src = collections.defaultdict(collections.Counter)
exp_unc = collections.defaultdict(collections.Counter)
# Baris yang berisi angka non-hasil. Bagian angka HASIL di baris ini diambil lagi lewat KEEP_FROM_EXPECT.
EXPECT = re.compile("|".join([
    r"^EKSPERIMEN C\.\d", r"^EXPERIMENT [\d.]+ SELESAI", r"^Error (In|Ex)clusive \(Exp", r"^Ratio -> ",
    r"^\(Rank_Diff = 0", r"^KLASIFIKASI 2x2", r"range \[0,1\] eksak", r"^\(R mendekati", r"^\(Improvement_vs_Self > 0",
    r"^Tinggi \(-> 1\)", r"^- Normalized_Error tinggi \(>1\)", r"negara2 di dalamnya", r"region terbaik di kondisi",
    r"^CentDist_Change [<>] 0", r"^BASELINE EKSKLUSIF — PROBING LINEAR \(HANYA", r"^Logika: Hanya menggunakan",
    r"^LAYER-WISE [01] —", r"^Cek fitur layer terakhir vs Cell", r"vs Cell \d+ = ", r"^Agregat\s+: layer|^Individual: layer",
    r"^Noise CV Agregat", r"^- Artefak multi-negara \(diklaim >1", r"^F_all: ", r"^Individual layer\s+\d+ ",
    r"^Region Bias_Ratio > 0\.4", r"^AGREGAT \(Err_s42", r"^Cek asumsi OK: hidden_states\[-1\]",
]))
def KEEP_FROM_EXPECT(s):
    """angka hasil yang ADA di baris EXPECT (ditangkap extractor)"""
    pats = [
        (r"^Error (?:In|Ex)clusive \(Exp [\d.]+\): ([-\d.]+)°", [1]),
        (r"^Cek fitur layer terakhir vs Cell \d+: selisih maks ([-\d.e+]+)$", [1]),
        (r"^(?:Agregat|Individual)\s*: ([\d.]+)°\s+vs Cell \d+ = ([\d.]+)°$", [1, 2]),
        (r"^(?:Agregat|Individual)\s*: layer \d+ = ([\d.]+)° \| terbaik = layer (\d+) \((\d+)% kedalaman\) ([\d.]+)° \| terakhir = ([\d.]+)°$", [1, 2, 3, 4, 5]),
        (r"^Noise CV Agregat pada layer terbaik: SD antar-seed = ([\d.]+)°", [1]),
        (r"^- Artefak multi-negara \(diklaim >1 negara\): (\d+) \(([\d.]+)%\)$", [1, 2]),
        (r"^F_all: \((\d+), (\d+), (\d+)\)", [1, 2, 3]),
        (r"^Individual layer\s+(\d+) \(\d+/\d+\) \| err\s+([\d.]+)° \|\s+(\d+)s berjalan", [1, 2, 3]),
        (r"^Individual layer\s+(\d+) \| err\s+([\d.]+)° \|\s+(\d+)s \(sisa", [1, 2, 3]),
        (r"^Region Bias_Ratio > 0\.4", []),
        (r"^Cek asumsi OK: hidden_states\[-1\] == keluaran final norm \(selisih maks ([-\d.e+]+)\)", [1]),
    ]
    for p, gs in pats:
        m = re.search(p, s)
        if m:
            return [m.group(g) for g in gs]
    return []
for fname, nb in iter_nbs(zips):
    m = re.match(r"(.+?)_(kuliner|musik)_", fname)
    key = (m.group(1), m.group(2))
    ign = collections.Counter({k[2]: v for k, v in ignored.items() if (k[0], k[1]) == key})
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        txt = "".join("".join(o["text"]) for o in c.get("outputs", [])
                      if o.get("output_type") == "stream" and o.get("name") == "stdout")
        for line in txt.split("\n"):
            s = line.strip()
            if ign.get(s[:300], 0) > 0:
                ign[s[:300]] -= 1
                continue
            if EXPECT.search(s):
                for t in TOK.findall(s):
                    exp_unc[key][float(t)] += 1
                for t in KEEP_FROM_EXPECT(s):
                    src[key][float(t)] += 1
                    exp_unc[key][float(t)] -= 1
                continue
            for t in TOK.findall(s):
                src[key][float(t)] += 1

got = collections.defaultdict(collections.Counter)
for p in glob.glob(os.path.join(outdir, "*.csv")):
    b = os.path.basename(p)
    if b.startswith("_") or b.startswith("00_"):
        continue  # 00_ringkasan = turunan dari 01_skalar (dicek terpisah)
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        key = (r["model"], r["domain"])
        for col, v in r.items():
            if col in META or v in ("", None):
                continue
            if col == "DeltaRank_raw":
                if v != "=":
                    got[key][float(v[1:])] += 1
                continue
            try:
                got[key][float(v)] += 1
            except ValueError:
                for t in TOK.findall(v):  # teks (mis. path di skalar) bisa mengandung angka
                    got[key][float(t)] += 1

bad = 0
for key in sorted(src):
    missing = src[key] - got[key]      # ada di sumber, tidak di CSV
    extra = got[key] - src[key]        # ada di CSV, tidak di sumber  (HARUS kosong)
    print(f"{key}: sumber={sum(src[key].values())} csv={sum(got[key].values())} "
          f"| tak-terambil={sum(missing.values())} | ekstra(tidak ada di sumber)={sum(extra.values())}")
    if extra:
        bad += 1
        print("   EKSTRA:", sorted(extra.items())[:20])
    if missing:
        print("   tak-terambil:", sorted(missing.items())[:40])
print("HASIL:", "GAGAL" if bad else "OK: setiap angka di CSV benar-benar ada di output notebook")
