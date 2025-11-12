"""
Streamlit entrypoint for the Solar Dashboard.

Provides page navigation and page-level layout. Integrates with helpers in app.utils
and small UI components in app.components.

Pages:
- Home
- Visualizations
- Cross-Country Comparison
- Insights & Recommendations
"""
from __future__ import annotations
from typing import Dict, Optional, Tuple
from pathlib import Path
import io

import streamlit as st
import pandas as pd
import plotly.express as px

# Ensure the project root is on sys.path so `from app import ...` works when
# Streamlit runs this file as a script. This makes imports reliable whether
# the app is launched from the repository root or from the `app/` folder.
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import utils
from app import components

st.set_page_config(page_title="Solar Challenge — Dashboard", layout="wide")

# Simple nav
PAGES = ["Home", "Visualizations", "Cross-Country Comparison", "Insights & Recommendations"]


def load_uploaded_files() -> Dict[str, pd.DataFrame]:
    """
    Read uploaded files from three upload widgets on the Home page (if present).

    Uses `st.session_state` to persist loaded DataFrames across interaction.
    """
    # initialize map in session_state
    if "datasets" not in st.session_state:
        st.session_state["datasets"] = {}

    datasets: Dict[str, pd.DataFrame] = st.session_state["datasets"]

    # Uploaders on Home manage this; this helper just returns what is stored
    return datasets


def home_page() -> None:
    """
    Home page:
    - file uploaders for Benin, Sierra Leone, Togo
    - overview and dataset description
    - KPIs (average GHI/DNI/DHI)
    """
    st.title("📈 Solar Dashboard — Home")
    st.markdown(
        """
        Welcome to the Solar Dashboard template. Use the upload widgets below to provide
        CSVs for Benin, Sierra Leone and Togo. The app will parse timestamps and compute
        simple metrics (GHI, DNI, DHI) and render interactive visualizations on the
        Visualizations and Comparison pages.
        """
    )

    st.markdown("### Upload cleaned CSVs (Benin, Sierra Leone, Togo)")
    cols = st.columns(3)
    country_keys = [("Benin", "benin"), ("Sierra Leone", "sierraleone"), ("Togo", "togo")]

    # Keep files in session_state so other pages can read them without re-upload
    if "datasets" not in st.session_state:
        st.session_state["datasets"] = {}

    for (label, key), col in zip(country_keys, cols):
        with col:
            uploaded = st.file_uploader(f"{label} CSV", type=["csv"], key=f"upload_{key}")
            if uploaded is not None:
                try:
                    df = utils.load_uploaded_csv(uploaded, country_name=label)
                except Exception as exc:
                    st.error(f"Failed to parse {label} CSV: {exc}")
                    continue
                st.session_state["datasets"][label] = df
                st.success(f"{label} loaded ({len(df)} rows)")
            else:
                # allow showing a loaded dataset if already uploaded earlier
                if label in st.session_state["datasets"]:
                    existing = st.session_state["datasets"][label]
                    st.caption(f"{label} dataset cached ({len(existing)} rows)")

    # Show quick sample KPIs aggregated across available datasets
    datasets = load_uploaded_files()
    st.markdown("---")
    st.header("Key sample KPIs (across uploaded datasets)")
    if datasets:
        summary = utils.compute_global_kpis(datasets)
        components.render_kpi_row(
            {
                "Mean GHI": f"{summary.get('GHI_mean', float('nan')):.1f}",
                "Mean DNI": f"{summary.get('DNI_mean', float('nan')):.1f}",
                "Mean DHI": f"{summary.get('DHI_mean', float('nan')):.1f}",
            }
        )
    else:
        st.info("Upload at least one country CSV to compute KPIs.")


def visualizations_page() -> None:
    """
    Visualizations page:
    - Sidebar filters: countries, date range, metric type
    - Line chart, boxplot, bar chart
    """
    st.title("Visualizations")
    datasets = load_uploaded_files()
    if not datasets:
        st.info("No datasets loaded yet. Go to Home and upload CSV files.")
        return

    # Sidebar controls
    st.sidebar.header("Visualization filters")
    country_choices = list(datasets.keys())
    selected_countries = st.sidebar.multiselect("Select countries", country_choices, default=country_choices)
    metric = st.sidebar.selectbox("Metric", ["GHI", "DNI", "DHI"])
    # compute global date range from loaded datasets
    min_date, max_date = utils.get_datasets_date_bounds(datasets)
    date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    plot_type = st.sidebar.radio("Plot type", ["Line chart", "Boxplot", "Bar chart"])
    refresh = st.sidebar.button("Refresh data")

    if refresh:
        # trivial re-read step: in a more advanced variant we'd re-run preprocessing
        st.experimental_rerun()

    # filter datasets by selection and date range
    filtered = utils.filter_datasets(datasets, selected_countries, date_range)

    st.header(f"{plot_type} — {metric}")
    # Show line chart
    if plot_type == "Line chart":
        fig = utils.plot_line_metric(filtered, metric)
        st.plotly_chart(fig, use_container_width=True)
    elif plot_type == "Boxplot":
        fig = utils.plot_box_metric(filtered, metric)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = utils.plot_bar_metric(filtered, metric)
        st.plotly_chart(fig, use_container_width=True)

    # Small table: per-country mean for selected metric
    st.subheader("Per-country mean")
    stats_df = utils.compute_per_country_mean(filtered, metric)
    st.dataframe(stats_df)


def comparison_page() -> None:
    """
    Cross-Country Comparison page:
    - select countries to compare
    - show summary statistics table (mean, median, std for GHI/DNI/DHI)
    - boxplots / bar charts
    - top regions by mean GHI and export CSV
    """
    st.title("Cross-Country Comparison")
    datasets = load_uploaded_files()
    if not datasets:
        st.info("No datasets loaded yet. Go to Home and upload CSV files.")
        return

    st.sidebar.header("Comparison controls")
    countries = list(datasets.keys())
    selected = st.sidebar.multiselect("Choose countries to compare", countries, default=countries[:2])
    metrics = st.sidebar.multiselect("Metrics", ["GHI", "DNI", "DHI"], default=["GHI", "DNI"])
    top_n = st.sidebar.slider("Top regions to show", min_value=1, max_value=20, value=10)

    filtered = utils.filter_datasets(datasets, selected, None)

    st.header("Summary statistics")
    summary_table = utils.summary_statistics_table(filtered, metrics)
    st.dataframe(summary_table)

    csv_bytes = utils.df_to_csv_bytes(summary_table)
    st.download_button("Download summary CSV", data=csv_bytes, file_name="comparison_summary.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("Comparison plots")
    # Boxplot across selected metrics (show only first metric for boxplot)
    if metrics:
        bp = utils.plot_box_metric(filtered, metrics[0])
        st.plotly_chart(bp, use_container_width=True)

    st.subheader("Top regions by mean GHI")
    top_regions = utils.top_regions_by_metric(filtered, metric="GHI", top_n=top_n)
    if not top_regions.empty:
        st.table(top_regions)
    else:
        st.info("No region information available in uploaded datasets.")


def insights_page() -> None:
    """
    Insights & Recommendations page with Markdown narrative and computed highlights.
    """
    st.title("Insights & Recommendations")
    datasets = load_uploaded_files()
    st.markdown(
        """
        This page summarizes key insights computed from the uploaded datasets.
        Use these as placeholders and edit with domain-specific recommendations.
        """
    )

    if not datasets:
        st.info("Upload datasets on the Home page to generate automated insights.")
        return

    # Example insight: country with highest mean GHI
    top_country, top_ghi = utils.country_with_highest_mean(datasets, "GHI")
    st.metric(label="Country with highest mean GHI", value=f"{top_country}", delta=f"{top_ghi:.1f}")

    st.markdown("#### Recommendations (example)")
    st.markdown(
        """
        - Investigate the top regions above for solar project siting.
        - Consider seasonal patterns from the visualizations page when planning production estimates.
        - Validate data quality for stations with high variance.
        """
    )

    st.markdown("#### Visual summary placeholder")
    # small placeholder plot
    try:
        fig = utils.plot_bar_metric(utils.filter_datasets(datasets, list(datasets.keys()), None), "GHI")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Charts unavailable — ensure datasets include the expected columns.")


def main() -> None:
    """
    Main app function: render sidebar navigation and pages.
    """
    # App header
    components.app_header(title="Solar Challenge — Dashboard", subtitle="Interactive solar-radiation visualizer")

    page = st.sidebar.radio("Navigate", PAGES)
    # small theme toggle? left as placeholder - can be extended to change CSS
    if page == "Home":
        home_page()
    elif page == "Visualizations":
        visualizations_page()
    elif page == "Cross-Country Comparison":
        comparison_page()
    elif page == "Insights & Recommendations":
        insights_page()
    else:
        st.error("Unknown page")


if __name__ == "__main__":
    main()
