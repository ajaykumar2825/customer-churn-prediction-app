"""Global layout: theme CSS, top bar, hero and section helpers."""

from __future__ import annotations

import streamlit as st

_BASE_CSS = """
<style>
:root{
  --bg:#09090B; --panel:#0F1117; --panel-2:#111827; --border:#1E293B;
  --text:#F9FAFB; --muted:#AEB9C7; --muted-2:#64748B;
  --primary:#10B981; --cyan:#06B6D4; --blue:#2563EB; --violet:#8B5CF6;
  --warning:#F59E0B; --danger:#EF4444; --success:#10B981;
}

[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 600px at 80% -10%, rgba(16,185,129,0.07), transparent 50%),
              radial-gradient(1000px 500px at -10% 10%, rgba(37,99,235,0.08), transparent 55%),
              var(--bg);
  color: var(--text);
}
[data-testid="stSidebar"]{ background: #0B0C11; border-right:1px solid rgba(30,41,59,.55); }
[data-testid="stSidebar"] .st-expander{border-color:var(--border);}
[data-testid="stHeader"]{ background:transparent; }
#MainMenu, footer, [data-testid="stToolbar"]{ visibility:hidden; }
[data-testid="stSidebar"]{ visibility:visible; }
.block-container{padding-top:1.1rem; padding-bottom:4rem; max-width:1400px;}

h1,h2,h3{ font-weight:650; letter-spacing:-.01em; }
h1{ font-size:1.9rem!important; }
h2{ font-size:1.25rem!important; color:var(--text); }
p, li{ color:var(--muted); }

div[data-testid="stMetric"]{
  background:linear-gradient(160deg, rgba(17,24,39,.7), rgba(9,9,11,.4));
  border:1px solid var(--border); border-radius:14px; padding:.9rem 1rem;
}
div[data-testid="stMetric"] label{ color:var(--muted); font-size:.78rem; }
div[data-testid="stMetricValue"]{ color:var(--text); font-weight:650; }

/* ---------- Glass panels & cards ---------- */
.glass-panel{
  background:linear-gradient(160deg, rgba(17,24,39,.85), rgba(9,9,11,.55));
  border:1px solid var(--border); border-radius:16px;
  box-shadow:0 1px 2px rgba(2,6,23,.25), 0 8px 24px -16px rgba(2,6,23,.6);
  padding:1.15rem 1.25rem; margin-bottom:1rem;
}
.glass-panel.inset{ background:rgba(9,9,11,.55); }

.metric-row{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:14px 0 22px; }
.metric-row.c3{ grid-template-columns:repeat(3,1fr); }
.metric-row.c5{ grid-template-columns:repeat(5,1fr); }
@media (max-width: 1100px){ .metric-row,.metric-row.c3,.metric-row.c5{ grid-template-columns:repeat(2,1fr);} }

.metric-card{
  position:relative; overflow:hidden;
  background:linear-gradient(160deg, rgba(17,24,39,.85), rgba(9,9,11,.5));
  border:1px solid var(--border); border-radius:14px; padding:.95rem 1.05rem;
}
.metric-chip{ position:absolute; top:10px; right:10px; width:30px; height:30px;
  border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:15px;}
.metric-card .label{ color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em;}
.metric-card .value{ font-size:1.55rem; font-weight:700; color:var(--text); margin:.15rem 0 .1rem; font-variant-numeric:tabular-nums;}
.metric-card .hint{ color:var(--muted-2); font-size:.74rem; }
.metric-card .kpi-delta{ font-size:.75rem; margin-bottom:.15rem; font-weight:600; }

.gradient{ background-image:var(--grad, linear-gradient(135deg,#10B981,#06B6D4)); }

/* ---------- Badges ---------- */
.risk-badge,.churn-badge{
  display:inline-flex; align-items:center; gap:.4rem;
  border:1px solid; border-radius:999px; padding:.18rem .6rem;
  font-size:.72rem; font-weight:700; letter-spacing:.05em; text-transform:uppercase;
  white-space:nowrap;
}
.risk-badge .dot{ width:6px; height:6px; border-radius:99px; display:inline-block;}
.churn-badge{ text-transform:none; letter-spacing:0; font-weight:600; }
.mono{ font-family:JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace; }

.cap-badge{
  display:inline-flex; align-items:center; gap:.4rem;
  border:1px solid rgba(6,182,212,.35); color:#22D3EE;
  background:rgba(6,182,212,.08); border-radius:999px; padding:.22rem .7rem;
  font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
}
.pill-outline{
  display:inline-block; border:1px solid var(--border); border-radius:999px;
  padding:.2rem .7rem; font-size:.72rem; color:var(--muted); font-weight:600;
}

/* ---------- Top bar / hero ---------- */
.topbar{
  display:flex; align-items:center; justify-content:space-between;
  gap:12px; padding:.55rem 0 .6rem; border-bottom:1px solid rgba(30,41,59,.5);
  margin-bottom:1.4rem;
}
.topbar .tagline{ color:var(--muted); font-size:.86rem;}
.topbar .tagline b{ color:var(--text);}
.topbar .right{ display:flex; align-items:center; gap:10px;}
.brand-chip{ display:inline-flex; align-items:center; gap:.4rem; font-size:.74rem;
  color:#22D3EE; border:1px solid rgba(6,182,212,.35); background:rgba(6,182,212,.08);
  border-radius:999px; padding:.2rem .65rem; letter-spacing:.06em; text-transform:uppercase; font-weight:700;}
.pulse{ width:7px; height:7px; border-radius:99px; background:var(--success);
  box-shadow:0 0 0 0 rgba(16,185,129,.7); animation:pulse 2s infinite;}
@keyframes pulse{ 0%{box-shadow:0 0 0 0 rgba(16,185,129,.65);} 70%{box-shadow:0 0 0 8px rgba(16,185,129,0);} 100%{box-shadow:0 0 0 0 rgba(16,185,129,0);} }

.hero{
  position:relative; overflow:hidden; border-radius:20px; padding:2.1rem 2.3rem; margin-bottom:1.5rem;
  background:linear-gradient(120deg, rgba(16,185,129,.12), rgba(6,182,212,.05) 45%, rgba(9,9,11,.2) 100%);
  border:1px solid var(--border);
}
.hero h1{ margin:0 0 .35rem; font-size:2.1rem!important;
  background:linear-gradient(120deg,#fff 0%, #cbd5e1 55%, var(--cyan) 100%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;}
.hero .sub{ color:var(--muted); font-size:.98rem; max-width:760px;}
.hero .meta{ position:absolute; top:1.4rem; right:1.6rem; display:flex; gap:.5rem;}

.section-title{ display:flex; align-items:center; gap:.5rem; margin:1.4rem 0 .6rem;}
.section-title .bar{ width:4px; height:18px; border-radius:99px;
  background:linear-gradient(180deg, var(--primary), var(--cyan));}
.section-title h2{ margin:0; font-size:1.15rem!important;}

/* ---------- Insights / callouts ---------- */
.insight-card{
  border-radius:14px; padding:1rem 1.15rem; margin:1rem 0;
  border:1px solid rgba(6,182,212,.25);
  background:linear-gradient(120deg, rgba(6,182,212,.07), rgba(10,10,14,0) 60%);
}
.insight-card.danger{ border-color:rgba(239,68,68,.3); background:linear-gradient(120deg, rgba(239,68,68,.08), rgba(10,10,14,0) 60%); }
.insight-card .cap{ font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; color:var(--cyan); font-weight:800;}
.insight-card.danger .cap{ color:var(--danger); }
.insight-card p{ margin:.35rem 0 0; color:var(--muted); font-size:.9rem;}
.insight-card b{ color:var(--text);}

/* ---------- Factor list / SHAP ---------- */
.factor-row{
  display:flex; align-items:center; justify-content:space-between;
  padding:.5rem .7rem; border:1px solid var(--border); border-radius:10px; margin-bottom:.4rem;
  background:rgba(9,9,11,.4);
}
.factor-row .name{ color:var(--muted); font-size:.84rem;}
.factor-row .val{ font-family:JetBrains Mono, monospace; font-size:.84rem; font-weight:600;}
.pos{ color:var(--danger);} .neg{ color:var(--success);}

.stat-tile{ background:rgba(9,9,11,.5); border:1px solid var(--border); border-radius:12px; padding:.7rem .9rem;}
.stat-tile .cap{ font-size:.66rem; letter-spacing:.08em; text-transform:uppercase; color:var(--muted-2);}
.stat-tile .val{ font-size:1.02rem; font-weight:650; color:var(--text); margin-top:.15rem; font-variant-numeric:tabular-nums;}
.stat-row{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-top:.8rem;}
@media (max-width:1100px){ .stat-row{ grid-template-columns:repeat(3,1fr);} }

.streamlit-button{ margin-top:.4rem; }
hr{ border-color:rgba(30,41,59,.6);}
[data-testid="stCheckbox"] span{ font-size:.86rem;}
[data-testid="stNumberInput"] input{ color:var(--text);}

/* Dataframe polish */
[data-testid="stDataFrame"]{ border:1px solid var(--border); border-radius:14px; overflow:hidden;}
</style>
"""


def inject_global_css() -> None:
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def render_topbar() -> None:
    st.markdown(
        """
        <div class="topbar">
          <div class="tagline">Churn prediction platform — gradient-boosted · <b>SHAP-explainable</b></div>
          <div class="right">
            <span class="brand-chip"><span class="pulse"></span>model live</span>
            <span class="pill-outline">v1.0.0</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, meta: str | None = None) -> None:
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p class="sub">{subtitle}</p>{meta_html}</div>',
        unsafe_allow_html=True,
    )


def section_title(title: str) -> None:
    st.markdown(
        f'<div class="section-title"><span class="bar"></span><h2>{title}</h2></div>',
        unsafe_allow_html=True,
    )


def insight_caption(caption: str, body_html: str, danger: bool = False) -> None:
    cls = "insight-card danger" if danger else "insight-card"
    st.markdown(
        f'<div class="{cls}"><div class="cap">{caption}</div><p>{body_html}</p></div>',
        unsafe_allow_html=True,
    )


def stat_tiles(items: list[tuple[str, str]]) -> None:
    tiles = "".join(
        f'<div class="stat-tile"><div class="cap">{k}</div><div class="val">{v}</div></div>'
        for k, v in items
    )
    st.markdown(f'<div class="stat-row">{tiles}</div>', unsafe_allow_html=True)