from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


@dataclass
class EmailConfig:
    host: str
    port: int
    user: str
    password: str
    from_addr: str
    to_addrs: list[str]
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> EmailConfig | None:
        to_raw = os.environ.get("EMAIL_TO", "")
        host = os.environ.get("SMTP_HOST", "")
        if not to_raw or not host:
            return None
        return cls(
            host=host,
            port=int(os.environ.get("SMTP_PORT", "587")),
            user=os.environ.get("SMTP_USER", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            from_addr=os.environ.get("EMAIL_FROM", os.environ.get("SMTP_USER", "")),
            to_addrs=[a.strip() for a in to_raw.split(",") if a.strip()],
            use_tls=os.environ.get("SMTP_USE_TLS", "true").lower() != "false",
        )


def get_actionable_tickers(report: dict) -> list[dict]:
    return [t for t in report.get("tickers", []) if t.get("tier") in ("Tier 1", "Tier 2")]


def _get_latest_finance_vibe_html() -> str:
    """Scans the shared volume path for the latest Finance-Vibe logs and formats them."""
    vibe_logs_dir = Path("/app/finance_vibe_data/logs")
    if not vibe_logs_dir.exists():
        return """
        <div style="background-color: #fcf8e3; border: 1px solid #faf2cc; color: #8a6d3b; padding: 12px; border-radius: 4px; font-size: 14px;">
            ⚠️ Finance-Vibe directory not found at volume mount path.
        </div>"""

    # Look for files in the logs directory
    files = [f for f in vibe_logs_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        return "<p style='color: #777; font-style: italic;'>No Finance-Vibe log outputs found for today yet.</p>"

    # Get the single most recent log file to extract contents
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        content = latest_file.read_text(encoding="utf-8").strip()
        # Convert simple line breaks to HTML breaks for safe display
        formatted_content = content.replace("\n", "<br>").replace(" ", "&nbsp;")
        
        return f"""
        <div style="background-color: #1e1e1e; border: 1px solid #333; border-radius: 6px; padding: 15px; margin-top: 10px;">
            <div style="font-size: 12px; color: #aaa; margin-bottom: 8px; font-family: monospace; border-bottom: 1px solid #333; padding-bottom: 4px;">
                SOURCE FILE: {latest_file.name}
            </div>
            <div style="font-family: 'Courier New', Courier, monospace; font-size: 13px; color: #d4d4d4; line-height: 1.5; overflow-x: auto;">
                {formatted_content}
            </div>
        </div>
        """
    except Exception as e:
        return f"<p style='color: #d9534f;'>Error parsing Finance-Vibe file: {str(e)}</p>"


def build_actionable_email(
    report: dict,
    *,
    scan_date: date | None = None,
    archive_dir: Path | None = None,
) -> tuple[str, str]:
    """Return (subject, html_body) for actionable tickers email."""
    scan_date = scan_date or date.today()
    summary = report["scan_summary"]
    regime = report["market_regime"]
    tiers = summary["tier_counts"]
    actionable = get_actionable_tickers(report)

    subject = (
        f"🎯 Quant Stack Report {scan_date:%Y-%m-%d}: "
        f"{len(actionable)} Actionable "
        f"({tiers['Tier 1']} T1, {tiers['Tier 2']} T2)"
    )

    rows_html = ""
    for t in sorted(actionable, key=lambda x: x["summary"]["final_adjusted_score"], reverse=True):
        s = t["summary"]
        scores = t.get("scores") or {}
        rs = scores.get("rs_market", {}).get("score", "-")
        comp = scores.get("compression", {}).get("score", "-")
        vol = scores.get("relative_volume", {}).get("score", "-")
        
        # 1. Interactive Hyperlink Conversion
        ticker = t['ticker']
        tv_link = f"https://www.tradingview.com/chart/?symbol={ticker}"
        ticker_cell = f'<a href="{tv_link}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: bold;">{ticker} ↗</a>'
        
        # 2. Modern Color-Coded Badges
        if t['tier'] == "Tier 1":
            tier_badge = '<span style="background-color: #022c22; color: #4ade80; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #064e3b;">Tier 1</span>'
        else:
            tier_badge = '<span style="background-color: #3f2d06; color: #fbbf24; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #78350f;">Tier 2</span>'

        rows_html += f"""
        <tr style="border-bottom: 1px solid #2d2d2d;">
          <td style="padding: 12px; font-size: 14px;">{ticker_cell}</td>
          <td style="padding: 12px;">{tier_badge}</td>
          <td style="padding: 12px; font-size: 14px; font-weight: bold; color: #e2e8f0;">{s.get('final_adjusted_score', 0):.1f}</td>
          <td style="padding: 12px; font-size: 14px; color: #94a3b8;">{t.get('sector_etf', '')}</td>
          <td style="padding: 12px; font-size: 14px; color: #e2e8f0;">{rs}</td>
          <td style="padding: 12px; font-size: 14px; color: #e2e8f0;">{comp}</td>
          <td style="padding: 12px; font-size: 14px; color: #e2e8f0;">{vol}</td>
          <td style="padding: 12px; font-size: 13px; color: #cbd5e1; max-width: 300px;">{t.get('tier_reason', '')}</td>
        </tr>"""

    if not rows_html:
        rows_html = '<tr><td colspan="8" style="padding: 20px; text-align: center; color: #94a3b8; font-style: italic;">No actionable breakout tickers today (Tier 1 or Tier 2).</td></tr>'

    archive_note = f"<p style='color: #94a3b8; font-size: 13px;'>🗄️ Archived to: <code style='background: #2d2d2d; padding: 2px 6px; border-radius: 4px; color: #f1f5f9;'>{archive_dir}</code></p>" if archive_dir else ""

    # Fetch the embedded Finance Vibe updates
    finance_vibe_section = _get_latest_finance_vibe_html()

    html = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 1000px; margin: 0 auto; background-color: #1e293b; border-radius: 8px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);">
            
            <div style="border-bottom: 2px solid #334155; padding-bottom: 16px; margin-bottom: 24px;">
                <h2 style="margin: 0 0 8px 0; color: #f1f5f9; font-size: 24px; font-weight: 700;">📈 Automated Market Intelligence Dashboard</h2>
                <div style="font-size: 14px; color: #94a3b8;">Run Date: <span style="color: #f1f5f9; font-weight: bold;">{scan_date:%A, %B %d, %Y}</span></div>
            </div>

            <div style="margin-bottom: 24px; background-color: #0f172a; border-radius: 6px; padding: 16px; border: 1px solid #334155;">
                <h4 style="margin: 0 0 10px 0; color: #94a3b8; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em;">Market Environment Profile</h4>
                <div style="font-size: 15px; line-height: 1.6;">
                    Regime Baseline: <span style="color: #38bdf8; font-weight: bold;">{regime['label'].title()} (×{regime['multiplier']})</span><br>
                    SPY Close: <span style="color: #e2e8f0; font-weight: bold;">${regime['spy_price']}</span> &nbsp;|&nbsp; 
                    63-Day Rolling Return: <span style="color: { '#4ade80' if float(regime['return_63d_pct']) >= 0 else '#f87171' }; font-weight: bold;">{regime['return_63d_pct']}%</span>
                </div>
                <div style="font-size: 13px; color: #64748b; margin-top: 8px; border-top: 1px solid #1e293b; padding-top: 8px;">
                    Universe Baseline: {summary['universe_size']} scanned &bull; {summary['eligible_count']} eligible filters &bull; {len(actionable)} signaling breakout profiles
                </div>
                {archive_note}
            </div>

            <div style="margin-bottom: 32px;">
                <h3 style="margin: 0 0 12px 0; color: #38bdf8; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
                    ⚡ Breakout Execution Scans (Quant-Scanner)
                </h3>
                <div style="overflow-x: auto; border: 1px solid #334155; border-radius: 6px; background-color: #0f172a;">
                    <table cellspacing="0" cellpadding="0" style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead>
                            <tr style="background-color: #1e293b; border-bottom: 2px solid #334155; color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;">
                                <th style="padding: 12px;">Ticker</th>
                                <th style="padding: 12px;">Classification</th>
                                <th style="padding: 12px;">Composite</th>
                                <th style="padding: 12px;">ETF Group</th>
                                <th style="padding: 12px;">RS Mkt</th>
                                <th style="padding: 12px;">Compress</th>
                                <th style="padding: 12px;">Rel Vol</th>
                                <th style="padding: 12px;">Primary Trigger Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>

            <div style="margin-bottom: 32px; border-top: 2px dashed #334155; padding-top: 24px;">
                <h3 style="margin: 0 0 4px 0; color: #a855f7; font-size: 18px; font-weight: 600;">
                    🎯 Swing Trade Layouts & Tracking (Finance-Vibe)
                </h3>
                <p style="margin: 0 0 12px 0; font-size: 13px; color: #94a3b8;">Workflow logs, pipeline executions, and target levels extracted from production runs.</p>
                {finance_vibe_section}
            </div>

            <div style="background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #e2e8f0; font-size: 14px; font-weight: 600; border-bottom: 1px solid #334155; padding-bottom: 6px;">
                    🔍 Core Technical Component Breakdowns (Top Actionable Profiles)
                </h4>
                {_component_details_html(actionable[:5])}
            </div>

            <div style="margin-top: 24px; border-top: 1px solid #334155; padding-top: 12px; text-align: center; color: #64748b; font-size: 11px; line-height: 1.5;">
                Generated automatically by Core Engine Hub &bull; Running Environment Matrix: Docker Linux container clusters<br>
                <span style="color: #475569;">Tier 1 labels confirm high-probability immediate breakout setups. Tier 2 elements match watchlists parameters. All charts utilize TradingView direct routing.</span>
            </div>

        </div>
    </body>
    </html>
    """
    return subject, html


def _component_details_html(tickers: list[dict]) -> str:
    if not tickers:
        return "<p style='color: #64748b; font-style: italic;'>No component telemetry records to show.</p>"
    parts = []
    for t in tickers:
        lines = [f"<div style='font-size: 14px; margin-bottom: 4px;'><strong style='color: #38bdf8;'>{t['ticker']}</strong> <span style='color: #94a3b8; font-size:12px;'>({t['tier']})</span></div>"]
        scores = t.get("scores") or {}
        for name, comp in scores.items():
            label = name.replace("_", " ").title()
            meaning = comp.get("meaning", "")
            lines.append(
                f"<div style='font-size: 12px; color: #cbd5e1; margin-left: 16px; margin-bottom: 2px;'>"
                f"&bull; <strong style='color: #e2e8f0;'>{label}:</strong> {comp.get('score')}/{comp.get('max')} "
                f"<span style='color: #64748b;'>— {meaning}</span>"
                f"</div>"
            )
        parts.append("<div style='margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed #1e293b;'>" + "".join(lines) + "</div>")
    return "\n".join(parts)


def send_scan_email(
    report: dict,
    *,
    config: EmailConfig | None = None,
    scan_date: date | None = None,
    archive_dir: Path | None = None,
) -> bool:
    """Send actionable tickers email. Returns True if sent."""
    config = config or EmailConfig.from_env()
    if not config:
        return False

    subject, html = build_actionable_email(report, scan_date=scan_date, archive_dir=archive_dir)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.from_addr
    msg["To"] = ", ".join(config.to_addrs)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(config.host, config.port, timeout=30) as server:
        if config.use_tls:
            server.starttls()
        if config.user and config.password:
            server.login(config.user, config.password)
        server.sendmail(config.from_addr, config.to_addrs, msg.as_string())

    return True