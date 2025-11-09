"""Comparison utilities for cross-country synthesis.

This module provides a small helper to compute summary metrics across multiple
country datasets (e.g., mean GHI, median WS) and produce a compact comparison
DataFrame that can be saved or used by notebooks/dashboards.
"""
from __future__ import annotations

from typing import Dict
import pandas as pd


def compare_countries(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compute cross-country summary statistics.

    Parameters
    ----------
    dfs: dict
        Mapping from country name to cleaned DataFrame (index must be Timestamp).

    Returns
    -------
    pd.DataFrame
        Summary table with per-country metrics.
    """
    rows = []
    for name, df in dfs.items():
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
                "observations": len(df),
            }
        )
    return pd.DataFrame(rows).set_index("country")
