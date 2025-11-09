"""I/O helpers for the project.

This small module centralizes file read/write helpers so the rest of the code
can keep IO concerns minimal and easier to test.

Currently provides:
- read_clean_csv(path): read a CSV with sensible defaults and parse dates.
- list_cleaned_files(path_glob): convenience for listing cleaned CSVs.
"""
from __future__ import annotations

from typing import Iterable
import pathlib
import pandas as pd

__all__ = ["read_clean_csv", "list_cleaned_files"]


def read_clean_csv(path: str | pathlib.Path) -> pd.DataFrame:
    """Read a cleaned CSV produced by the pipeline.

    Parameters
    ----------
    path: str | Path
        Path to CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with parsed datetime index if a "timestamp" or "Datetime" column
        is present. Otherwise returns the raw DataFrame.
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")

    df = pd.read_csv(p)

    # common column names created by the cleaning pipeline
    for col in ("timestamp", "Timestamp", "Datetime"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.set_index(col)
            break

    return df


def list_cleaned_files(path_glob: str) -> Iterable[pathlib.Path]:
    """Yield paths matching a glob (e.g., "data/*_clean.csv").

    This helper is intentionally tiny so callers can mock it in tests.
    """
    return pathlib.Path().glob(path_glob)
