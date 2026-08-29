"""Generate self-contained HTML report snapshots under ``reports/generated``."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from ml_pipeline.config import REPO_ROOT

REPORTS_DIR = Path(REPO_ROOT) / "reports" / "generated"


def _esc(value) -> str:
    import html

    return html.escape(str(value))


def write_batch_report(scored: pd.DataFrame, summary: dict, file_stem: str | None = None) -> Path:
    """One lightweight HTML file summarising a scored batch."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = file_stem or f"batch_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    scored = scored.sort_values("churn_probability", ascending=False)
    rows = []
    for _, r in scored.head(50).iterrows():
        pct = f"{r['churn_probability'] * 100:.1f}%"
        rows.append(
            "<tr>"
            f"<td>{_esc(r['customer_id'])}</td>"
            f"<td style='text-align:right'>{_esc(r['tenure'])}</td>"
            f"<td style='text-align:right'>${_esc(r['monthly_charges'])}</td>"
            f"<td>{_esc(r['contract'])}</td>"
            f"<td style='text-align:right' class='{'hot' if r['churn_probability'] >= 0.7 else 'warm' if r['churn_probability'] >= 0.5 else 'cool'}'>"
            f"<b>{pct}</b></td>"
            "</tr>"
        )

    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Churn Score Report</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#09090B;color:#F9FAFB;padding:32px;}}
h1{{font-size:22px;margin:0}} .muted{{color:#9CA3AF;font-size:13px}}
.kpis{{display:flex;gap:16px;margin:24px 0}}
.kpi{{background:#111827;border:1px solid #1F2937;border-radius:12px;padding:12px 18px}}
.kpi b{{display:block;font-size:20px;color:#10B981}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:16px}}
th,td{{padding:8px 12px;border-bottom:1px solid #1F2937;text-align:left}}
th{{color:#9CA3AF;font-size:11px;text-transform:uppercase;letter-spacing:.06em}}
.hot{{color:#EF4444}} .warm{{color:#F59E0B}} .cool{{color:#10B981}}
</style></head><body>
<h1>Churn Score Report</h1>
<div class="muted">{now} · {summary['rows']} rows scored at threshold {summary['threshold']:.3f}</div>
<div class="kpis">
<div class="kpi"><b>{summary['rows']}</b> rows</div>
<div class="kpi"><b>{summary['expected_churners']}</b> expected churners</div>
<div class="kpi"><b style="color:#F9FAFB">{summary['mean_probability'] * 100:.1f}%</b> mean p</div>
<div class="kpi"><b style="color:#EF4444">${summary['expected_annual_loss']:,.0f}</b> annual exposure</div>
</div>
<table><thead><tr><th>Customer</th><th>Tenure</th><th>Monthly</th><th>Contract</th><th>Risk</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
</body></html>"""

    path = REPORTS_DIR / f"{stem}.html"
    path.write_text(html_doc, encoding="utf-8")
    return path