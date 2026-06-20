"""Dashboard styling and chart defaults."""

PLOTLY_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "system-ui, sans-serif", "size": 12, "color": "#334155"},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {"l": 24, "r": 24, "t": 48, "b": 24},
    "title": {"font": {"size": 14, "color": "#0f172a"}},
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
    .block-container { padding-top: 1.5rem; max-width: 1400px; }
    .scan-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        color: #f8fafc;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .scan-header h1 { color: #f8fafc !important; margin: 0; font-size: 1.6rem; }
    .scan-header p { color: #cbd5e1; margin: 0.25rem 0 0 0; font-size: 0.95rem; }
    .info-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
    }
    .info-card h4 { margin: 0 0 0.5rem 0; color: #0f172a; font-size: 0.95rem; }
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
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
    }
    a.ticker-link {
        color: #2563eb;
        font-weight: 600;
        text-decoration: none;
    }
    a.ticker-link:hover {
        text-decoration: underline;
        color: #1d4ed8;
    }
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
