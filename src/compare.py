"""Comparison utilities for cross-country synthesis.

This module provides helpers to compute summary metrics across multiple
country datasets (e.g., mean GHI, median WS) and produce a compact comparison
DataFrame that can be saved or used by notebooks/dashboards.

Public API
----------
- compare_countries(dfs): main function to compute per-country summary metrics.
- summarize_countries: alias for compare_countries (stable public name).
"""
from __future__ import annotations

from typing import Dict
import pandas as pd

__all__ = ["compare_countries", "summarize_countries"]


def compare_countries(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compute cross-country summary statistics.

    Parameters
    ----------
    dfs: dict[str, pd.DataFrame]
        Mapping from country name to cleaned DataFrame (index should be Timestamp).

    Returns
    -------
    pd.DataFrame
        Summary table with per-country metrics. Index is `country` and columns
        include `ghi_mean`, `ghi_median`, `ws_mean`, `precip_mean`, `observations`.
    """
    if not isinstance(dfs, dict):
        raise TypeError("dfs must be a dict mapping country->DataFrame")

    rows = []
    for name, df in dfs.items():
        if not hasattr(df, "columns"):
            raise TypeError(f"Value for '{name}' is not a DataFrame-like object")
        # pick metrics that are useful for solar siting
        ghi_mean = float(df["GHI"].mean()) if "GHI" in df.columns else float("nan")
        ghi_median = float(df["GHI"].median()) if "GHI" in df.columns else float("nan")
        ws_mean = float(df["WS"].mean()) if "WS" in df.columns else float("nan")
        precip_mean = float(df["Precipitation"].mean()) if "Precipitation" in df.columns else float("nan")
        rows.append(
            {
                "country": name,
                "ghi_mean": ghi_mean,
                "ghi_median": ghi_median,
                "ws_mean": ws_mean,
                "precip_mean": precip_mean,
                "observations": int(len(df)),
            }
        )
    return pd.DataFrame(rows).set_index("country")


def summarize_countries(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Stable alias for compare_countries kept for backward compatibility.

    This name is more explicit about the function's role in producing a
    synthesis/summarization artifact for cross-country comparison.
    """
    return compare_countries(dfs)
