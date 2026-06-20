"""Peter Lynch scanner pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from quant_platform.config import (
    DEFAULT_LYNCH_CSV,
    DEFAULT_LYNCH_JSON,
    DEFAULT_LYNCH_MD,
)
from quant_platform.data.tickers import resolve_universe
from quant_platform.history.lynch_archive import archive_lynch_outputs
from quant_platform.lynch import config as lynch_cfg
from quant_platform.lynch.categories import (
    QUALITATIVE_OVERLAY,
    assign_categories,
    classify_asset_play,
    classify_fast_grower,
    classify_stalwart,
)
from quant_platform.lynch.filters import apply_anti_filters, apply_base_screen, lynch_score
from quant_platform.lynch.metrics import fetch_lynch_metrics_batch
from quant_platform.lynch.report import export_json, export_markdown
from quant_platform.strategies.registry import get_strategy

logger = logging.getLogger(__name__)

class LynchScannerRunner:
    def __init__(
        self,
        *,
        tickers: list[str] | None = None,
        tickers_file: Path | None = None,
        dynamic_universe: bool = False,
        preset: str = "summary",
        output: Path = DEFAULT_LYNCH_CSV,
        report: str | None = None,
        report_json: Path = DEFAULT_LYNCH_JSON,
        report_md: Path = DEFAULT_LYNCH_MD,
        archive: bool = False,
    ) -> None:
        if preset not in lynch_cfg.PRESETS:
            raise ValueError(f"Unknown preset: {preset}")
        self.tickers = tickers
        self.tickers_file = tickers_file
        self.dynamic_universe = dynamic_universe
        self.preset = preset
        self._strategy = get_strategy("lynch")
        self.output = output
        self.report = report
        self.report_json = report_json
        self.report_md = report_md
        self.archive = archive

    def run(self) -> pd.DataFrame:
        universe = resolve_universe(
            self.tickers,
            tickers_file=self.tickers_file,
            dynamic=self.dynamic_universe,
        )
        logger.info("Lynch scan: %d tickers, preset=%s", len(universe), self.preset)

        metrics_list = fetch_lynch_metrics_batch(universe)
        rows: list[dict] = []
        candidates: list[dict] = []

        for metrics in metrics_list:
            detail = self._evaluate(metrics)
            rows.append(detail)
            if detail["passed"]:
                candidates.append(detail)

        df = pd.DataFrame([_csv_row(r) for r in rows])
        if not df.empty:
            df = df.sort_values(
                ["passed", "lynch_score", "peg_ratio"],
                ascending=[False, False, True],
                na_position="last",
            )

        self.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output, index=False)
        logger.info("Wrote %d rows to %s", len(df), self.output)

        scan_report = None
        if self.report or self.archive:
            scan_report = self._build_report(universe, rows, candidates)
        if self.report and scan_report:
            if self.report in ("json", "both"):
                export_json(scan_report, self.report_json)
                logger.info("Wrote Lynch JSON report to %s", self.report_json)
            if self.report in ("md", "both"):
                export_markdown(scan_report, self.report_md)
                logger.info("Wrote Lynch markdown summary to %s", self.report_md)

        if self.archive and scan_report:
            if self.report not in ("json", "both"):
                export_json(scan_report, self.report_json)
            archive_dir = archive_lynch_outputs(
                csv_path=self.output,
                json_path=self.report_json,
                md_path=self.report_md if self.report in ("md", "both") else None,
                scan_report=scan_report,
            )
            logger.info("Archived Lynch scan to %s", archive_dir)

        return df

    def _evaluate(self, metrics: dict) -> dict:
        ticker = metrics.get("ticker", "?")
        anti_ok, anti_checks, anti_fail = apply_anti_filters(metrics)
        all_checks = list(anti_checks)

        passed = False
        fail_reason = anti_fail
        categories: list[str] = []

        if anti_ok:
            if self.preset == "fast_grower":
                passed, preset_checks = classify_fast_grower(metrics)
                all_checks.extend(preset_checks)
                if passed:
                    categories = ["fast_grower"]
                else:
                    fail_reason = "fast_grower_criteria"
            elif self.preset == "stalwart":
                passed, preset_checks = classify_stalwart(metrics)
                all_checks.extend(preset_checks)
                if passed:
                    categories = ["stalwart"]
                else:
                    fail_reason = "stalwart_criteria"
            elif self.preset == "asset_play":
                passed, preset_checks = classify_asset_play(metrics)
                all_checks.extend(preset_checks)
                if passed:
                    categories = ["asset_play"]
                else:
                    fail_reason = "asset_play_criteria"
            elif self.preset == "base":
                passed, base_checks, fail_reason = apply_base_screen(metrics)
                all_checks.extend(base_checks)
            else:  # summary
                base_ok, base_checks, base_fail = apply_base_screen(metrics)
                all_checks.extend(base_checks)
                categories = assign_categories(metrics)
                passed = base_ok or bool(categories)
                fail_reason = None if passed else (base_fail or "no_category_match")

        score = lynch_score(all_checks)
        m = metrics

        return {
            "ticker": ticker,
            "company_name": m.get("company_name"),
            "sector": m.get("sector"),
            "passed": passed,
            "preset": self.preset,
            "categories": categories,
            "lynch_score": score,
            "fail_reason": fail_reason or "",
            "tier_reason": _tier_reason(passed, categories, m),
            "pe_ratio": m.get("pe_ratio"),
            "peg_ratio": m.get("peg_ratio"),
            "eps_growth_5y_pct": _to_pct(m.get("eps_growth_5y")),
            "debt_to_equity": m.get("debt_to_equity"),
            "institutional_pct": _to_pct(m.get("institutional_ownership")),
            "analyst_count": m.get("analyst_count"),
            "market_cap": m.get("market_cap"),
            "dividend_yield": m.get("dividend_yield"),
            "price_to_book": m.get("price_to_book"),
            "net_cash": m.get("net_cash"),
            "metrics": m,
            "checks": all_checks,
            "qualitative_overlay": QUALITATIVE_OVERLAY,
        }

    def _build_report(
        self,
        universe: list[str],
        rows: list[dict],
        candidates: list[dict],
    ) -> dict:
        cat_counts = {
            "fast_grower": sum(1 for r in rows if "fast_grower" in r.get("categories", [])),
            "stalwart": sum(1 for r in rows if "stalwart" in r.get("categories", [])),
            "asset_play": sum(1 for r in rows if "asset_play" in r.get("categories", [])),
        }
        sorted_candidates = sorted(
            candidates,
            key=lambda r: (r.get("lynch_score", 0), -(r.get("peg_ratio") or 99)),
            reverse=True,
        )
        return {
            "strategy_id": "lynch",
            "scan_summary": {
                "scanner": "peter_lynch",
                "preset": self.preset,
                "preset_label": lynch_cfg.PRESET_LABELS[self.preset],
                "universe_size": len(universe),
                "passed_count": sum(1 for r in rows if r["passed"]),
                "category_counts": cat_counts,
            },
            "qualitative_overlay": QUALITATIVE_OVERLAY,
            "tickers": rows,
            "candidates": sorted_candidates,
        }


def _csv_row(detail: dict) -> dict:
    return {
        "ticker": detail["ticker"],
        "company_name": detail.get("company_name"),
        "sector": detail.get("sector"),
        "passed": detail["passed"],
        "categories": ",".join(detail.get("categories", [])),
        "lynch_score": detail["lynch_score"],
        "fail_reason": detail.get("fail_reason"),
        "tier_reason": detail.get("tier_reason"),
        "pe_ratio": detail.get("pe_ratio"),
        "peg_ratio": detail.get("peg_ratio"),
        "eps_growth_5y_pct": detail.get("eps_growth_5y_pct"),
        "debt_to_equity": detail.get("debt_to_equity"),
        "institutional_pct": detail.get("institutional_pct"),
        "analyst_count": detail.get("analyst_count"),
        "market_cap": detail.get("market_cap"),
        "dividend_yield": detail.get("dividend_yield"),
        "price_to_book": detail.get("price_to_book"),
        "net_cash": detail.get("net_cash"),
    }


def _to_pct(value) -> float | None:
    if value is None:
        return None
    v = float(value)
    return round(v * 100, 2) if abs(v) <= 1.5 else round(v, 2)


def _tier_reason(passed: bool, categories: list[str], metrics: dict) -> str:
    if not passed:
        return "Did not pass Lynch quantitative screen"
    if categories:
        labels = ", ".join(c.replace("_", " ").title() for c in categories)
        return f"Lynch match: {labels}"
    peg = metrics.get("peg_ratio")
    if peg is not None and peg < lynch_cfg.PEG_BARGAIN:
        return f"Base screen pass; exceptional PEG bargain ({peg:.2f})"
    return "Passes Lynch base quantitative screen"
