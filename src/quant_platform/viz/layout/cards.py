"""HTML card builders for Finqube-style layout."""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from quant_platform.filters.eligibility import FILTER_LABELS
from quant_platform.viz.strategy.registry import VizStrategyConfig


def _esc(text: str | None) -> str:
    if text is None:
        return ""
    return html.escape(str(text))


def format_market_cap(value: float | None) -> str:
    if not value:
        return "—"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:.1f}M"
    return f"${value:,.0f}"


def build_company_hero_html(
    *,
    ticker: str,
    company_name: str | None,
    tier_badge: str,
    strategy_label: str,
    snapshot: dict | None,
    sector_etf: str | None,
    scan_date: str,
    insight: str,
) -> str:
    name = _esc(company_name or ticker)
    price_html = "—"
    change_html = ""
    mcap_html = "—"
    year_html = "—"

    if snapshot:
        price = snapshot.get("price")
        if price is not None:
            price_html = f"${price:,.2f}"
        change = snapshot.get("change_pct")
        if change is not None:
            cls = "hero-change-up" if change >= 0 else "hero-change-down"
            arrow = "▲" if change >= 0 else "▼"
            change_html = f'<span class="{cls}">{arrow} {change:+.2f}% today</span>'
        mcap_html = format_market_cap(snapshot.get("market_cap"))
        year_chg = snapshot.get("year_change_pct")
        if year_chg is not None:
            year_html = f"{year_chg:+.1f}%"

    sector = _esc(sector_etf or "—")
    insight_block = ""
    if insight:
        insight_block = f'<div class="hero-insight">{_esc(insight)}</div>'

    return f"""
    <div class="company-hero">
      <div class="hero-top">
        <div>
          <p class="hero-ticker">{_esc(ticker)}</p>
          <p class="hero-name">{name}</p>
        </div>
        <div class="hero-badges">
          {tier_badge}
          <span class="strategy-badge">{_esc(strategy_label)}</span>
        </div>
      </div>
      <div class="hero-price-row">
        <div>
          <span class="hero-price">{price_html}</span>
          {f" {change_html}" if change_html else ""}
        </div>
        <div class="hero-stat"><span>Market cap</span><strong>{mcap_html}</strong></div>
        <div class="hero-stat"><span>Sector ETF</span><strong>{sector}</strong></div>
        <div class="hero-stat"><span>1Y change</span><strong>{year_html}</strong></div>
        <div class="hero-stat"><span>Scan</span><strong>{_esc(scan_date)}</strong></div>
      </div>
      {insight_block}
    </div>
    """


def build_score_strip_html(
    *,
    final_score: float,
    regime_multiplier: float | None,
    pills: list[dict],
) -> str:
    regime_note = ""
    if regime_multiplier is not None and regime_multiplier != 1.0:
        regime_note = f'<div class="score-composite-sub">Regime ×{regime_multiplier:.2f}</div>'

    pill_html = []
    for pill in pills:
        pct = pill.get("pct", 0)
        pill_html.append(
            f"""
            <div class="score-pill">
              <div class="score-pill-label">{_esc(pill["label"])}</div>
              <div class="score-pill-value">{pill["score"]:.0f} / {pill["max"]:.0f}</div>
              <div class="score-pill-bar">
                <div class="score-pill-fill" style="width:{pct:.0f}%"></div>
              </div>
            </div>
            """
        )

    return f"""
    <div class="layout-card">
      <div class="score-strip">
        <div class="score-composite">
          <div class="score-composite-value">{final_score:.1f}</div>
          <div class="score-composite-label">Final score</div>
          {regime_note}
        </div>
        <div class="score-pills">
          {"".join(pill_html)}
        </div>
      </div>
    </div>
    """


def build_scan_summary_html(
    *,
    strategy_label: str,
    summary: dict,
    regime: dict,
    config: VizStrategyConfig,
) -> str:
    tiers = summary.get("tier_counts", {})
    tier_parts = " · ".join(f"{tiers.get(t, 0)} {t}" for t in config.tiers)
    return f"""
    <div class="scan-summary-strip">
      <div class="scan-stat">
        <span>{_esc(strategy_label)} scan</span>
        <strong>{summary.get("universe_size", 0)} tickers</strong>
      </div>
      <div class="scan-stat">
        <span>Eligible</span>
        <strong>{summary.get("eligible_count", 0)}</strong>
      </div>
      <div class="scan-stat">
        <span>Tiers</span>
        <strong>{_esc(tier_parts)}</strong>
      </div>
      <div class="scan-stat">
        <span>Regime</span>
        <strong>{_esc(regime.get("label", "").title())} ×{regime.get("multiplier", 1)}</strong>
      </div>
    </div>
    """


def build_universe_context_html(
    *,
    ticker: str,
    final_score: float,
    tier: str,
    df: pd.DataFrame,
    config: VizStrategyConfig,
) -> str:
    eligible = df[df["eligible"]] if "eligible" in df.columns else df
    median = float(eligible["final_score"].median()) if not eligible.empty else 0.0
    if not eligible.empty and ticker in eligible["ticker"].values:
        rank = (eligible["final_score"] > final_score).sum() + 1
        pct = 100 * (1 - (rank - 1) / len(eligible))
        percentile = f"top {max(1, min(100, int(round(pct))))}%"
    else:
        percentile = "—"
    actionable = df[df["tier"].isin(config.actionable_tiers)] if "tier" in df.columns else df
    actionable_count = len(actionable)
    return f"""
    <div class="layout-card">
      <div class="layout-card-title">Universe context</div>
      <p><strong>{_esc(ticker)}</strong> · Tier <strong>{_esc(tier)}</strong></p>
      <p>Final score: <strong>{final_score:.1f}</strong> vs universe median <strong>{median:.1f}</strong></p>
      <p>Percentile (eligible): <strong>{percentile}</strong></p>
      <p>Actionable names this scan: <strong>{actionable_count}</strong></p>
    </div>
    """


def build_key_insight_html(ticker_data: dict, config: VizStrategyConfig) -> str:
    strengths, watches = rank_factor_insights(ticker_data, config)
    strength_items = "".join(f'<li class="insight-strength">{_esc(s)}</li>' for s in strengths)
    watch_items = "".join(f'<li class="insight-watch">{_esc(w)}</li>' for w in watches)
    strength_block = f"<ul class='insight-list'>{strength_items}</ul>" if strengths else ""
    watch_block = f"<ul class='insight-list'>{watch_items}</ul>" if watches else ""
    return f"""
    <div class="layout-card">
      <div class="layout-card-title">Key insight</div>
      {"<p><strong>Strengths</strong></p>" + strength_block if strength_block else ""}
      {"<p><strong>Watch</strong></p>" + watch_block if watch_block else ""}
      {("<p>No factor highlights available.</p>" if not strength_block and not watch_block else "")}
    </div>
    """


def rank_factor_insights(
    ticker_data: dict,
    config: VizStrategyConfig,
) -> tuple[list[str], list[str]]:
    scores = ticker_data.get("scores") or {}
    ranked: list[tuple[float, str]] = []
    for key in config.score_component_keys:
        comp = scores.get(key)
        if not comp:
            continue
        max_pts = comp.get("max") or 0
        score = comp.get("score") or 0
        if max_pts <= 0:
            continue
        pct = score / max_pts
        label = config.score_labels.get(key, key.replace("_", " ").title())
        ranked.append((pct, f"{label}: {score:.0f}/{max_pts:.0f} ({pct * 100:.0f}%)"))

    ranked.sort(key=lambda item: item[0], reverse=True)
    strengths = [text for _, text in ranked[:2]]

    watches: list[str] = []
    for pct, text in ranked[-2:]:
        if pct < 0.35:
            watches.append(text)
    if not ticker_data.get("eligible"):
        fail = ticker_data.get("eligibility", {}).get("fail_reason")
        if fail:
            watches.append(FILTER_LABELS.get(fail, fail.replace("_", " ").title()))

    return strengths, watches


def score_pills_from_ticker(ticker_data: dict, config: VizStrategyConfig) -> list[dict]:
    scores = ticker_data.get("scores") or {}
    pills = []
    for key in config.score_component_keys:
        comp = scores.get(key)
        if not comp:
            continue
        max_pts = float(comp.get("max") or 0)
        score = float(comp.get("score") or 0)
        pct = (score / max_pts * 100) if max_pts else 0
        pills.append(
            {
                "label": config.score_labels.get(key, key.replace("_", " ").title()),
                "score": score,
                "max": max_pts,
                "pct": pct,
            }
        )
    return pills


def extract_scan_date(report_path: str) -> str:
    parent = Path(report_path).parent.name
    if len(parent) == 10 and parent[4] == "-" and parent[7] == "-":
        return parent
    return "Latest"
