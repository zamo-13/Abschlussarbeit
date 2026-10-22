# Content moderation by TikTok and X in the DSA Transparency Database, 2025

This repository turns the European Commission's DSA Transparency Database daily dumps for TikTok
and X (2025) into the tables in `results/` and the figures in `results/figures/` used in my
bachelor's thesis. The data is processed in three layers with DuckDB:
- Bronze: the converted daily dumps, read in place.
- Silver: scoped to Germany and content posted in 2025, cleaned and deduplicated, written once as
  parquet.
- Gold: views over Silver, aggregated into small tables that are saved as CSV.

Everything below can be reproduced from this repository and the public database.

| File / folder | Content |
|---|---|
| `config.py` | Paths (`DATA_ROOT`), constants and the shared DuckDB connection |
| `build_silver.py` | Writes the Silver layer (scope, implausible dates, deduplication, derived attributes) |
| `01_bronze.ipynb` | Completeness of the downloaded dumps, Bronze views, profiling of the raw data |
| `02_silver.ipynb` | Scope rules, the schema change of 1 July 2025, cleaning decisions, Silver build and checks |
| `03_gold.ipynb` | Gold views, measure classification, all result tables with a short description of each |
| `04_figures.ipynb` | Figures 1–5, drawn only from the CSV files in `results/` |
| `results/` | 29 result tables (CSV) and `README.md` with title and denominator of each |
| `results/figures/` | 5 figures, each as PNG (300 dpi) and SVG |
| `dsa-tdb/` | `parameters_tiktok.yaml`, `parameters_x.yaml`: the settings of the original dsa-tdb run |
| `input_manifest.csv` | File name, size and SHA-1 of all 730 raw daily dumps used |
| `requirements.txt` | Pinned Python packages |
| `notes/` | My working notes on method choices and results |
| `NULL_columns.txt` | Early note on empty columns; not used by the code |

## 1. Requirements

- **Python 3.12.** Tested with 3.12.10 on Windows 11.
- **RAM:** about 16 GB. DuckDB is limited to 10 GB in `config.py`.
- **Docker**, for the Commission's `dsa-tdb` tool (download and conversion of the dumps).
- **Disk** on the data drive, as measured:

  | What | Size |
  |---|---|
  | Raw zips, TikTok + X, 2025 | 67.77 GB |
  | Converted parquet chunks | 55.29 GB |
  | Silver layer | 28.71 GB |
  | DuckDB temporary files during the Silver build | about 57 GB at peak (capped at 300 GiB in `build_silver.py`) |

  Plan for at least 220 GB of free space.

- **Runtime.** Full run from the converted chunks to the figures, on a laptop (Intel Core i7-10510U,
  16 GB RAM) with the data on an external USB drive:

  | Step | Runtime |
  |---|---:|
  | `01_bronze` | 1,184 s |
  | `02_silver`, including the Silver build | 18,319 s |
  | of which the Silver build, TikTok | 15,379 s |
  | of which the Silver build, X | 6 s |
  | `03_gold` | 1,066 s |
  | `04_figures` | 25 s |
  | **Total** | **20,594 s (about 5.7 h)** |

  An earlier full run on the same machine took 23,484 s. Download and conversion of the raw dumps
  are not included.

## 2. Setup

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt        # Windows
.venv/bin/python -m pip install -r requirements.txt            # Linux / macOS
```

`requirements.txt` is complete: a new environment installed from it alone runs the whole pipeline.
`ipywidgets` is required even though no notebook imports it. Without it, DuckDB refuses
`SET enable_progress_bar` inside a Jupyter kernel, and the first cell of every notebook fails.

## 3. Getting the data

### 3.1 Tool and settings

The dumps were downloaded and converted with the Commission's tool
[`dsa-tdb`](https://code.europa.eu/dsa/transparency-database/dsa-tdb), version **0.7.2**, run as its
Docker image:

```
code.europa.eu:4567/dsa/transparency-database/dsa-tdb:latest
image ID / digest: sha256:5a127832c6cd723f259a2c270243cddd4209e0c6ea5cd7d7c914d303d07a61f7
```

The `:latest` tag has moved on since. Use the digest to get the same version.

The original run used the tool's web app (`prepare` task). It writes its settings to
`parameters.yaml`; both files are in `dsa-tdb/`. The settings:
- platforms `tiktok` and `x`, one run each;
- daily dumps, version `full`, from 2025-01-01 to 2025-12-31;
- SHA-1 check on, raise on error;
- parquet chunks of 1,000,000 rows;
- original zips kept, one process.

The same settings on the command line (with `<DATA_ROOT>` mounted as `/data`, once per platform):

```
docker run --rm -v <DATA_ROOT>:/data --entrypoint /home/user/.venv/bin/dsa-tdb-cli <image> \
  preprocess -o /data -v full -p <platform> -i 2025-01-01 -f 2025-12-31 -n 1 \
  --chunk_size 1000000 --format parquet --override_chunked_subfolder daily_dumps_chunked --loglevel INFO
```

`--loglevel` needs a level name: `INFO` is the `loglevel: 20` of `parameters.yaml`.

Result: `<DATA_ROOT>/<platform>___full/` holds the zips, their `.sha1` files and
`daily_dumps_chunked/sor-<platform>-<date>-full/`. Each of those folders holds the parquet chunks
and a `COMPLETE` marker.

### 3.2 Known problem: the download step of dsa-tdb 0.7.2 fails against the current website

As of October 2026, three changes on the Commission's website break the download step of dsa-tdb
0.7.2. The conversion step still works.

1. **Rate limit.** The download page allows 20 requests per window. The tool pages through the whole
   list of daily files without pausing and stops with HTTP 429.
2. **Column name.** The list column is now called `Statements of reasons`; the tool looks for
   `Statements of Reasons` and fails with a KeyError.
3. **Link format.** Download links now point to `…/explore-data/download-file/<id>/full` and redirect
   to the Commission's S3 bucket. The tool derives the `.sha1` link from the old link format, finds
   no checksum, and stops with KeyError `web_sha1_chunk_check`.

**Workaround: download the files yourself, then convert them with dsa-tdb's own functions.**

1. Download, for each platform `p` in `tiktok`, `x` and each date `d` from 2025-01-01 to 2025-12-31,
   both files into `<DATA_ROOT>/<p>___full/`:

   ```
   https://dsa-sor-data-dumps.s3.eu-central-1.amazonaws.com/sor-<p>-<d>-full.zip
   https://dsa-sor-data-dumps.s3.eu-central-1.amazonaws.com/sor-<p>-<d>-full.zip.sha1
   ```

2. Save this script as `convert.py` in a folder of its own, for example `<TOOLS>`. It checks the
   SHA-1 and converts with the same call and settings that `preprocess` uses internally (dsa-tdb
   0.7.2, `fetch.py`). It also writes the `COMPLETE` marker.

   ```python
   from datetime import date, timedelta
   from pathlib import Path
   from dsa_tdb.fetch import chunkFile, check_sha1_sum
   from dsa_tdb.types import DAILY_FILE_EXTENSION

   for p in ("tiktok", "x"):
       d = date(2025, 1, 1)
       while d <= date(2025, 12, 31):
           z = Path(f"/data/{p}___full/sor-{p}-{d}-full.zip")
           check_sha1_sum(str(z), str(z) + ".sha1")   # raises on a mismatch
           chunkFile(csv_zip_in=z, folder_out=f"/data/{p}___full/daily_dumps_chunked",
                     platforms_to_exclude=None, header_in=True, header_out=True, chunk_size=1000000,
                     overwrite=True, extension=DAILY_FILE_EXTENSION, out_format="parquet",
                     delete_original=False)
           d += timedelta(days=1)
   ```

3. Run it in the original image:

   ```
   docker run --rm -v <DATA_ROOT>:/data -v <TOOLS>:/tools:ro \
     --entrypoint /home/user/.venv/bin/python <image> /tools/convert.py
   ```

This route was tested on three days per platform (2025-01-15, 2025-03-10, 2025-06-10). The
downloaded zips had the same SHA-1 as the original ones, and the converted chunks were identical
in rows and values.

### 3.3 Check the downloads

`input_manifest.csv` lists every zip used, with its size and SHA-1. Compare your files with it:

```python
import csv, hashlib
from pathlib import Path

DATA_ROOT = Path("E:/dsa-data")          # your data folder
bad = []
for r in csv.DictReader(open("input_manifest.csv")):
    f = DATA_ROOT / f"{r['platform']}___full" / r["file"]
    h = hashlib.sha1()
    with open(f, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    if f.stat().st_size != int(r["size_bytes"]) or h.hexdigest() != r["sha1"]:
        bad.append(r["file"])
print(len(bad), "files differ", bad[:10])
```

On the original data all 730 files match, both the manifest and the `.sha1` files published with
the dumps. Hashing all 67.77 GB took 3,266 s.

## 4. Configuration

Set `DATA_ROOT` in `config.py` to the folder that contains `tiktok___full/` and `x___full/`, for
example `DATA_ROOT = Path("E:/dsa-data")`. Everything else is derived from it:

| Path | Written by | Content |
|---|---|---|
| `<DATA_ROOT>/dsa.duckdb` | all notebooks | DuckDB catalog; views only, no data |
| `<DATA_ROOT>/silver/` | `build_silver.py` | Silver parquet, `platform=<TikTok/X>/month=<YYYY-MM-01>/` |
| `<DATA_ROOT>/silver_meta/` | `build_silver.py` | cached lists of duplicated identifiers |
| `<DATA_ROOT>/_duckdb_tmp/` | DuckDB | temporary files; empty after a successful run |
| `results/`, `results/figures/` (in the repository) | `03_gold`, `04_figures` | result tables and figures |

The DuckDB views store absolute paths. If you move the data folder, run the notebooks again.

## 5. Run order

Run from the repository root, each notebook in a fresh kernel:

```
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 01_bronze.ipynb
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 02_silver.ipynb
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 03_gold.ipynb
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 04_figures.ipynb
```

| Step | Produces |
|---|---|
| `01_bronze` | Checks the 365 days per platform. Registers the Bronze views over the parquet chunks and profiles the raw data. |
| `02_silver` | Applies the scope (Germany in the territorial scope, content posted in 2025) and documents the schema change of 1 July 2025. Builds Silver by calling `build_silver.py`, which takes most of the runtime. Checks the result and defines the analysis set: content posted from 2025-01-01 to 2025-06-30 and submitted before 2025-07-01, when the submission schema changed. |
| `03_gold` | Defines the Gold views. Writes the 29 CSV files in `results/`. |
| `04_figures` | Writes the 5 figures in `results/figures/`. |

`02_silver` builds Silver only when `<DATA_ROOT>/silver/` contains no parquet files. The build can
also be run on its own: `python build_silver.py x` and `python build_silver.py tiktok`. An optional
second argument sets the output folder.

**Always build into an empty folder.** The deduplicated rows are appended, so building again into a
folder that already holds Silver files counts those rows twice. To rebuild, delete or rename the old
folder first, or pass a new folder as the second argument.

## 6. What to expect

Row counts at each step, as printed by `02_silver` §5.1 and §6:

| Step | TikTok | X |
|---|---:|---:|
| Bronze (all rows of 2025) | 1,002,729,268 | 670,093 |
| Germany in the territorial scope, content posted in 2025 | 979,896,444 | 183,321 |
| removed: application date before content date | 2,499 | 0 |
| removed: duplicate submissions | 337,745 | 0 |
| **Silver** | **979,556,200** | **183,321** |
| removed: content posted from 2025-07-01 | 155,327,533 | 51,130 |
| removed: submitted from 2025-07-01 (new submission schema) | 7,782,575 | 42 |
| **Analysis set** (content posted 2025-01-01 to 2025-06-30, submitted before 2025-07-01) | **816,446,092** | **132,149** |

- **Deduplication is deterministic.** Each statement keeps exactly one row: the earliest submission
  (`created_at`), with ties broken by `uuid` and then by source file. A rebuild therefore gives the
  same Silver layer row for row.
- **Results.** `results/` holds 29 tables and 5 figures. A rebuild should reproduce every table
  value for value, and every figure: the PNGs byte for byte, the SVGs apart from metadata and the
  random element ids that matplotlib writes.
- **Printed output.** Apart from runtimes, it can differ in a few places:
  - the list of views already in the catalog (`02_silver`);
  - compressed column sizes and the order of tied rows (`02_silver` §5.3);
  - a one-time font-cache message from matplotlib.

This was verified in two independent re-runs from a fresh copy of the repository. The last re-run,
with the current code, rebuilt Silver from the converted chunks: identical to the Silver layer used for
the analysis in every row and attribute, and all 29 tables and 5 figures identical.
