"""Minimal Streamlit app to showcase cleaned data and cross-country comparison.

Run with: streamlit run scripts/streamlit_app.py

The app loads cleaned CSVs from `data/` if present and uses `src.compare`
to produce a compact summary table. This is a lightweight demo to satisfy the
feedback asking for dashboard/artifacts.
"""
from pathlib import Path
import streamlit as st
import pandas as pd

from src.compare import compare_countries


st.set_page_config(page_title="Solar Challenge — Comparison", layout="wide")

st.title("Solar data — quick compare")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

st.sidebar.header("Data selection")
available = list(DATA_DIR.glob("*_clean.csv"))
if not available:
    st.sidebar.warning("No cleaned CSVs found in data/ — run cleaning first or place sample files there.")

selected = st.sidebar.multiselect("Select cleaned country files", [p.name for p in available], default=[p.name for p in available])

dfs = {}
for name in selected:
    p = DATA_DIR / name
    try:
        df = pd.read_csv(p, parse_dates=["Timestamp"]) if p.exists() else pd.DataFrame()
        # ensure Timestamp index for compare
        if not df.empty:
            df = df.set_index("Timestamp")
        country = name.replace("_clean.csv", "")
        dfs[country] = df
    except Exception as e:
        st.error(f"Failed to load {name}: {e}")

if dfs:
    summary = compare_countries(dfs)
    st.header("Cross-country summary")
    st.dataframe(summary)
else:
    st.info("No datasets selected or available.")
