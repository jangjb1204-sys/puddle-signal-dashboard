from __future__ import annotations

from calendar import month_name
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
SCAN_DIR = APP_DIR / "signal_scans"

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
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"], [data-testid="collapsedControl"] {
    display:none!important; visibility:hidden!important; height:0!important;
}
.block-container {
    max-width: 1380px;
    padding: 4.6rem 3.2rem 3rem !important;
    position: relative;
    z-index: 1;
}
.hero {
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:24px;
    margin-bottom:2.7rem;
}
.title-wrap h1 {
    margin:0;
    font-size:2.95rem;
    line-height:1.04;
    font-weight:760;
    letter-spacing:-0.055em;
    color:#f5f5f7;
}
.title-row { display:flex; align-items:center; gap:14px; }
.status-dot { width:9px; height:9px; border-radius:999px; background:#63f29d; box-shadow:0 0 18px rgba(99,242,157,.42); }
.subtle { color:#8e8e93; font-size:.88rem; font-weight:600; letter-spacing:.01em; }
.updated { margin-top:2.1rem; color:#8e8e93; font-size:.76rem; font-weight:760; letter-spacing:.06em; text-transform:uppercase; }
.updated strong { margin-left:8px; color:#b7bcc7; font-family:'DM Mono', monospace; font-weight:500; }
.top-stats { display:flex; align-items:center; gap:12px; color:#8e8e93; font-size:.82rem; margin-top:.35rem; white-space:nowrap; }
.blue-dot { width:8px; height:8px; border-radius:999px; background:#2f70dc; box-shadow:0 0 16px rgba(47,112,220,.45); }
.top-stats strong { color:#f5f5f7; }
.section-label { color:#8e8e93; font-size:.78rem; font-weight:760; letter-spacing:.055em; text-transform:uppercase; margin:1.9rem 0 .85rem; }
.chip-row { display:flex; gap:9px; flex-wrap:wrap; align-items:center; }
.chip {
    display:inline-flex; align-items:center; justify-content:center;
    min-height:47px; padding:0 20px;
    border:1px solid rgba(255,255,255,.08);
    border-radius:999px;
    background:rgba(255,255,255,.035);
    color:#f5f5f7;
    font-size:.86rem;
    font-weight:740;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
}
.chip.active { background:#d8dde6; color:#111318; border-color:#d8dde6; }
.chip.muted { color:#a0a4ad; }
.divider { height:1px; background:rgba(255,255,255,.08); margin:2.2rem 0 2rem; }
.summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-top:1.1rem; }
.summary-item { border-top:1px solid rgba(255,255,255,.08); padding-top:1.35rem; min-height:105px; }
.summary-item .label { color:#8e8e93; font-size:.75rem; font-weight:760; letter-spacing:.055em; text-transform:uppercase; }
.summary-item .value { margin-top:.5rem; font-family:'DM Mono', monospace; font-size:2.05rem; color:#f5f5f7; line-height:1; }
.summary-item .hint { margin-top:.5rem; color:#777b84; font-size:.82rem; }
.panel-title { display:flex; align-items:center; gap:12px; color:#f5f5f7; font-weight:760; font-size:1.05rem; margin:1.3rem 0 .9rem; }
.chev { color:#f5f5f7; font-size:1.4rem; line-height:1; }
.stage-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:1rem 0 1.4rem; }
.stage { border:1px solid rgba(255,255,255,.075); border-radius:22px; padding:16px 17px; background:rgba(255,255,255,.025); }
.stage .name { color:#e9ebef; font-weight:760; font-size:.95rem; }
.stage .count { margin-top:.45rem; font-family:'DM Mono', monospace; color:#f5f5f7; font-size:1.45rem; }
.stage .desc { margin-top:.35rem; color:#777b84; font-size:.78rem; }
div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label { color:#8e8e93!important; font-size:.78rem!important; font-weight:760!important; letter-spacing:.055em; text-transform:uppercase; }
div[data-baseweb="select"] > div, div[data-testid="stTextInput"] [data-baseweb="input"] {
    background:#e9edf5!important;
    border:0!important;
    border-radius:14px!important;
    min-height:60px!important;
    box-shadow:none!important;
}
div[data-baseweb="select"] span { color:#16191f!important; font-weight:720!important; }
div[data-testid="stTextInput"] input { color:#16191f!important; font-weight:650!important; }
.stButton > button {
    border-radius:999px!important;
    border:1px solid rgba(255,255,255,.08)!important;
    background:rgba(255,255,255,.035)!important;
    color:#f5f5f7!important;
    min-height:46px!important;
    font-weight:740!important;
}
.stButton > button[kind="primary"] { background:#d8dde6!important; color:#111318!important; border-color:#d8dde6!important; }
div[data-testid="stDataFrame"] { border-top:1px solid rgba(255,255,255,.08); padding-top:1.2rem; }
.download-wrap { margin-top:1rem; }
@media (max-width:900px){
    .block-container{padding:3.4rem 1.5rem 2.4rem!important;}
    .hero{display:block;}
    .top-stats{margin-top:1.2rem;}
    .summary-grid,.stage-strip{grid-template-columns:repeat(2,minmax(0,1fr));}
    .title-wrap h1{font-size:2.45rem;}
}
@media (max-width:640px){
    .summary-grid,.stage-strip{grid-template-columns:1fr;}
    .title-wrap h1{font-size:2.05rem;}
}
</style>
"""

@st.cache_data(show_spinner=False)
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
        rows.append({"date": scan_date, "path": str(path), "filename": path.name})
    return pd.DataFrame(rows).sort_values("date") if rows else pd.DataFrame(columns=["date", "path", "filename"])

@st.cache_data(show_spinner=False)
def load_scan_csv(path: str) -> pd.DataFrame:
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

def prepare_display_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    preferred = ["asset_type", "universe", "ticker", "signal", "close", "change_pct", "rsi", "puddle", "date"]
    out = out[[c for c in preferred if c in out.columns]]
    out = out.rename(columns={
        "asset_type": "Type", "universe": "Universe", "ticker": "Ticker", "signal": "Signal",
        "close": "Close", "change_pct": "Change %", "rsi": "RSI", "puddle": "Puddle", "date": "Price Date"
    })
    for col in ["Close", "Change %", "RSI"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
    return out

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

    selected_row = file_df[file_df["date"] == selected_date].iloc[-1]
    df = load_scan_csv(selected_row["path"])

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
    month_options = sorted({d.replace(day=1) for d in file_df["date"]}, reverse=True)
    selected_month = st.selectbox("Month", month_options, format_func=lambda d: f"{d.year}. {d.month:02d}")
    month_days = file_df[file_df["date"].apply(lambda d: d.year == selected_month.year and d.month == selected_month.month)].sort_values("date", ascending=False)
    cols = st.columns(min(8, max(1, len(month_days))))
    for idx, (_, row) in enumerate(month_days.iterrows()):
        day = row["date"]
        if cols[idx % len(cols)].button(f"{month_name[day.month][:3]} {day.day}", key=f"date-{day.isoformat()}", type="primary" if day == selected_date else "secondary"):
            st.session_state.selected_scan_date = day
            st.rerun()

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
    f1, f2, f3 = st.columns([1, 1, 2.1])
    type_filter = f1.selectbox("Type", ["All", "Stock", "ETF"])
    signal_filter = f2.selectbox("Signal", ["All", "RSI & Puddle", "Puddle"])
    query = f3.text_input("Search", placeholder="Ticker, e.g. AAPL, NVDA, QQQ")

    filtered = df.copy()
    if type_filter != "All" and "asset_type" in filtered.columns:
        filtered = filtered[filtered["asset_type"] == type_filter]
    if signal_filter != "All" and "signal" in filtered.columns:
        filtered = filtered[filtered["signal"] == signal_filter]
    if query and "ticker" in filtered.columns:
        filtered = filtered[filtered["ticker"].str.contains(query.strip(), case=False, na=False)]

    st.markdown("<div class='panel-title'><span class='chev'>›</span><span>Signal List</span></div>", unsafe_allow_html=True)
    st.dataframe(prepare_display_table(filtered), use_container_width=True, hide_index=True, height=560)
    st.download_button("Download selected CSV", data=filtered.drop(columns=["_stage"], errors="ignore").to_csv(index=False).encode("utf-8"), file_name=selected_row["filename"], mime="text/csv", use_container_width=True)

if __name__ == "__main__":
    main()
