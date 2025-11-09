"""Unit tests for the DataCleaner module.

These are minimal, fast tests to demonstrate how the class can be validated with
pytest. They do not require external files — synthetic data is used.
"""
import pandas as pd
from src.cleaning import DataCleaner


def make_sample_df():
    data = {
        "Timestamp": [
            "2024-01-01 00:00",
            "2024-01-01 01:00",
            "2024-01-01 02:00",
            "2024-01-01 03:00",
        ],
        "GHI": [0, 10, -5, 20],
        "RH": [50, 55, None, 60],
        "Cleaning": [0, 1, 0, None],
    }
    return pd.DataFrame(data)


def test_data_cleaner_basic_flow():
    df = make_sample_df()
    dc = DataCleaner()
    # load from DataFrame by temporarily assigning
    dc.df = df.copy()
    dc.set_index_timestamp()
    dc.enforce_dtypes()
    dc.basic_clipping_impute()
    # after clipping negative GHI should be 0
    assert (dc.df["GHI"] >= 0).all()
    # RH should have no values >100 or <0
    assert dc.df["RH"].between(0, 100).all()
    # Cleaning should be Int64 dtype (nullable integer)
    assert str(dc.df["Cleaning"].dtype).startswith("Int")
