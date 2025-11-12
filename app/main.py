# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# Dark theme: make background black and text white
st.markdown(
        """
        <style>
            html, body, .stApp, .reportview-container, .main {background-color: #000000; color: #ffffff}
            .block-container {background-color: #000000}
            table {color: #ffffff}
        </style>
        """,
        unsafe_allow_html=True,
)
#st.set_page_config(layout="wide")
st.title("📈 Cross-Country Comparison Dashboard")
st.subheader("☀️ Three-Country Temperature Comparison for Solar Performance")
st.write("Upload temperature data for three countries to compare solar company performance side-by-side.")

# --- File Uploaders in Sidebar ---
st.sidebar.header("Upload Your Data")

# Create two columns for the file uploaders
col1, col2, col3 = st.sidebar.columns(3)

with col1:
    uploaded_file_1 = st.file_uploader("Upload Benin's CSV file", type="csv", key="file1")

with col2:
    uploaded_file_2 = st.file_uploader("Upload Sierra Leone's CSV file", type="csv", key="file2")

with col3:
    uploaded_file_3 = st.file_uploader("Upload Togo's CSV file", type="csv", key="file3")

# Check if all files have been uploaded before proceeding
if uploaded_file_1 is not None and uploaded_file_2 is not None and uploaded_file_3 is not None:
    try:
        # Read each CSV file into a separate DataFrame
        df1 = pd.read_csv(uploaded_file_1)
        df2 = pd.read_csv(uploaded_file_2)
        df3 = pd.read_csv(uploaded_file_3)

        # --- THE CRUCIAL STEP: COMBINING DATA ---
        # Add a new column to each DataFrame to identify the company
        df1['Company'] = 'Benin'
        df2['Company'] = 'Sierra Leone'
        df3['Company'] = 'Togo'

        # Combine the three DataFrames into a single one
        df_combined = pd.concat([df1, df2, df3], ignore_index=True)

        st.sidebar.success("Files uploaded and combined successfully!")

    except Exception as e:
        st.error(f"Error processing files: {e}")
        st.stop()


    # --- DISPLAY THE DASHBOARD ---
    st.header("Side-by-Side Performance")

    # --- 1. Key Performance Indicators (KPIs) ---
    st.subheader("Overall Totals")
    
    # Create two columns for the KPIs
    kpi_col1, kpi_col2 = st.columns(2)
    
    with kpi_col1:
        total_revenue_A = df1['Revenue'].sum()
        st.metric(label="Company A Total Revenue", value=f"${total_revenue_A:,}")

    with kpi_col2:
        total_revenue_B = df2['Revenue'].sum()
        st.metric(label="Company B Total Revenue", value=f"${total_revenue_B:,}")

    # --- 2. Comparative Bar Chart ---
    st.subheader("Monthly Revenue Comparison")
    
    # Let the user select which metric to plot
    metric_to_plot = st.selectbox("Select a metric to compare:", ['Revenue', 'Units Sold'])
    
    try:
        fig = px.bar(
            df_combined,
            x='Month',
            y=metric_to_plot,
            color='Company',        
            barmode='group',        # This places bars side-by-side
            title=f"Monthly {metric_to_plot} Comparison"
        )
        # style the plotly figure for dark background
        fig.update_layout(
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            font=dict(color="#ffffff"),
        )
        fig.update_xaxes(color="#ffffff")
        fig.update_yaxes(color="#ffffff", gridcolor="#333333")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating chart: {e}")

    # --- 3. Data Preview ---
    with st.expander("Show Combined Data"):
        st.dataframe(df_combined)

# This is the message that shows before files are uploaded
else:
    st.info("Please upload both CSV files in the sidebar to begin the comparison.")
