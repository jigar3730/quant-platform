from quant_platform.engine.context import ScanContext, synthetic_prices


def test_scan_context_dry_run():
    ctx = ScanContext.from_universe(tickers=["AAA", "BBB"], dry_run=True)
    assert len(ctx.universe) == 2
    assert ctx.spy_df is not None
    assert "AAA" in ctx.stock_dfs
    df = ctx.stock_df("AAA")
    assert df is not None
    assert len(df) >= 200
    assert set(df.columns) >= {"Date", "Open", "High", "Low", "Close", "Volume"}


def test_synthetic_prices_deterministic():
    a = synthetic_prices(["X", "Y"])
    b = synthetic_prices(["X", "Y"])
    assert a["Close"].tolist() == b["Close"].tolist()
