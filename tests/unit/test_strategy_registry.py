from quant_platform.strategies.lynch.spec import LynchStrategySpec, lynch_strategy
from quant_platform.strategies.registry import STRATEGY_IDS, get_strategy


def test_strategy_registry():
    for sid in ("breakout", "swing", "lynch", "fake"):
        spec = get_strategy(sid)
        assert spec.id == sid

    assert set(STRATEGY_IDS) == {"breakout", "swing", "lynch", "fake"}


def test_lynch_strategy_spec_defaults():
    spec = LynchStrategySpec(
        id="lynch",
        name="Peter Lynch Scanner",
        max_raw_score=100.0,
        regime_mode="none",
    )
    assert spec.filters == []
    assert spec.factor_bindings == []
    assert spec.penalties == []
    assert spec.preset == "summary"

    factory = lynch_strategy("fast_grower")
    assert factory.preset == "fast_grower"
    assert factory.filters == []
