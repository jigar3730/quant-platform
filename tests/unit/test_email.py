from datetime import date
from unittest.mock import MagicMock, patch

from quant_platform.notify.email import (
    EmailConfig,
    build_actionable_email,
    get_actionable_tickers,
    send_scan_email,
)


def _scores(rs=10, comp=5, vol=3):
    return {
        "rs_market": {"score": rs, "max": 20, "meaning": "ok"},
        "compression": {"score": comp, "max": 15, "meaning": "wide"},
        "relative_volume": {"score": vol, "max": 8, "meaning": "normal"},
    }


def _report():
    return {
        "scan_summary": {
            "universe_size": 3,
            "eligible_count": 2,
            "tier_counts": {"Tier 1": 1, "Tier 2": 1, "Tier 3": 0, "filtered": 1},
        },
        "market_regime": {
            "label": "strong",
            "multiplier": 1.0,
            "spy_price": 500,
            "return_63d_pct": 5.0,
        },
        "tickers": [
            {
                "ticker": "AAA",
                "tier": "Tier 1",
                "tier_reason": "ready",
                "summary": {"final_adjusted_score": 85},
                "scores": _scores(18, 10, 5),
            },
            {
                "ticker": "BBB",
                "tier": "Tier 2",
                "tier_reason": "watch",
                "summary": {"final_adjusted_score": 70},
                "scores": _scores(12, 3, 3),
            },
            {
                "ticker": "CCC",
                "tier": "Tier 3",
                "tier_reason": "low",
                "summary": {"final_adjusted_score": 40},
                "scores": {},
            },
        ],
    }


def test_get_actionable_tickers():
    actionable = get_actionable_tickers(_report())
    assert len(actionable) == 2
    assert {t["ticker"] for t in actionable} == {"AAA", "BBB"}


def test_build_actionable_email():
    subject, html = build_actionable_email(_report(), scan_date=date(2026, 6, 6))
    assert "2026-06-06" in subject
    assert "2 Actionable" in subject
    assert "AAA" in html
    assert "BBB" in html
    assert "CCC" not in html


@patch("quant_platform.notify.email.smtplib.SMTP")
def test_send_scan_email(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_server

    config = EmailConfig(
        host="smtp.test.com",
        port=587,
        user="user",
        password="pass",
        from_addr="from@test.com",
        to_addrs=["to@test.com"],
    )
    sent = send_scan_email(_report(), config=config)
    assert sent
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user", "pass")
    mock_server.sendmail.assert_called_once()
