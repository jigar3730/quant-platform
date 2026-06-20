from quant_platform.strategies.registry import STRATEGY_IDS, get_strategy


def test_strategy_registry():
    for sid in ("breakout", "swing", "lynch", "fake"):
        spec = get_strategy(sid)
        assert spec.id == sid

    assert set(STRATEGY_IDS) == {"breakout", "swing", "lynch", "fake"}
