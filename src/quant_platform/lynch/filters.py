"""Peter Lynch quantitative filters and anti-filters."""

from __future__ import annotations

from quant_platform.lynch import config as cfg


def _check(
    rule: str,
    passed: bool,
    *,
    value,
    threshold: str,
    detail: str = "",
) -> dict:
    return {
        "rule": rule,
        "passed": passed,
        "value": value,
        "threshold": threshold,
        "detail": detail,
    }


def apply_anti_filters(metrics: dict) -> tuple[bool, list[dict], str | None]:
    """Return (passed, checks, fail_reason)."""
    if metrics.get("error"):
        return False, [], metrics["error"]

    checks: list[dict] = []
    eps = metrics.get("trailing_eps")
    pe = metrics.get("pe_ratio")

    profitable = eps is not None and float(eps) > 0
    checks.append(
        _check(
            "positive_earnings",
            profitable,
            value=eps,
            threshold="trailing EPS > 0",
            detail="Avoid pre-profit speculative names",
        )
    )

    roe = metrics.get("return_on_equity")
    roe_ok = roe is None or roe >= cfg.ROE_MIN_ANTI
    checks.append(
        _check(
            "return_on_equity",
            roe_ok,
            value=roe,
            threshold=f">= {cfg.ROE_MIN_ANTI:.0%} (ROIC proxy)",
        )
    )

    rev_cv = metrics.get("revenue_cv")
    rev_stable = rev_cv is None or rev_cv <= cfg.REVENUE_CV_MAX
    checks.append(
        _check(
            "revenue_stability",
            rev_stable,
            value=rev_cv,
            threshold=f"revenue CV <= {cfg.REVENUE_CV_MAX}",
            detail="High volatility may signal customer concentration risk",
        )
    )

    if not profitable and (pe is None or pe <= 0):
        return False, checks, "no_earnings"

    if not all(c["passed"] for c in checks):
        failed = next(c["rule"] for c in checks if not c["passed"])
        return False, checks, failed

    return True, checks, None


def apply_base_screen(metrics: dict) -> tuple[bool, list[dict], str | None]:
    """Part 1 core Lynch screen."""
    if metrics.get("error"):
        return False, [], metrics["error"]

    checks: list[dict] = []
    peg = metrics.get("peg_ratio")
    peg_ok = peg is not None and peg <= cfg.PEG_MAX
    checks.append(
        _check("peg_ratio", peg_ok, value=peg, threshold=f"<= {cfg.PEG_MAX}")
    )

    growth = metrics.get("eps_growth_5y")
    growth_ok = (
        growth is not None and cfg.EPS_GROWTH_MIN <= float(growth) <= cfg.EPS_GROWTH_MAX
    )
    checks.append(
        _check(
            "eps_growth_5y",
            growth_ok,
            value=_pct(growth),
            threshold=f"{cfg.EPS_GROWTH_MIN:.0%} – {cfg.EPS_GROWTH_MAX:.0%}",
        )
    )

    pe = metrics.get("pe_ratio")
    pe_ok = pe is not None and pe < cfg.PE_MAX
    checks.append(_check("pe_ratio", pe_ok, value=pe, threshold=f"< {cfg.PE_MAX}"))

    de = metrics.get("debt_to_equity")
    de_ok = de is not None and de < cfg.DEBT_TO_EQUITY_MAX
    checks.append(
        _check(
            "debt_to_equity",
            de_ok,
            value=de,
            threshold=f"< {cfg.DEBT_TO_EQUITY_MAX:.2f} (D/E ratio)",
        )
    )

    net_cash = metrics.get("net_cash")
    net_cash_ok = net_cash is not None and net_cash > 0
    checks.append(
        _check(
            "net_cash_positive",
            net_cash_ok,
            value=net_cash,
            threshold="total cash > total debt",
        )
    )

    inst = metrics.get("institutional_ownership")
    analysts = metrics.get("analyst_count")
    neglected = False
    if inst is not None and inst < cfg.INSTITUTIONAL_OWNERSHIP_MAX:
        neglected = True
    if analysts is not None and analysts <= cfg.ANALYST_COVERAGE_MAX:
        neglected = True
    checks.append(
        _check(
            "wall_street_neglect",
            neglected,
            value={"institutional_pct": _pct(inst), "analysts": analysts},
            threshold=(
                f"inst < {cfg.INSTITUTIONAL_OWNERSHIP_MAX:.0%} "
                f"OR analysts <= {cfg.ANALYST_COVERAGE_MAX}"
            ),
        )
    )

    insider_buy = metrics.get("insider_purchases_6m")
    shares_chg = metrics.get("shares_outstanding_change_yoy")
    alignment = False
    if insider_buy is not None and insider_buy > 0:
        alignment = True
    if shares_chg is not None and shares_chg < 0:
        alignment = True
    checks.append(
        _check(
            "insider_or_buyback",
            alignment,
            value={"insider_purchases_6m": insider_buy, "shares_change_yoy": _pct(shares_chg)},
            threshold="insider buying > 0 OR shares outstanding declining",
        )
    )

    if not all(c["passed"] for c in checks):
        failed = next(c["rule"] for c in checks if not c["passed"])
        return False, checks, failed
    return True, checks, None


def _pct(value) -> str | float | None:
    if value is None:
        return None
    try:
        v = float(value)
        if abs(v) <= 1.5:
            return round(v * 100, 2)
        return round(v, 2)
    except (TypeError, ValueError):
        return value


def lynch_score(checks: list[dict]) -> float:
    if not checks:
        return 0.0
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / len(checks) * 100, 1)
