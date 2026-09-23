"""Shared configuration for the data preparation notebooks.

Paths, constants and the DuckDB connection used by the bronze, silver and gold notebooks.
"""

from datetime import date
from pathlib import Path

import duckdb

DATA_ROOT = Path("E:/dsa-data")
DB_PATH = DATA_ROOT / "dsa.duckdb"  # persistent catalog of views/tables, shared by all notebooks
SILVER_ROOT = DATA_ROOT / "silver"

PLATFORMS = ["tiktok", "x"]
PERIOD = (date(2025, 1, 1), date(2025, 12, 31))

MEMORY_LIMIT = "10GB"


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open the shared DuckDB database with the settings used across the notebooks."""
    con = duckdb.connect(DB_PATH, read_only=read_only)
    con.execute(f"SET memory_limit = '{MEMORY_LIMIT}'")
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET temp_directory = '{(DATA_ROOT / '_duckdb_tmp').as_posix()}'")
    return con
