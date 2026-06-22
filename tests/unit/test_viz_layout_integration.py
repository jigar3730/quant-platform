"""Integration checks for Finqube layout against real scan reports."""

from __future__ import annotations

from pathlib import Path

import pytest

from quant_platform.viz.layout.cards import (
    build_company_hero_html,
    build_scan_summary_html,
    build_score_strip_html,
    score_pills_from_ticker,
)
from quant_platform.viz.strategy.registry import get_viz_strategy
from quant_platform.viz.strategy.reports import load_scan_report, report_to_dataframe

REPO_ROOT = Path(__file__).resolve().parents[2]
BREAKOUT_REPORT = REPO_ROOT / "data" / "output" / "breakout_scan_report.json"
SWING_REPORT = REPO_ROOT / "data" / "output" / "swing_scan_report.json"


@pytest.mark.parametrize(
    ("report_path", "strategy_id", "expected_pills"),
    [
        (BREAKOUT_REPORT, "breakout", 9),
        (SWING_REPORT, "swing", 4),
    ],
)
def test_real_report_score_pills(report_path: Path, strategy_id: str, expected_pills: int):
    if not report_path.exists():
        pytest.skip(f"Report not found: {report_path}")

    config = get_viz_strategy(strategy_id)
    report = load_scan_report(str(report_path))
    eligible = next(t for t in report["tickers"] if t.get("eligible"))
    pills = score_pills_from_ticker(eligible, config)
    assert len(pills) == expected_pills


def test_real_breakout_report_html_builders():
    if not BREAKOUT_REPORT.exists():
        pytest.skip("Breakout report not found")

    config = get_viz_strategy("breakout")
    report = load_scan_report(str(BREAKOUT_REPORT))
    ticker = next(t for t in report["tickers"] if t.get("eligible"))
    df = report_to_dataframe(report, config)
    summary = report["scan_summary"]
    regime = report["market_regime"]

    scan_html = build_scan_summary_html(
        strategy_label=config.label,
        summary=summary,
        regime=regime,
        config=config,
    )
    assert config.label in scan_html
    assert "scan-summary-strip" in scan_html

    pills = score_pills_from_ticker(ticker, config)
    strip_html = build_score_strip_html(
        final_score=float(ticker["summary"]["final_adjusted_score"]),
        regime_multiplier=ticker["summary"].get("regime_multiplier"),
        pills=pills,
    )
    assert "score-strip" in strip_html
    assert str(ticker["summary"]["final_adjusted_score"])[:3] in strip_html

    hero_html = build_company_hero_html(
        ticker=ticker["ticker"],
        company_name=ticker["ticker"],
        tier_badge=f'<span class="tier-badge">{ticker["tier"]}</span>',
        strategy_label=config.label,
        snapshot=None,
        sector_etf=ticker.get("sector_etf"),
        scan_date="2026-06-19",
        insight=ticker.get("tier_reason", ""),
    )
    assert ticker["ticker"] in hero_html
    assert "company-hero" in hero_html
    assert not df.empty
