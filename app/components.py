"""
Small UI components reused across pages.
"""
from __future__ import annotations
from typing import Dict
import streamlit as st


def app_header(title: str, subtitle: str = "") -> None:
    """
    Render the top header of the app.
    """
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"**{subtitle}**")
    st.markdown("---")


def render_kpi_row(kpis: Dict[str, str]) -> None:
    """
    Render a horizontal row of KPI cards.

    kpis: mapping label -> value (string)
    """
    cols = st.columns(len(kpis))
    for col, (label, value) in zip(cols, kpis.items()):
        with col:
            st.metric(label, value)