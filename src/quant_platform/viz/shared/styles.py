"""Dashboard styling and chart defaults."""

PLOTLY_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "Inter, system-ui, sans-serif", "size": 12, "color": "#374151"},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "#f9fafb",
    "margin": {"l": 24, "r": 24, "t": 48, "b": 24},
    "title": {"font": {"size": 14, "color": "#111827"}},
    "xaxis": {"gridcolor": "#e5e7eb", "linecolor": "#e5e7eb"},
    "yaxis": {"gridcolor": "#e5e7eb", "linecolor": "#e5e7eb"},
}

DEFAULT_TIER_COLORS = {
    "Tier 1": "#22c55e",
    "Tier 2": "#eab308",
    "Tier 3": "#94a3b8",
    "A": "#22c55e",
    "B": "#eab308",
    "C": "#94a3b8",
    "filtered": "#ef4444",
}

CUSTOM_CSS = """
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 0.75rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    .app-shell {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .app-shell-brand {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }
    .app-shell-sub {
        font-size: 0.75rem;
        color: #6b7280;
        margin: 0;
    }
    .nav-link {
        color: #2563eb;
        font-weight: 600;
        text-decoration: none;
        font-size: 0.9rem;
    }
    .nav-link:hover { text-decoration: underline; }
    .nav-link-active {
        color: #111827;
        font-weight: 700;
        text-decoration: none;
        font-size: 0.9rem;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 2px;
    }
    .breadcrumb {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 0.75rem;
    }
    .breadcrumb a { color: #2563eb; text-decoration: none; font-weight: 600; }
    .breadcrumb a:hover { text-decoration: underline; }

    .layout-card, .company-hero, .scan-summary-strip {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .company-hero { padding: 1.5rem; }
    .hero-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .hero-ticker { font-size: 1.75rem; font-weight: 700; color: #111827; margin: 0; }
    .hero-name { font-size: 0.95rem; color: #6b7280; margin: 0.15rem 0 0 0; }
    .hero-badges { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
    .strategy-badge {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #eff6ff;
        color: #1d4ed8;
    }
    .hero-price-row {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        align-items: baseline;
        margin-bottom: 0.75rem;
    }
    .hero-price { font-size: 2rem; font-weight: 700; color: #111827; }
    .hero-change-up { color: #16a34a; font-weight: 600; font-size: 0.95rem; }
    .hero-change-down { color: #dc2626; font-weight: 600; font-size: 0.95rem; }
    .hero-stat { font-size: 0.8rem; color: #6b7280; }
    .hero-stat strong { display: block; font-size: 0.95rem; color: #111827; font-weight: 600; }
    .hero-insight {
        background: #f0f9ff;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        color: #0c4a6e;
        margin-top: 0.5rem;
    }

    .score-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: stretch;
    }
    .score-composite {
        flex: 0 0 180px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .score-composite-value { font-size: 2.25rem; font-weight: 700; color: #111827; line-height: 1; }
    .score-composite-label { font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem; }
    .score-composite-sub { font-size: 0.75rem; color: #9ca3af; margin-top: 0.35rem; }
    .score-pills {
        flex: 1;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 0.65rem;
    }
    .score-pill {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.65rem 0.75rem;
    }
    .score-pill-label { font-size: 0.72rem; color: #6b7280; margin-bottom: 0.2rem; }
    .score-pill-value { font-size: 0.95rem; font-weight: 700; color: #111827; }
    .score-pill-bar {
        background: #e5e7eb;
        border-radius: 4px;
        height: 5px;
        margin-top: 0.4rem;
        overflow: hidden;
    }
    .score-pill-fill {
        background: #2563eb;
        height: 5px;
        border-radius: 4px;
    }

    .scan-summary-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 1.25rem;
        align-items: center;
    }
    .scan-stat strong { font-size: 1.1rem; color: #111827; }
    .scan-stat span { font-size: 0.75rem; color: #6b7280; display: block; }

    .layout-card h4, .layout-card-title {
        margin: 0 0 0.75rem 0;
        font-size: 0.95rem;
        font-weight: 700;
        color: #111827;
    }
    .insight-list { margin: 0.5rem 0 0 0; padding-left: 1.1rem; font-size: 0.9rem; }
    .insight-strength { color: #166534; }
    .insight-watch { color: #b45309; }

    .filter-bar-label { font-size: 0.75rem; color: #6b7280; font-weight: 600; text-transform: uppercase; }

    .tier-badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .pass-badge { color: #166534; font-weight: 600; }
    .fail-badge { color: #991b1b; font-weight: 600; }
    .component-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }
    a.ticker-link {
        color: #2563eb;
        font-weight: 600;
        text-decoration: none;
    }
    a.ticker-link:hover { text-decoration: underline; color: #1d4ed8; }

    div[data-testid="stMetric"] {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
    }
    .news-card {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        background: #fff;
    }
    .news-card-meta { font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem; }

    div[data-testid="stTabs"] button { font-weight: 600; }
</style>
"""

PRICE_LAYOUT_CSS = """
<style>
    [data-testid="stSidebar"] { display: none; }
</style>
"""


def tier_badge_styles(config) -> dict[str, str]:
    colors = {**DEFAULT_TIER_COLORS, **config.tier_colors}
    css = {}
    for tier, hex_color in colors.items():
        if tier == "filtered":
            css[tier] = "background:#fee2e2;color:#991b1b;"
        elif tier in ("Tier 1", "A"):
            css[tier] = "background:#dcfce7;color:#166534;"
        elif tier in ("Tier 2", "B"):
            css[tier] = "background:#fef9c3;color:#854d0e;"
        else:
            css[tier] = "background:#f1f5f9;color:#475569;"
    return css
