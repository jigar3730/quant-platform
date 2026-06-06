from quant_platform.data.sector import resolve_sector_etf


def test_technology_sector():
    assert resolve_sector_etf("AAPL", {"sector": "Technology", "industry": ""}) == "XLK"


def test_semiconductor_industry():
    assert (
        resolve_sector_etf("NVDA", {"sector": "Technology", "industry": "Semiconductors"})
        == "SOXX"
    )


def test_unmapped_fallback():
    assert resolve_sector_etf("XYZ", {"sector": "Unknown", "industry": ""}) == "SPY"
