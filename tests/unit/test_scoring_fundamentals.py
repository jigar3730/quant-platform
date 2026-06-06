from quant_platform.scoring.fundamentals import score_eps, score_revenue


def test_revenue_boundaries():
    assert score_revenue(0.45) == 15.0
    assert score_revenue(0.30) == 12.0
    assert score_revenue(0.20) == 8.0
    assert score_revenue(0.10) == 4.0
    assert score_revenue(0.0) == 0.0
    assert score_revenue(None) == 0.0


def test_eps_boundaries():
    assert score_eps(0.55) == 15.0
    assert score_eps(0.35) == 12.0
    assert score_eps(0.20) == 8.0
    assert score_eps(0.05) == 4.0
    assert score_eps(-0.1) == 0.0
    assert score_eps(None) == 0.0
