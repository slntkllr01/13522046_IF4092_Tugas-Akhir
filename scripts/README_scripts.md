# Scripts

Three scripts extract the numbers that the notebooks print and check them against the notebook outputs. They read the stored outputs of the `.ipynb` files; they do not run any model.
The results of the last run are described in [`../results/summary/README_summary.md`](../results/summary/README_summary.md).

| Script | Purpose |
|---|---|
| `extract_results.py` | Parses the stdout of all notebook cells (scalars, pandas tables, printed lists) and writes CSV files. `--xlsx` also writes `semua_hasil.xlsx`. |
| `verify_numbers.py` | Check 1: for each model x domain, the multiset of numbers in the notebook output must equal the multiset of numbers in the CSV files. It does not use the parser code. |
| `check_consistency.py` | Check 2: re-parses every pandas table with a different method (split from the right) and compares cell by cell, then runs cross-checks between tables that must agree. |

## Requirements

Python 3. The three scripts use the standard library only; `--xlsx` additionally imports `pandas` and needs an Excel writer package for pandas (for example `openpyxl`).

## Usage

Run from the repository root. The same commands work in PowerShell and in bash.

```
python scripts/extract_results.py notebooks/culinary notebooks/instrument -o _tmp_tables
python scripts/verify_numbers.py   notebooks/culinary notebooks/instrument _tmp_tables
python scripts/check_consistency.py notebooks/culinary notebooks/instrument _tmp_tables
```

- Inputs can be a zip file, a folder that contains `.ipynb` files (searched recursively), or a single `.ipynb` file.
- For `extract_results.py`, `-o` (`--out`) is the output folder; the default is `hasil_csv`. `verify_numbers.py` and `check_consistency.py` take the input paths first and the CSV folder last.
- The expected result: `verify_numbers.py` ends with `HASIL: OK: setiap angka di CSV benar-benar ada di output notebook` and `check_consistency.py` prints `4815 cek dijalankan, 0 gagal`.
- The CSV files in `_tmp_tables` are identical to the files in `results/summary/` (`00_*`, `01_*` and `tables/`). `_tmp_tables` is a temporary folder; delete it after the comparison.

## What the checks cover

- Line audit in `extract_results.py`: every output line with a number is parsed or ignored with a written reason (`_audit_ignored_lines.csv`); an unknown table header stops the script.
- `verify_numbers.py`: numbers that are not results (section numbers, thresholds in explanatory text, progress counters) are excluded through a list of regular expressions in the script.
- `check_consistency.py`: values that appear in several tables must be identical, the length of the bias vector must equal `Centroid_Distance`, the layer-wise summary must equal the argmin of the table,
  the sum of the regional `Count` must equal n, and the list of regions must equal the `Mechanism` column.

Details, the file list of the CSV output and the known limitations are in `results/summary/README_summary.md`.
