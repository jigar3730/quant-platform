import numpy as np
import pandas as pd

from quant_platform.scoring.volume import (
    compute_accumulation_ratio,
    score_accumulation,
    score_relative_volume,
)


def test_accumulation_ratio():
    df = pd.DataFrame(
        {
            "Close": [10, 11, 10, 12, 11, 13, 12, 14, 13, 15] * 2,
            "Volume": [100, 200, 150, 300, 250, 400, 350, 500, 450, 600] * 2,
        }
    )
    ratio = compute_accumulation_ratio(df, window=20)
    assert ratio is not None
    assert ratio > 1.0


def test_score_accumulation_percentile():
    ratios = pd.Series({"A": 2.0, "B": 1.5, "C": 1.0})
    scores = score_accumulation(ratios)
    assert scores["A"] == 12.0
    assert scores["C"] == 4.0


def test_relative_volume_thresholds():
    base_vol = 1_000_000
    df = pd.DataFrame(
        {
            "Close": np.arange(21) + 100,
            "Volume": [base_vol] * 20 + [base_vol * 2.5],
        }
    )
    assert score_relative_volume(df) == 8.0

    df["Volume"] = [base_vol] * 20 + [base_vol * 1.6]
    assert score_relative_volume(df) == 5.0

    df["Volume"] = [base_vol] * 20 + [base_vol * 1.3]
    assert score_relative_volume(df) == 3.0

    df["Volume"] = [base_vol] * 21
    assert score_relative_volume(df) == 0.0
