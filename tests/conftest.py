import pandas as pd
import pytest


@pytest.fixture
def date_index():
    return pd.bdate_range(end="2024-06-01", periods=260)
