import pandas as pd
from src.compare import compare_countries, summarize_countries


def _make_df(ghi_vals, ws_vals=None, precip_vals=None):
    data = {"GHI": ghi_vals}
    if ws_vals is not None:
        data["WS"] = ws_vals
    if precip_vals is not None:
        data["Precipitation"] = precip_vals
    return pd.DataFrame(data)


def test_compare_countries_basic():
    df_a = _make_df([0.0, 5.0, 10.0], ws_vals=[1.0, 2.0, 3.0], precip_vals=[0.0, 0.0, 1.0])
    df_b = _make_df([2.0, 2.0, 2.0], ws_vals=[0.5, 0.5, 0.5], precip_vals=[0.0, 1.0, 0.0])

    res = compare_countries({"A": df_a, "B": df_b})

    assert "A" in res.index and "B" in res.index
    assert res.loc["A", "observations"] == 3
    # means roughly match expected
    assert abs(res.loc["A", "ghi_mean"] - df_a["GHI"].mean()) < 1e-8
    assert abs(res.loc["B", "ws_mean"] - df_b["WS"].mean()) < 1e-8


def test_summarize_alias():
    # alias should return identical results
    df = _make_df([1, 2, 3])
    a = compare_countries({"X": df})
    b = summarize_countries({"X": df})
    pd.testing.assert_frame_equal(a, b)
