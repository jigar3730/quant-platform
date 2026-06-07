import pandas as pd

from quant_platform.viz.display import format_display_value
from quant_platform.viz.lynch_data import lynch_checks_dataframe


def test_format_display_value_handles_mixed_types():
    assert format_display_value(None) == "—"
    assert format_display_value({"institutional_pct": 65.82}) == '{"institutional_pct": 65.82}'
    assert format_display_value("Consumer Electronics") == "Consumer Electronics"
    assert format_display_value(0.25) == "25.00%"
    assert format_display_value(15.5) == "15.5"


def test_lynch_checks_dataframe_arrow_safe_strings():
    ticker = {
        "checks": [
            {
                "rule": "peg_ratio",
                "passed": True,
                "value": {"institutional_pct": 65.82, "analysts": 43},
                "threshold": "<= 1.0",
            },
            {
                "rule": "sector",
                "passed": False,
                "value": "Consumer Electronics",
                "threshold": None,
            },
        ]
    }
    df = lynch_checks_dataframe(ticker)
    assert all(isinstance(value, str) for value in df["value"])
    assert all(isinstance(value, str) for value in df["threshold"])
    # Streamlit serializes via Arrow — mixed object column of strings must convert cleanly
    import pyarrow as pa

    table = pa.Table.from_pandas(df)
    assert table.num_rows == 2
