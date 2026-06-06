import pandas as pd

from quant_platform.viz.data import full_universe_dataframe


def test_full_universe_dataframe_includes_scores():
    tickers = [
        {
            "ticker": "MU",
            "eligible": True,
            "tier": "Tier 3",
            "sector_etf": "SOXX",
            "eligibility": {"fail_reason": None},
            "summary": {
                "final_adjusted_score": 64.0,
                "normalized_score": 64.0,
                "raw_score": 76.8,
            },
            "scores": {
                "rs_market": {"score": 18.0, "max": 20},
                "revenue": {"score": 15.0, "max": 15, "raw": {"revenue_yoy_pct": 196.3}},
                "eps": {"score": 15.0, "max": 15, "raw": {"eps_combined_pct": 756.0}},
            },
        },
        {
            "ticker": "XYZ",
            "eligible": False,
            "tier": "filtered",
            "eligibility": {"fail_reason": "trend_misaligned"},
            "summary": {"final_adjusted_score": 0, "normalized_score": 0, "raw_score": 0},
            "scores": None,
        },
    ]

    df = full_universe_dataframe(tickers)
    assert len(df) == 2
    mu = df[df["ticker"] == "MU"].iloc[0]
    assert mu["final_score"] == 64.0
    assert mu["RS vs Market"] == 18.0
    assert mu["revenue_yoy_pct"] == 196.3
    assert mu["eps_growth_pct"] == 756.0

    xyz = df[df["ticker"] == "XYZ"].iloc[0]
    assert pd.isna(xyz["RS vs Market"])
    assert xyz["filter_reason"] == "trend_misaligned"
