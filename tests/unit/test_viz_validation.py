from quant_platform.viz.shared.validation import regime_looks_synthetic


def test_regime_looks_synthetic_detects_dry_run():
    assert regime_looks_synthetic({"spy_price": 113.1}) is True


def test_regime_looks_synthetic_accepts_live_spy():
    assert regime_looks_synthetic({"spy_price": 737.55}) is False
