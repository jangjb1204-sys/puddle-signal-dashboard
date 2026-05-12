from __future__ import annotations

from calendar import Calendar, month_name
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
SCAN_DIR = APP_DIR / "signal_scans"
THREADS_URL = "https://www.threads.net/@30s_tech_j"
CACHE_TTL_SECONDS = 60

st.set_page_config(
    page_title="Puddle Signal Scanner",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: #03050a !important;
    color: #f5f5f7 !important;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(circle at 12% 0%, rgba(40,92,160,0.18), transparent 30%),
        radial-gradient(circle at 88% 2%, rgba(50,105,190,0.10), transparent 28%),
        linear-gradient(180deg, rgba(255,255,255,0.02), transparent 38%);
    opacity: .9;
}
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"], [data-testid="collapsedControl"] { display:none!important; visibility:hidden!important; height:0!important; }
.block-container { max-width: 1380px; padding: 4.6rem 3.2rem 3rem !important; position: relative; z-index: 1; }
.hero { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; margin-bottom:2.7rem; }
.title-wrap h1 { margin:0; font-size:2.95rem; line-height:1.04; font-weight:760; letter-spacing:-0.055em; color:#f5f5f7; }
.title-row { display:flex; align-items:center; gap:14px; }
.status-dot { width:9px; height:9px; border-radius:999px; background:#63f29d; box-shadow:0 0 18px rgba(99,242,157,.42); }
.updated { margin-top:2.1rem; color:#8e8e93; font-size:.76rem; font-weight:760; letter-spacing:.06em; text-transform:uppercase; }
.updated strong { margin-left:8px; color:#b7bcc7; font-family:'DM Mono', monospace; font-weight:500; }
.top-stats { display:flex; align-items:center; gap:12px; color:#8e8e93; font-size:.82rem; margin-top:.35rem; white-space:nowrap; }
.blue-dot { width:8px; height:8px; border-radius:999px; background:#2f70dc; box-shadow:0 0 16px rgba(47,112,220,.45); }
.top-stats strong { color:#f5f5f7; }
.section-label { color:#8e8e93; font-size:.78rem; font-weight:760; letter-spacing:.055em; text-transform:uppercase; margin:1.9rem 0 .85rem; }
.divider { height:1px; background:rgba(255,255,255,.08); margin:2.2rem 0 2rem; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-top:1.1rem; }
.summary-item { border-top:1px solid rgba(255,255,255,.08); padding-top:1.35rem; min-height:105px; }
.summary-item .label { color:#8e8e93; font-size:.75rem; font-weight:760; letter-spacing:.055em; text-transform:uppercase; }
.summary-item .value { margin-top:.5rem; font-family:'DM Mono', monospace; font-size:2.05rem; color:#f5f5f7; line-height:1; }
.summary-item .hint { margin-top:.5rem; color:#777b84; font-size:.82rem; }
.panel-title { display:flex; align-items:center; gap:12px; color:#f5f5f7; font-weight:760; font-size:1.05rem; margin:1.3rem 0 .9rem; }
.chev { color:#f5f5f7; font-size:1.4rem; line-height:1; }
.stage-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:1rem 0 1.4rem; }
.stage { border:1px solid rgba(255,255,255,.075); border-radius:22px; padding:16px 17px; background:rgba(255,255,255,.022); }
.stage .name { color:#e9ebef; font-weight:760; font-size:.95rem; }
.stage .count { margin-top:.45rem; font-family:'DM Mono', monospace; color:#f5f5f7; font-size:1.45rem; }
.stage .desc { margin-top:.35rem; color:#777b84; font-size:.78rem; }
.calendar-head { display:flex; align-items:center; justify-content:space-between; gap:14px; margin:.2rem 0 .9rem; }
.calendar-title { color:#f5f5f7; font-size:1.08rem; font-weight:760; text-align:center; }
.calendar-grid-static { display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:8px; margin-bottom:.45rem; }
.calendar-dow { color:#777b84; text-align:center; font-size:.68rem; font-weight:760; letter-spacing:.05em; text-transform:uppercase; padding:.25rem 0; }
.calendar-empty { min-height:46px; border:1px solid rgba(255,255,255,.045); border-radius:15px; background:rgba(255,255,255,.012); color:rgba(245,245,247,.16); display:flex; align-items:center; justify-content:center; font-family:'DM Mono', monospace; font-size:.8rem; }
.calendar-empty.out { opacity:.28; }
.filter-label { color:#777b84; font-size:.72rem; font-weight:760; letter-spacing:.05em; text-transform:uppercase; margin:0 0 .42rem .15rem; }
.stButton > button, div[data-testid="stDownloadButton"] button { border-radius:999px!important; border:1px solid rgba(255,255,255,.08)!important; background:rgba(255,255,255,.035)!important; color:#f5f5f7!important; min-height:36px!important; padding:0 13px!important; font-size:.78rem!important; font-weight:720!important; font-family:'DM Sans', sans-serif!important; }
.stButton > button[kind="primary"] { background:#d8dde6!important; color:#111318!important; border-color:#d8dde6!important; }
div[data-testid="stDownloadButton"] button { min-height:44px!important; font-size:.82rem!important; margin-top:.8rem!important; }
.signal-table-wrap { margin-top: 1rem; border-top:1px solid rgba(255,255,255,.08); padding-top:1.2rem; overflow-x:auto; }
.signal-table { width:100%; border-collapse:collapse; min-width:920px; font-family:'DM Sans', sans-serif; }
.signal-table thead th { padding:13px 14px; text-align:left; color:#8e8e93; font-size:.72rem; font-weight:760; letter-spacing:.055em; text-transform:uppercase; border-bottom:1px solid rgba(255,255,255,.075); background:#05070d; }
.signal-table tbody td { padding:14px; color:#e9ebef; font-size:.88rem; font-weight:560; border-bottom:1px solid rgba(255,255,255,.055); background:#05070d; vertical-align:middle; }
.signal-table tbody tr:hover td { background:#0b0f18; }
.signal-table .ticker { font-family:'DM Mono', monospace; color:#f5f5f7; font-weight:500; }
.signal-table .num { font-family:'DM Mono', monospace; color:#d7dce5; font-weight:500; white-space:nowrap; }
.signal-table .muted { color:#8e8e93; }
.signal-badge { display:inline-flex; align-items:center; border-radius:999px; padding:5px 10px; font-size:.76rem; font-weight:760; border:1px solid rgba(255,255,255,.09); background:rgba(255,255,255,.045); color:#e9ebef; white-space:nowrap; }
.signal-badge.strong { background:rgba(255,107,122,.12); color:#ffb6bf; border-color:rgba(255,107,122,.22); }
.type-badge { color:#9fb6d9; font-size:.78rem; font-weight:720; }
.puddle-text { color:#b7bcc7; max-width:330px; }
.empty-note { color:#8e8e93; padding:1.2rem 0; }
.creator-footer { margin:2.8rem 0 .4rem; }
.creator-footer a { color:rgba(245,245,247,.34); font-family:'DM Sans', sans-serif; font-size:1rem; font-weight:650; text-decoration:none!important; }
.creator-footer a:hover { color:rgba(245,245,247,.58); }
@media (max-width:900px){ .block-container{padding:3.4rem 1.5rem 2.4rem!important;} .hero{display:block;} .top-stats{margin-top:1.2rem;} .summary-grid,.stage-strip{grid-template-columns:repeat(2,minmax(0,1fr));} .title-wrap h1{font-size:2.45rem;} }
@media (max-width:640px){ .summary-grid,.stage-strip{grid-template-columns:1fr;} .title-wrap h1{font-size:2.05rem;} .calendar-grid-static{gap:5px}.calendar-empty{min-height:39px;border-radius:12px;font-size:.76rem;} }
</style>
"""

@st.cache_data(show_spinner=False, ttl=CACHE_TTL_SECONDS)
def list_scan_files() -> pd.DataFrame:
    rows = []
    if not SCAN_DIR.exists():
        return pd.DataFrame(columns=["date", "path", "filename"])
    for path in sorted(SCAN_DIR.glob("signal_scan_*.csv")):
        raw = path.stem.replace("signal_scan_", "")
        try:
            scan_date = pd.to_datetime(raw, format="%Y%m%d").date()
        except Exception:
            continue
        rows.append({"date": scan_date, "path": str(path), "filename": path.name, "mtime_ns": path.stat().st_mtime_ns})
    return pd.DataFrame(rows).sort_values("date") if rows else pd.DataFrame(columns=["date", "path", "filename", "mtime_ns"])

@st.cache_data(show_spinner=False, ttl=CACHE_TTL_SECONDS)
def load_scan_csv(path: str, mtime_ns: int | None = None) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    for col in ["close", "change_pct", "rsi"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    return df

def parse_stage(puddle) -> str:
    text = str(puddle or "")
    for stage in ["4th", "3rd", "2nd", "1st"]:
        if text.startswith(stage):
            return stage
    return "Other"

def safe_num(value, suffix="") -> str:
    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return "--"

def calendar_weeks(selected_month):
    cal = Calendar(firstweekday=6)
    yield from cal.monthdatescalendar(selected_month.year, selected_month.month)

def render_calendar_header() -> str:
    cells = [f"<div class='calendar-dow'>{day}</div>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]]
    return f"<div class='calendar-grid-static'>{''.join(cells)}</div>"

def render_empty_calendar_cell(day, selected_month) -> str:
    classes = ["calendar-empty"]
    if day.month != selected_month.month:
        classes.append("out")
    text = day.day if day.month == selected_month.month else ""
    return f"<div class='{' '.join(classes)}'>{text}</div>"

def render_signal_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='signal-table-wrap'><div class='empty-note'>No signals match the selected filters.</div></div>"
    rows = []
    for _, row in df.iterrows():
        signal = str(row.get("signal", ""))
        strong = "strong" if signal == "RSI & Puddle" else ""
        rank = row.get("rank", "")
        company = row.get("company_name", "")
        rows.append(
            "<tr>"
            f"<td><span class='type-badge'>{escape(str(row.get('asset_type','')))}</span></td>"
            f"<td class='muted'>{escape(str(row.get('universe','')))}</td>"
            f"<td class='num'>{escape(str(rank)) if str(rank).strip() else '--'}</td>"
            f"<td><span class='ticker'>{escape(str(row.get('ticker','')))}</span></td>"
            f"<td>{escape(str(company)) if str(company).strip() else '--'}</td>"
            f"<td><span class='signal-badge {strong}'>{escape(signal)}</span></td>"
            f"<td class='num'>{safe_num(row.get('close'))}</td>"
            f"<td class='num'>{safe_num(row.get('change_pct'), '%')}</td>"
            f"<td class='num'>{safe_num(row.get('rsi'))}</td>"
            f"<td class='puddle-text'>{escape(str(row.get('puddle','')))}</td>"
            "</tr>"
        )
    return """
    <div class='signal-table-wrap'>
      <table class='signal-table'>
        <thead><tr><th>Type</th><th>Universe</th><th>Rank</th><th>Ticker</th><th>Company</th><th>Signal</th><th>Close</th><th>Change</th><th>RSI</th><th>Puddle</th></tr></thead>
        <tbody>
    """ + "".join(rows) + "</tbody></table></div>"

def chip_filter(label: str, options: list[str], key: str) -> str:
    if key not in st.session_state or st.session_state[key] not in options:
        st.session_state[key] = options[0]
    st.markdown(f"<div class='filter-label'>{label}</div>", unsafe_allow_html=True)
    cols = st.columns([1] * len(options), gap="small")
    for idx, option in enumerate(options):
        with cols[idx]:
            if st.button(option, key=f"{key}-{option}", type="primary" if st.session_state[key] == option else "secondary"):
                st.session_state[key] = option
                st.rerun()
    return st.session_state[key]

def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    file_df = list_scan_files()
    if file_df.empty:
        st.markdown("<div class='title-wrap'><h1>Puddle Signal Scanner</h1></div>", unsafe_allow_html=True)
        st.info("signal_scans 폴더에 CSV가 아직 없습니다.")
        return

    latest_date = file_df["date"].max()
    if "selected_scan_date" not in st.session_state:
        st.session_state.selected_scan_date = latest_date
    selected_date = st.session_state.selected_scan_date
    if selected_date not in set(file_df["date"].tolist()):
        selected_date = latest_date
        st.session_state.selected_scan_date = latest_date

    month_options = sorted({d.replace(day=1) for d in file_df["date"]})
    current_month = st.session_state.get("calendar_month", selected_date.replace(day=1))
    if current_month not in month_options:
        current_month = selected_date.replace(day=1)
    current_idx = month_options.index(current_month)

    selected_row = file_df[file_df["date"] == selected_date].iloc[-1]
    df = load_scan_csv(selected_row["path"], int(selected_row.get("mtime_ns", 0)))

    scan_time = "--"
    if not df.empty and "scan_timestamp_utc" in df.columns:
        times = df["scan_timestamp_utc"].dropna()
        if not times.empty:
            scan_time = str(times.iloc[0])[11:16]

    total = len(df)
    rsi_puddle = int((df.get("signal") == "RSI & Puddle").sum()) if not df.empty and "signal" in df.columns else 0
    stocks = int((df.get("asset_type") == "Stock").sum()) if not df.empty and "asset_type" in df.columns else 0
    etfs = int((df.get("asset_type") == "ETF").sum()) if not df.empty and "asset_type" in df.columns else 0

    st.markdown(f"""
    <div class='hero'>
      <div class='title-wrap'>
        <div class='title-row'><span class='status-dot'></span><h1>Puddle Signal Scanner</h1></div>
        <div class='updated'>UPDATED <strong>{scan_time}</strong></div>
      </div>
      <div class='top-stats'><span class='blue-dot'></span><span>Selected <strong>{selected_date}</strong></span><span>·</span><span>Total <strong>{total}</strong></span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Saved dates</div>", unsafe_allow_html=True)
    nav_cols = st.columns([1, 5, 1])
    with nav_cols[0]:
        if st.button("‹", disabled=current_idx <= 0, key="prev-month"):
            st.session_state.calendar_month = month_options[current_idx - 1]
            st.rerun()
    with nav_cols[1]:
        st.markdown(f"<div class='calendar-head'><div class='calendar-title'>{month_name[current_month.month]} {current_month.year}</div></div>", unsafe_allow_html=True)
    with nav_cols[2]:
        if st.button("›", disabled=current_idx >= len(month_options) - 1, key="next-month"):
            st.session_state.calendar_month = month_options[current_idx + 1]
            st.rerun()

    st.markdown(render_calendar_header(), unsafe_allow_html=True)
    available_dates = set(file_df["date"].tolist())
    for week_index, week in enumerate(calendar_weeks(current_month)):
        cols = st.columns(7, gap="small")
        for col_index, day in enumerate(week):
            with cols[col_index]:
                if day in available_dates:
                    if st.button(str(day.day), key=f"calendar-{day.isoformat()}", type="primary" if day == selected_date else "secondary", use_container_width=True):
                        st.session_state.selected_scan_date = day
                        st.rerun()
                else:
                    st.markdown(render_empty_calendar_cell(day, current_month), unsafe_allow_html=True)

    st.markdown("<div class='summary-grid'>" +
        f"<div class='summary-item'><div class='label'>Signals</div><div class='value'>{total}</div><div class='hint'>Puddle + RSI & Puddle</div></div>" +
        f"<div class='summary-item'><div class='label'>RSI & Puddle</div><div class='value'>{rsi_puddle}</div><div class='hint'>stronger warning</div></div>" +
        f"<div class='summary-item'><div class='label'>Stocks</div><div class='value'>{stocks}</div><div class='hint'>S&P500 + NASDAQ100</div></div>" +
        f"<div class='summary-item'><div class='label'>ETFs</div><div class='value'>{etfs}</div><div class='hint'>representative set</div></div>" +
        "</div>", unsafe_allow_html=True)

    if not df.empty:
        df["_stage"] = df.get("puddle", pd.Series(dtype=str)).apply(parse_stage)
        counts = df["_stage"].value_counts().to_dict()
        st.markdown("<div class='panel-title'><span class='chev'>›</span><span>Puddle Overview</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='stage-strip'>" +
            f"<div class='stage'><div class='name'>1st · MA20</div><div class='count'>{counts.get('1st',0)}</div><div class='desc'>short-term break</div></div>" +
            f"<div class='stage'><div class='name'>2nd · MA60</div><div class='count'>{counts.get('2nd',0)}</div><div class='desc'>mid-term break</div></div>" +
            f"<div class='stage'><div class='name'>3rd · MA120</div><div class='count'>{counts.get('3rd',0)}</div><div class='desc'>longer trend warning</div></div>" +
            f"<div class='stage'><div class='name'>4th · MA200</div><div class='count'>{counts.get('4th',0)}</div><div class='desc'>MA200 + RSI</div></div>" +
            "</div>", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Filter</div>", unsafe_allow_html=True)
    filter_cols = st.columns([1.2, 1.8, 3.4])
    with filter_cols[0]:
        type_filter = chip_filter("Type", ["Stock", "ETF"], "type_filter")
    with filter_cols[1]:
        signal_filter = chip_filter("Signal", ["RSI & Puddle", "Puddle"], "signal_filter")

    filtered = df.copy()
    if "asset_type" in filtered.columns:
        filtered = filtered[filtered["asset_type"] == type_filter]
    if "signal" in filtered.columns:
        filtered = filtered[filtered["signal"] == signal_filter]

    st.markdown("<div class='panel-title'><span class='chev'>›</span><span>Signal List</span></div>", unsafe_allow_html=True)
    st.markdown(render_signal_table(filtered), unsafe_allow_html=True)
    st.download_button("Download selected CSV", data=filtered.drop(columns=["_stage"], errors="ignore").to_csv(index=False).encode("utf-8"), file_name=selected_row["filename"], mime="text/csv", use_container_width=True)
    st.markdown(f"<div class='creator-footer'><a href='{THREADS_URL}' target='_blank' rel='noopener'>by 30s_tech_j</a></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
