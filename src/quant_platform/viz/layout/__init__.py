"""Finqube-style layout components."""

from quant_platform.viz.layout.cards import (
    build_company_hero_html,
    build_key_insight_html,
    build_scan_summary_html,
    build_score_strip_html,
    build_universe_context_html,
    rank_factor_insights,
    score_pills_from_ticker,
)
from quant_platform.viz.layout.company import render_company_page
from quant_platform.viz.layout.compare import render_compare_page
from quant_platform.viz.layout.shell import ShellState, render_app_shell, render_lynch_sidebar
from quant_platform.viz.layout.universe import render_universe_page

__all__ = [
    "ShellState",
    "build_company_hero_html",
    "build_key_insight_html",
    "build_scan_summary_html",
    "build_score_strip_html",
    "build_universe_context_html",
    "rank_factor_insights",
    "render_app_shell",
    "render_company_page",
    "render_compare_page",
    "render_lynch_sidebar",
    "render_universe_page",
    "score_pills_from_ticker",
]
