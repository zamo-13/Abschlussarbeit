"""Build the Silver layer: scope -> deduplicate -> clean -> derive -> write parquet.

Run as a script because the TikTok write takes hours:

    python build_silver.py x      [out_root]   # seconds
    python build_silver.py tiktok [out_root]   # ~2.3 h with cached duplicate sets, ~4.7 h without

out_root defaults to config.SILVER_ROOT; pass a new folder to rebuild without touching the old one.

Design notes
------------
* Source is ``silver.scoped_<platform>`` (whole year, DE + content posted 2025). The v1
  analysis layer is a *view* over the written parquet, so the data is written once.
* Partitioned by ``platform`` and ``month`` (derived from ``content_date``). Partitions
  are NOT sorted by ``application_date``: the dumps arrive in submission order, so unsorted row
  groups already span ~1.1 days of ``application_date`` (0.4 when sorted), and a sort costs
  ~2.6 h per partition for ~20% on cold full scans and no gain on windowed queries
  (measured 2026-10-03).
* Deduplication is global across the whole period. A window function over all
  ~980M wide rows would spill tens of GB, so the duplicate identifiers are collected in two
  narrow passes first; only the affected rows then pass through the window. Those two passes
  cost ~2.7 h on TikTok, so their result is cached under ``silver_meta`` and reused on a retry.
  Duplicates are resolved sequentially with one total order (created_at, uuid, source_file,
  platform_uid): first one row per platform_uid, then one row per uuid among those survivors.
  A rebuild therefore always keeps the same row, and no statement loses all its rows. (Until
  2026-10-20 the two windows were combined with AND and broke ties independently, which dropped
  383 statements entirely.)
* JSON array attributes are parsed to native lists but NOT unnested: one Silver row
  stays one statement of reasons.
"""
import sys
import time
from pathlib import Path

from config import DATA_ROOT, SILVER_ROOT, connect

LIST_COLS = ["decision_visibility", "content_type", "category_specification",
             "category_addition", "territorial_scope"]

# The 14 attributes populated in every row (mandatory under the Commission schema).
MANDATORY = ["uuid", "platform_uid", "platform_name", "content_date", "application_date",
             "created_at", "territorial_scope", "decision_ground", "category", "content_type",
             "decision_facts", "automated_detection", "automated_decision", "source_type"]

# n_filled_optional_fields: the 23 remaining source attributes.
OPTIONAL = ["decision_visibility", "decision_visibility_other", "end_date_visibility_restriction",
            "decision_monetary", "decision_monetary_other", "end_date_monetary_restriction",
            "decision_provision", "end_date_service_restriction", "decision_account",
            "end_date_account_restriction", "account_type", "decision_ground_reference_url",
            "illegal_content_legal_ground", "illegal_content_explanation",
            "incompatible_content_ground", "incompatible_content_explanation",
            "incompatible_content_illegal", "category_addition", "category_specification",
            "category_specification_other", "content_type_other", "content_language",
            "source_identity"]

# n_filled_strictly_optional: OPTIONAL minus the conditionally required attributes, whose
# presence follows from decision_ground and would make X look more granular merely because it
# uses the illegal-content ground. ``content_language_other`` is named in the specification of
# this counter but does not exist in the schema; ``category_specification_other`` is a
# borderline case (conditional on category_specification = KEYWORD_OTHER) and was kept, as the
# instruction listed only the decision_*_other fields and content_type_other.
CONDITIONALLY_REQUIRED = ["decision_visibility_other", "decision_monetary_other",
                          "illegal_content_legal_ground", "illegal_content_explanation",
                          "incompatible_content_ground", "incompatible_content_explanation",
                          "content_type_other"]
STRICTLY_OPTIONAL = [c for c in OPTIONAL if c not in CONDITIONALLY_REQUIRED]

EU27 = ["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU",
        "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"]
# EEA = EU27 + LI + NO, with or without IS (verified 2026-10-02: the 29- and 30-country lists
# differ only in IS; Papaevangelou & Votta 2025, fn. 5).
EEA_EXTRA = ["LI", "NO", "IS"]


def parsed(col: str) -> str:
    return f"""from_json({col}, '["VARCHAR"]') AS {col}"""


def select_clause() -> str:
    """Source attributes (lists parsed in place) plus the derived attributes."""
    eu27 = ", ".join(f"'{c}'" for c in EU27)
    eea = ", ".join(f"'{c}'" for c in EU27 + EEA_EXTRA)
    opt = " + ".join(f"({c} IS NOT NULL)::INT" for c in OPTIONAL)
    strict = " + ".join(f"({c} IS NOT NULL)::INT" for c in STRICTLY_OPTIONAL)
    return f"""
        * EXCLUDE ({', '.join(LIST_COLS + ['n_countries_in_scope'])}),
        {', '.join(parsed(c) for c in LIST_COLS)},
        CASE WHEN platform_name ILIKE 'X%' THEN 'X' ELSE platform_name END AS platform,
        date_trunc('month', content_date)::DATE AS month,
        len(from_json(territorial_scope, '["VARCHAR"]')) AS n_countries_in_scope,
        date_diff('day', content_date, application_date) AS application_delay,
        date_diff('day', application_date, created_at::DATE) AS communication_delay,
        {opt} AS n_filled_optional_fields,
        {strict} AS n_filled_strictly_optional,
        CASE
            WHEN len(from_json(territorial_scope, '["VARCHAR"]')) = 1 THEN 'single_country'
            WHEN list_sort(from_json(territorial_scope, '["VARCHAR"]'))
                 = list_sort([{eu27}]) THEN 'eu'
            WHEN list_has_all([{eea}], from_json(territorial_scope, '["VARCHAR"]'))
                 AND list_has_all(from_json(territorial_scope, '["VARCHAR"]'), [{eu27}])
                 THEN 'eea'
            ELSE 'other'
        END AS scope_class
    """


def dup_set(con, platform: str, src: str, key: str) -> int:
    """Duplicate identifiers for `key`, cached as parquet — the pass costs ~1 h per key on TikTok."""
    meta = DATA_ROOT / "silver_meta"
    meta.mkdir(exist_ok=True)
    path = (meta / f"{platform}_dup_{key}.parquet").as_posix()
    t = time.time()
    if Path(path).exists():
        con.execute(f"CREATE OR REPLACE TEMP VIEW dup_{key} AS SELECT * FROM read_parquet('{path}')")
        n = con.sql(f"SELECT count(*) FROM dup_{key}").fetchone()[0]
        print(f"[{platform}] duplicate {key}s: {n:,}  (cached)", flush=True)
        return n
    con.execute(f"""COPY (SELECT {key} FROM {src} GROUP BY 1 HAVING count(*) > 1)
                    TO '{path}' (FORMAT PARQUET)""")
    con.execute(f"CREATE OR REPLACE TEMP VIEW dup_{key} AS SELECT * FROM read_parquet('{path}')")
    n = con.sql(f"SELECT count(*) FROM dup_{key}").fetchone()[0]
    print(f"[{platform}] duplicate {key}s: {n:,}  ({time.time()-t:.0f}s)", flush=True)
    return n


def build(platform: str, out_root: Path = SILVER_ROOT) -> None:
    con = connect()
    con.execute("SET preserve_insertion_order = false")   # no global ordering during the write
    con.execute("SET max_temp_directory_size = '300GiB'") # fail fast instead of filling the disk
    con.execute("SET threads = 6")
    src = f"silver.scoped_{platform}"
    out = Path(out_root).as_posix()
    t0 = time.time()

    rows_in = con.sql(f"SELECT count(*) FROM {src}").fetchone()[0]
    print(f"[{platform}] scoped rows: {rows_in:,}  ({time.time()-t0:.0f}s)", flush=True)

    n_puid = dup_set(con, platform, src, "platform_uid")
    n_uuid = dup_set(con, platform, src, "uuid")

    # Two separate COPY statements on purpose. Putting both branches in one query means the
    # shared CTE is referenced twice, which makes DuckDB materialise all ~980M wide rows to the
    # scratch directory (~300 GB, aborted on 2026-10-03). Each statement below is a single scan.
    not_dup = """platform_uid NOT IN (SELECT platform_uid FROM dup_platform_uid)
                 AND uuid NOT IN (SELECT uuid FROM dup_uuid)"""
    is_dup = """platform_uid IN (SELECT platform_uid FROM dup_platform_uid)
                OR uuid IN (SELECT uuid FROM dup_uuid)"""
    plausible = """(application_date IS NULL OR content_date IS NULL
                    OR application_date >= content_date)"""          # implausible records

    t = time.time()
    con.execute(f"""
        COPY (
            SELECT {select_clause()} FROM {src}
            WHERE {plausible} AND {not_dup}
        ) TO '{out}' (
            FORMAT PARQUET, COMPRESSION ZSTD,
            PARTITION_BY (platform, month),
            OVERWRITE_OR_IGNORE, FILENAME_PATTERN '{platform}_clean_{{i}}'
        )""")
    print(f"[{platform}] clean rows written  ({time.time()-t:.0f}s)", flush=True)

    # One row per statement, deterministic. Sequential, not an AND of two windows.
    order = "created_at, uuid, source_file, platform_uid"
    t = time.time()
    con.execute(f"""
        COPY (
            SELECT * FROM (
                SELECT * FROM (
                    SELECT {select_clause()} FROM {src}
                    WHERE {plausible} AND ({is_dup})
                )
                QUALIFY row_number() OVER (PARTITION BY platform_uid ORDER BY {order}) = 1
            )
            QUALIFY row_number() OVER (PARTITION BY uuid ORDER BY {order}) = 1
        ) TO '{out}' (
            FORMAT PARQUET, COMPRESSION ZSTD,
            PARTITION_BY (platform, month),
            APPEND, FILENAME_PATTERN '{platform}_dedup_{{uuid}}'
        )""")
    print(f"[{platform}] deduplicated rows written  ({time.time()-t:.0f}s)", flush=True)

    rows_out = con.sql(
        f"SELECT count(*) FROM read_parquet('{out}/platform=*/month=*/{platform}_*.parquet')"
    ).fetchone()[0]
    print(f"[{platform}] silver rows: {rows_out:,}  (removed {rows_in - rows_out:,})", flush=True)
    print(f"[{platform}] total {time.time()-t0:.0f}s", flush=True)
    con.close()


if __name__ == "__main__":
    build(sys.argv[1], *(sys.argv[2:3]))
