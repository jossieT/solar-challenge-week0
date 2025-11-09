"""Data cleaning utilities.

This module provides a small, reusable DataCleaner class that
encapsulates common cleaning steps used in notebooks (timestamp parsing,
dtype enforcement, clipping invalid values, simple gap imputation, and export).

Public interface
----------------
- DataCleaner: primary class to load and clean a dataset programmatically.
- quick_clean(path, out_path=None): convenience function for scripts.
- clean_path(path, out_path=None): explicit simple entrypoint for external callers.

Example
-------
from src.cleaning import clean_path
clean_path("data/benin-malanville.csv", out_path="data/benin_clean.csv")
"""
from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np

__all__ = ["DataCleaner", "quick_clean", "clean_path"]


class DataCleaner:
    """Simple data cleaner for solar resource CSV files.

    The class is intentionally small and demonstrates object-oriented
    packaging of repeated notebook logic. Methods are chainable where
    appropriate and include basic inline comments and docstrings.

    Parameters
    ----------
    path: str | None
        Optional path to CSV file. If None, `load` should be given a DataFrame.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.df: pd.DataFrame | None = None

    def load(self, path: Optional[str] = None) -> pd.DataFrame:
        """Load CSV into a DataFrame. If path passed, update self.path."""
        p = path or self.path
        if p is None:
            raise ValueError("No path provided to load data")
        self.df = pd.read_csv(p)
        return self.df

    def set_index_timestamp(self, ts_col: str = "Timestamp") -> pd.DataFrame:
        """Parse `ts_col` to datetime, drop duplicates, sort, and set as index."""
        assert self.df is not None, "Data not loaded"
        # coerce errors to NaT so later checks can reveal parsing problems
        self.df[ts_col] = pd.to_datetime(self.df[ts_col], errors="coerce")
        # drop duplicates on timestamp and sort chronologically
        self.df = self.df.drop_duplicates(subset=ts_col).sort_values(ts_col)
        self.df = self.df.set_index(ts_col)
        return self.df

    def enforce_dtypes(self, float_cols: Optional[list[str]] = None) -> pd.DataFrame:
        """Cast numeric columns to floats and ensure Cleaning flag is integer/boolean."""
        assert self.df is not None, "Data not loaded"
        if float_cols is None:
            # subset commonly used numeric columns; presence is dataset-dependent
            float_cols = [
                "GHI",
                "DNI",
                "DHI",
                "ModA",
                "ModB",
                "Tamb",
                "RH",
                "WS",
                "WSgust",
                "WSstdev",
                "WD",
                "WDstdev",
                "BP",
                "Precipitation",
                "TModA",
                "TModB",
            ]
        for c in float_cols:
            if c in self.df.columns:
                # use to_numeric to coerce bad strings to NaN
                self.df[c] = pd.to_numeric(self.df[c], errors="coerce").astype(float)
        # cleaning flag normalization
        if "Cleaning" in self.df.columns:
            # convert to integer 0/1 where possible
            self.df["Cleaning"] = self.df["Cleaning"].apply(
                lambda x: 1 if (x == 1 or str(x).strip() == "1") else 0
            ).astype("Int64")
        return self.df

    def basic_clipping_impute(self) -> pd.DataFrame:
        """Apply sensible clipping for environmental ranges and simple imputation."""
        assert self.df is not None, "Data not loaded"
        # clip negative irradiance to zero
        for col in ["GHI", "DNI", "DHI", "ModA", "ModB"]:
            if col in self.df.columns:
                self.df[col] = self.df[col].clip(lower=0)

        # humidity must be 0-100
        if "RH" in self.df.columns:
            self.df["RH"] = self.df["RH"].clip(0, 100)

        # normalize wind direction into [0,360)
        if "WD" in self.df.columns:
            self.df["WD"] = self.df["WD"].apply(lambda x: x % 360 if pd.notnull(x) else x)

        # simple median imputation for remaining numeric NaNs
        numeric = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric:
            medians = self.df[numeric].median()
            # fill only numeric columns
            self.df[numeric] = self.df[numeric].fillna(medians)

        return self.df

    def interpolate_short_gaps(self, limit: int = 3) -> pd.DataFrame:
        """Interpolate short gaps (limit steps) for numeric columns using time index."""
        assert self.df is not None, "Data not loaded"
        numeric = self.df.select_dtypes(include=[np.number]).columns.tolist()
        # interpolate only if index is datetime-like
        if not pd.api.types.is_datetime64_any_dtype(self.df.index):
            return self.df
        self.df[numeric] = self.df[numeric].interpolate(method="time", limit=limit)
        return self.df

    def drop_bad_rows(self, max_na_frac: float = 0.5) -> pd.DataFrame:
        """Drop rows with too many missing values (fraction threshold)."""
        assert self.df is not None, "Data not loaded"
        keep = self.df.isna().mean(axis=1) <= max_na_frac
        self.df = self.df.loc[keep]
        return self.df

    def export(self, out_path: str) -> None:
        """Export the cleaned DataFrame to CSV."""
        assert self.df is not None, "Data not loaded"
        self.df.to_csv(out_path, index=True)

    def run(self, path: Optional[str] = None, out_path: Optional[str] = None) -> pd.DataFrame:
        """High-level convenience method to run standard cleaning steps.

        If `out_path` is provided the cleaned CSV will be written to disk.
        """
        if path is not None:
            self.load(path)
        self.set_index_timestamp()
        self.enforce_dtypes()
        self.basic_clipping_impute()
        self.interpolate_short_gaps()
        self.drop_bad_rows()
        if out_path is not None:
            self.export(out_path)
        return self.df


def quick_clean(path: str, out_path: Optional[str] = None) -> pd.DataFrame:
    """Functional convenience wrapper around DataCleaner for quick scripts/notebooks."""
    dc = DataCleaner(path)
    return dc.run(out_path=out_path)


def clean_path(path: str, out_path: Optional[str] = None) -> pd.DataFrame:
    """Alias for external callers: clean a CSV at `path` and optionally write out.

    This function is a stable, small public entrypoint suitable for CI checks or
    simple scripts that need to run the full cleaning pipeline.
    """
    return quick_clean(path, out_path=out_path)
