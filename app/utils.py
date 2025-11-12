"""
Utility functions for the Streamlit solar dashboard.

Contains:
- upload parsing and preprocessing
- filtering helpers
- plotting helpers (Plotly)
- summary statistics, top-regions extraction
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import io

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Columns we expect commonly in solar datasets (non-exhaustive)
COMMON_METRICS = ["GHI", "DNI", "DHI"]
TIMESTAMP_COLS = ["Timestamp", "timestamp", "Datetime", "datetime", "time"]


def _parse_timestamp_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect and parse a timestamp column into a DatetimeIndex if possible.
    """
    for col in TIMESTAMP_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.set_index(col)
            return df
    return df


@st.cache_data
def load_uploaded_csv(file_like: io.BytesIO, country_name: str) -> pd.DataFrame:
    """
    Read a CSV uploaded via Streamlit and return a cleaned DataFrame.

    Parameters
    ----------
    file_like : file-like
        The uploaded file-like object from Streamlit.
    country_name : str
        Country label to add as a 'Country' column.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with parsed timestamp (if present).
    """
    try:
        df = pd.read_csv(file_like)
    except Exception as exc:
        raise ValueError(f"Could not read CSV for {country_name}: {exc}")

    df = df.copy()
    # parse timestamp if present and set it as index
    df = _parse_timestamp_column(df)

    # normalize numeric columns: coerce metrics to numeric
    for m in COMMON_METRICS:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce")

    # ensure Region column exists (may be missing)
    if "Region" not in df.columns:
        df["Region"] = np.nan

    df["Country"] = country_name
    return df


def get_datasets_date_bounds(datasets: Dict[str, pd.DataFrame]) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Return (min_date, max_date) across all provided datasets. Uses index if datetime.
    """
    mins, maxs = [], []
    for df in datasets.values():
        if isinstance(df.index, pd.DatetimeIndex) and not df.index.empty:
            mins.append(df.index.min())
            maxs.append(df.index.max())
    if not mins:
        today = pd.Timestamp.now().normalize().date()
        return (today, today)
    return (min(mins).date(), max(maxs).date())


def filter_datasets(datasets: Dict[str, pd.DataFrame], selected_countries: List[str], date_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]]) -> Dict[str, pd.DataFrame]:
    """
    Return a filtered copy of the datasets mapping: only selected_countries and date_range applied.
    date_range is (start_date, end_date) as date objects or timestamps; if None, no date filter.
    """
    out = {}
    for country, df in datasets.items():
        if selected_countries and country not in selected_countries:
            continue
        tmp = df.copy()
        if date_range and isinstance(tmp.index, pd.DatetimeIndex):
            start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            tmp = tmp.loc[(tmp.index >= start) & (tmp.index <= end)]
        out[country] = tmp
    return out


def compute_global_kpis(datasets: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """
    Compute simple global KPIs across all provided datasets: mean GHI, DNI, DHI.
    """
    vals = {"GHI": [], "DNI": [], "DHI": []}
    for df in datasets.values():
        for m in vals.keys():
            if m in df.columns:
                vals[m].append(df[m].dropna())
    out = {}
    for m, lists in vals.items():
        if lists:
            out[f"{m}_mean"] = float(pd.concat(lists).mean())
        else:
            out[f"{m}_mean"] = float("nan")
    return {"GHI_mean": out["GHI_mean"], "DNI_mean": out["DNI_mean"], "DHI_mean": out["DHI_mean"]}


def compute_per_country_mean(datasets: Dict[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    """
    Compute per-country mean for a selected metric and return a tidy DataFrame.
    """
    rows = []
    for country, df in datasets.items():
        if metric in df.columns:
            rows.append({"country": country, "mean": float(df[metric].dropna().mean())})
    return pd.DataFrame(rows).set_index("country")


def plot_line_metric(datasets: Dict[str, pd.DataFrame], metric: str) -> px.line:
    """
    Create a line chart (Plotly) of `metric` over time across datasets.

    Assumes each DataFrame has a DatetimeIndex or a Timestamp-like column parsed.
    """
    pieces = []
    for country, df in datasets.items():
        if metric in df.columns:
            tmp = df[[metric]].dropna().reset_index()
            tmp["Country"] = country
            pieces.append(tmp)
    if not pieces:
        return px.line(title=f"No data for {metric}")
    df_plot = pd.concat(pieces)
    fig = px.line(df_plot, x=df_plot.columns[0], y=metric, color="Country", labels={df_plot.columns[0]: "Timestamp"})
    fig.update_layout(template="plotly_dark", title=f"{metric} over time")
    return fig


def plot_box_metric(datasets: Dict[str, pd.DataFrame], metric: str) -> px.box:
    """
    Create a boxplot comparing `metric` distributions across countries.
    """
    pieces = []
    for country, df in datasets.items():
        if metric in df.columns:
            tmp = df[[metric]].dropna().copy()
            tmp["Country"] = country
            pieces.append(tmp)
    if not pieces:
        return px.box(title=f"No data for {metric}")
    plot_df = pd.concat(pieces)
    fig = px.box(plot_df, x="Country", y=metric, points="outliers", title=f"{metric} distribution by country", color="Country")
    fig.update_layout(template="plotly_dark")
    return fig


def plot_bar_metric(datasets: Dict[str, pd.DataFrame], metric: str) -> px.bar:
    """
    Create a bar chart of average `metric` per country.
    """
    rows = []
    for country, df in datasets.items():
        if metric in df.columns:
            rows.append({"Country": country, "mean": float(df[metric].dropna().mean())})
    if not rows:
        return px.bar(title=f"No data for {metric}")
    dfm = pd.DataFrame(rows)
    fig = px.bar(dfm, x="Country", y="mean", color="Country", title=f"Average {metric} per country")
    fig.update_layout(template="plotly_dark", yaxis_title=f"Mean {metric}")
    return fig


def summary_statistics_table(datasets: Dict[str, pd.DataFrame], metrics: List[str]) -> pd.DataFrame:
    """
    Compute mean/median/std for each metric and each country, return a tidy DataFrame.
    """
    rows = []
    for country, df in datasets.items():
        for m in metrics:
            if m in df.columns:
                s = df[m].dropna()
                rows.append({"country": country, "metric": m, "mean": float(s.mean()), "median": float(s.median()), "std": float(s.std())})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).pivot(index="metric", columns="country", values=["mean", "median", "std"])


def top_regions_by_metric(datasets: Dict[str, pd.DataFrame], metric: str = "GHI", top_n: int = 10) -> pd.DataFrame:
    """
    Find top regions by mean of `metric`. Expects a 'Region' column in each DataFrame.
    Returns a DataFrame with columns [country, region, mean_metric] sorted desc.
    """
    rows = []
    for country, df in datasets.items():
        if metric in df.columns and "Region" in df.columns:
            grp = df.groupby("Region")[metric].mean().dropna()
            for region, mean_val in grp.items():
                rows.append({"country": country, "region": region, "mean_metric": float(mean_val)})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("mean_metric", ascending=False).head(top_n)
    return df.reset_index(drop=True)


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Utility: convert a DataFrame to bytes for st.download_button.
    """
    if df is None or df.empty:
        return b""
    return df.to_csv(index=True).encode("utf-8")


def country_with_highest_mean(datasets: Dict[str, pd.DataFrame], metric: str = "GHI") -> Tuple[Optional[str], float]:
    """
    Return (country, mean_value) of the country with highest mean for metric.
    """
    best = None
    best_val = -float("inf")
    for country, df in datasets.items():
        if metric in df.columns:
            val = float(df[metric].dropna().mean())
            if val > best_val:
                best_val = val
                best = country
    if best is None:
        return (None, float("nan"))
    return (best, best_val)