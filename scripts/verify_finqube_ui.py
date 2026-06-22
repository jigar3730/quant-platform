"""Static verification for Finqube UI overhaul success criteria."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    dash = (REPO / "src/quant_platform/dashboard.py").read_text(encoding="utf-8")
    ps = (REPO / "src/quant_platform/viz/pages/price_scanner.py").read_text(encoding="utf-8")
    nav = (REPO / "src/quant_platform/viz/shared/navigation.py").read_text(encoding="utf-8")
    comp = (REPO / "src/quant_platform/viz/shared/components.py").read_text(encoding="utf-8")
    layout = REPO / "src/quant_platform/viz/layout"

    checks: dict[str, bool] = {
        "dashboard uses app shell": "render_app_shell" in dash,
        "dashboard uses price router": "render_price_scanner" in dash,
        "old 5-tab layout removed": "Full Universe" not in dash and "render_all_tickers_tab" not in dash,
        "sidebar collapsed for price": 'initial_sidebar_state="collapsed"' in dash,
        "lynch path preserved": "render_lynch_pages" in dash,
        "router dispatches company": "render_company_page" in ps,
        "router dispatches universe": "render_universe_page" in ps,
        "router dispatches compare": "render_compare_page" in ps,
        "split preview removed": "render_universe_detail_panel" not in ps,
        "layout modules present": all((layout / name).exists() for name in (
            "shell.py", "company.py", "universe.py", "compare.py", "cards.py"
        )),
        "resolve_view helper": "def resolve_view" in nav,
        "compare view param": "compare" in nav,
        "render_ticker_detail delegates": "render_company_page" in comp,
    }

    from quant_platform.viz.strategy.registry import get_viz_strategy
    from quant_platform.viz.strategy.reports import load_scan_report, report_to_dataframe
    from quant_platform.viz.layout.cards import score_pills_from_ticker

    breakout = get_viz_strategy("breakout")
    swing = get_viz_strategy("swing")
    breakout_report = load_scan_report(str(REPO / "data/output/breakout_scan_report.json"))
    swing_report = load_scan_report(str(REPO / "data/output/swing_scan_report.json"))

    b_eligible = next(t for t in breakout_report["tickers"] if t.get("eligible"))
    s_eligible = next(t for t in swing_report["tickers"] if t.get("eligible"))

    checks["breakout 9 score pills"] = len(score_pills_from_ticker(b_eligible, breakout)) == 9
    checks["swing 4 score pills"] = len(score_pills_from_ticker(s_eligible, swing)) == 4
    checks["breakout report loads"] = len(report_to_dataframe(breakout_report, breakout)) == 15
    checks["swing report loads"] = len(report_to_dataframe(swing_report, swing)) == 15

    print("Finqube UI verification")
    print("-" * 40)
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")

    failed = [name for name, ok in checks.items() if not ok]
    print("-" * 40)
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
