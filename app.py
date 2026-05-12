from __future__ import annotations

from calendar import Calendar, month_name
from datetime import datetime
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
    background:
        linear-gradient(118deg, rgba(182,221,255,0.08) 0%, rgba(182,221,255,0) 34%),
        linear-gradient(212deg, rgba(0,117,255,0.14) 0%, rgba(0,117,255,0) 42%),
        linear-gradient(180deg, #091b31 0%, #061323 42%, #020711 100%) !important;
    color: #f5f5f7 !important;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background:
        linear-gradient(112deg, transparent 0%, rgba(235,247,255,0.13) 18%, transparent 36%),
        linear-gradient(75deg, transparent 52%, rgba(86,154,255,0.10) 72%, transparent 90%);
    opacity: 0.72;
    mix-blend-mode: screen;
}
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1360px;
    position: relative;
    z-index: 1;
}
.app-hero {
    position: relative;
    overflow: hidden;
    margin: 0.2rem 0 1.05rem;
    padding: 1.22rem 1.32rem 1.18rem;
    border: 1px solid rgba(190,220,255,0.24);
    border-radius: 30px;
    background:
        linear-gradient(142deg, rgba(238,248,255,0.21), rgba(117,181,255,0.07) 38%, rgba(255,255,255,0.035) 70%),
        rgba(8,28,50,0.62);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.34),
        inset 0 -1px 0 rgba(255,255,255,0.08),
        0 22px 70px rgba(0,0,0,0.32),
        0 0 0 1px rgba(255,255,255,0.035);
    backdrop-filter: blur(34px) saturate(1.65);
    -webkit-backdrop-filter: blur(34px) saturate(1.65);
}
.app-hero::before {
    content: "";
    position: absolute;
    left: 22px;
    right: 22px;
    top: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.58), transparent);
}
.hero-row {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}
.app-hero h1 {
    margin: 0;
    font-size: 2.42rem !important;
    line-height: 1.08;
    font-weight: 760 !important;
    color: #f7fbff !important;
    text-shadow: 0 12px 34px rgba(0,0,0,0.28);
}
.app-hero p {
    margin: 0.45rem 0 0;
    color: rgba(207,228,255,0.68);
    font-size: 0.9rem;
}
.viewer-pill, .updated-mark, .mini-pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 9px 14px;
    border: 1px solid rgba(190,220,255,0.24);
    border-radius: 999px;
    background:
        linear-gradient(135deg, rgba(231,246,255,0.15), rgba(255,255,255,0.04)),
        rgba(7,24,43,0.56);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.20), 0 14px 38px rgba(0,0,0,0.16);
    color: rgba(226,240,255,0.72);
    font-size: 0.78rem;
    white-space: nowrap;
    backdrop-filter: blur(22px) saturate(1.4);
    -webkit-backdrop-filter: blur(22px) saturate(1.4);
}
.viewer-pill strong, .updated-mark strong, .mini-pill strong { color: #9cccff; font-weight: 750; }
.section-label {
    color: rgba(207,228,255,0.64);
    font-size: 0.8rem;
    font-weight: 700;
    margin: 1.15rem 0 0.48rem;
}
.glass-card {
    position: relative;
    overflow: hidden;
    padding: 16px 17px;
    border: 1px solid rgba(190,220,255,0.17);
    border-radius: 24px;
    background:
        linear-gradient(145deg, rgba(241,248,255,0.14), rgba(255,255,255,0.04) 54%, rgba(117,181,255,0.03)),
        rgba(7,23,42,0.52);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.24),
        inset 0 -1px 0 rgba(255,255,255,0.05),
        0 18px 54px rgba(0,0,0,0.22);
    backdrop-filter: blur(28px) saturate(1.5);
    -webkit-backdrop-filter: blur(28px) saturate(1.5);
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin: 0.75rem 0 1.0rem;
}
.metric-card .label {
    color: rgba(207,228,255,0.60);
    font-size: 0.72rem;
    font-weight: 700;
    margin-bottom: 9px;
}
.metric-card .value {
    font-family: 'DM Mono', monospace;
    font-size: 1.55rem;
    font-weight: 500;
    color: #f7fbff;
}
.metric-card .hint {
    margin-top: 7px;
    color: rgba(207,228,255,0.48);
    font-size: 0.76rem;
}
.signal-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin: 0.6rem 0 1.0rem;
}
.signal-card { min-height: 128px; }
.signal-title {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #f7fbff;
    font-size: 1.02rem;
    font-weight: 750;
    margin-bottom: 9px;
}
.signal-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--accent);
    box-shadow: 0 0 18px color-mix(in srgb, var(--accent) 55%, transparent);
}
.signal-item {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 7px 0;
    border-top: 1px solid rgba(255,255,255,0.08);
    color: rgba(235,244,255,0.86);
    font-size: 0.84rem;
}
.signal-item:first-of-type { border-top: none; }
.signal-date {
    color: rgba(207,228,255,0.56);
    white-space: nowrap;
    font-family: 'DM Mono', monospace;
    font-size: 0.76rem;
}
.calendar-wrap {
    padding: 15px;
}
.calendar-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    gap: 12px;
}
.calendar-title {
    color: #f7fbff;
    font-size: 1.05rem;
    font-weight: 750;
}
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 8px;
}
.calendar-dow {
    color: rgba(207,228,255,0.46);
    text-align: center;
    font-size: 0.68rem;
    font-weight: 750;
    padding: 4px 0;
}
.calendar-day {
    min-height: 42px;
    border: 1px solid rgba(190,220,255,0.13);
    border-radius: 14px;
    background: rgba(7,23,42,0.34);
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(226,240,255,0.36);
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
}
.calendar-day.has-data {
    color: #f7fbff;
    background: linear-gradient(145deg, rgba(156,204,255,0.18), rgba(255,255,255,0.04)), rgba(9,29,52,0.62);
    border-color: rgba(190,220,255,0.24);
    cursor: pointer;
}
.calendar-day.selected {
    background: linear-gradient(145deg, rgba(232,246,255,0.95), rgba(156,204,255,0.76));
    color: #071323;
    border-color: rgba(231,246,255,0.86);
    box-shadow: 0 18px 42px rgba(55,144,255,0.20);
    font-weight: 750;
}
.dataframe-wrap {
    border: 1px solid rgba(190,220,255,0.17);
    border-radius: 24px;
    overflow: hidden;
    background: rgba(7,23,42,0.38);
}
div[data-testid="stDataFrame"] {
    border-radius: 24px !important;
    overflow: hidden !important;
}
div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label {
    color: rgba(207,228,255,0.64) !important;
    font-size: 0.76rem !important;
    font-weight: 650 !important;
}
div[data-baseweb="select"] > div, div[data-testid="stTextInput"] [data-baseweb="input"] {
    background: linear-gradient(135deg, rgba(241,248,255,0.12), rgba(255,255,255,0.035)), rgba(9,28,50,0.72) !important;
    border: 1px solid rgba(190,220,255,0.24) !important;
    border-radius: 18px !important;
    min-height: 46px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 16px 42px rgba(0,0,0,0.14) !important;
}
div[data-baseweb="select"] span, div[data-testid="stTextInput"] input {
    color: #f5f5f7 !important;
    font-weight: 600 !important;
}
.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 1px solid rgba(190,220,255,0.18);
    background: rgba(7,23,42,0.46);
    color: rgba(226,240,255,0.82);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(145deg, rgba(232,246,255,0.95), rgba(156,204,255,0.76));
    color: #071323;
    border-color: rgba(231,246,255,0.86);
    font-weight: 750;
}
@media (max-width: 900px) {
    .metric-grid, .signal-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .app-hero h1 { font-size: 2.0rem !important; }
}
@media (max-width: 640px) {
    .metric-grid, .signal-grid { grid-template-columns: 1fr; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .calendar-grid { gap: 6px; }
    .calendar-day { min-height: 38px; border-radius: 12px; }
}
</style>
"""


@st.cache_data(show_spinner=False)
def list_scan_files() -> pd.DataFrame:
    rows: list[dict] = []
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


def metric_card(label: str, value: str | int, hint: str = "") -> str:
    return f"""
    <div class="glass-card metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="hint">{hint}</div>
    </div>
    """


def parse_stage(puddle: str) -> str:
    text = str(puddle or "")
    if text.startswith("4th"):
        return "4th"
    if text.startswith("3rd"):
        return "3rd"
    if text.startswith("2nd"):
        return "2nd"
    if text.startswith("1st"):
        return "1st"
    return "Other"


def signal_card(title: str, count: int, subtitle: str, accent: str) -> str:
    return f"""
    <div class="glass-card signal-card" style="--accent:{accent};">
        <div class="signal-title"><span class="signal-dot"></span>{title}</div>
        <div class="signal-item"><span>Signals</span><span class="signal-date">{count}</span></div>
        <div class="signal-item"><span>{subtitle}</span><span class="signal-date">active</span></div>
    </div>
    """


def render_calendar(file_df: pd.DataFrame, selected_date) -> object:
    dates = set(file_df["date"].tolist())
    latest = max(dates) if dates else selected_date
    current = selected_date or latest

    month_options = sorted({d.replace(day=1) for d in dates}, reverse=True)
    if not month_options:
        return selected_date

    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = current.replace(day=1)

    selected_month = st.selectbox(
        "Month",
        options=month_options,
        index=month_options.index(st.session_state.calendar_month) if st.session_state.calendar_month in month_options else 0,
        format_func=lambda d: f"{d.year}. {d.month:02d}",
    )
    st.session_state.calendar_month = selected_month

    st.markdown(
        f"""
        <div class="glass-card calendar-wrap">
            <div class="calendar-head">
                <div class="calendar-title">{month_name[selected_month.month]} {selected_month.year}</div>
                <div class="mini-pill"><strong>{len([d for d in dates if d.year == selected_month.year and d.month == selected_month.month])}</strong> saved days</div>
            </div>
            <div class="calendar-grid">
                <div class="calendar-dow">Mon</div><div class="calendar-dow">Tue</div><div class="calendar-dow">Wed</div><div class="calendar-dow">Thu</div><div class="calendar-dow">Fri</div><div class="calendar-dow">Sat</div><div class="calendar-dow">Sun</div>
        """,
        unsafe_allow_html=True,
    )

    cal = Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(selected_month.year, selected_month.month)
    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            in_month = day.month == selected_month.month
            has_data = day in dates
            is_selected = day == selected_date
            label = str(day.day) if in_month else ""
            if has_data and in_month:
                if cols[i].button(label, key=f"day-{day.isoformat()}", type="primary" if is_selected else "secondary"):
                    st.session_state.selected_scan_date = day
                    st.rerun()
            else:
                cols[i].markdown(f"<div class='calendar-day'>{label}</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
    return st.session_state.get("selected_scan_date", selected_date)


def prepare_display_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    preferred = ["asset_type", "universe", "ticker", "signal", "close", "change_pct", "rsi", "puddle", "date"]
    existing = [c for c in preferred if c in out.columns]
    out = out[existing]
    rename = {
        "asset_type": "Type",
        "universe": "Universe",
        "ticker": "Ticker",
        "signal": "Signal",
        "close": "Close",
        "change_pct": "Change %",
        "rsi": "RSI",
        "puddle": "Puddle",
        "date": "Price Date",
    }
    out = out.rename(columns=rename)
    for col in ["Close", "Change %", "RSI"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
    return out


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    file_df = list_scan_files()
    if file_df.empty:
        st.markdown(
            """
            <div class="app-hero"><h1>Puddle Signal Scanner</h1><p>No scan files found yet. Run GitHub Actions first.</p></div>
            """,
            unsafe_allow_html=True,
        )
        st.info("signal_scans 폴더에 CSV가 아직 없습니다.")
        return

    latest_date = file_df["date"].max()
    if "selected_scan_date" not in st.session_state:
        st.session_state.selected_scan_date = latest_date

    selected_date = st.session_state.selected_scan_date
    selected_row = file_df[file_df["date"] == selected_date].iloc[-1]
    df = load_scan_csv(selected_row["path"])

    scan_time = "Unknown"
    if not df.empty and "scan_timestamp_utc" in df.columns:
        scan_time = str(df["scan_timestamp_utc"].dropna().iloc[0]) if not df["scan_timestamp_utc"].dropna().empty else "Unknown"

    total = len(df)
    rsi_puddle = int((df.get("signal") == "RSI & Puddle").sum()) if not df.empty and "signal" in df.columns else 0
    stocks = int((df.get("asset_type") == "Stock").sum()) if not df.empty and "asset_type" in df.columns else 0
    etfs = int((df.get("asset_type") == "ETF").sum()) if not df.empty and "asset_type" in df.columns else 0

    st.markdown(
        f"""
        <div class="app-hero">
            <div class="hero-row">
                <div>
                    <h1>Puddle Signal Scanner</h1>
                    <p>Large-cap stocks and representative ETFs filtered by Puddle and RSI & Puddle signals.</p>
                </div>
                <div class="viewer-pill"><strong>{selected_date}</strong> selected</div>
            </div>
            <div style="margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;">
                <div class="updated-mark"><strong>{scan_time}</strong></div>
                <div class="mini-pill"><strong>{selected_row['filename']}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='metric-grid'>"
        + metric_card("Total Signals", total, "Puddle + RSI & Puddle")
        + metric_card("RSI & Puddle", rsi_puddle, "stronger warning")
        + metric_card("Stocks", stocks, "S&P500 + NASDAQ100")
        + metric_card("ETFs", etfs, "representative ETF set")
        + "</div>",
        unsafe_allow_html=True,
    )

    if not df.empty:
        df["_stage"] = df.get("puddle", pd.Series(dtype=str)).apply(parse_stage)
        stage_counts = df["_stage"].value_counts().to_dict()
        st.markdown("<div class='section-label'>Puddle stages</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='signal-grid'>"
            + signal_card("1st Puddle", stage_counts.get("1st", 0), "MA20 break", "#64a8ff")
            + signal_card("2nd Puddle", stage_counts.get("2nd", 0), "MA60 break", "#9cccff")
            + signal_card("3rd Puddle", stage_counts.get("3rd", 0), "MA120 break", "#ffd166")
            + signal_card("4th Puddle", stage_counts.get("4th", 0), "MA200 + RSI", "#ff6b7a")
            + "</div>",
            unsafe_allow_html=True,
        )

    left, right = st.columns([0.95, 2.05], gap="large")
    with left:
        st.markdown("<div class='section-label'>Date calendar</div>", unsafe_allow_html=True)
        render_calendar(file_df, selected_date)

    with right:
        st.markdown("<div class='section-label'>Signal list</div>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns([1, 1, 1.4])
        type_filter = f1.selectbox("Type", ["All", "Stock", "ETF"])
        signal_filter = f2.selectbox("Signal", ["All", "RSI & Puddle", "Puddle"])
        query = f3.text_input("Ticker search", placeholder="AAPL, QQQ...")

        filtered = df.copy()
        if type_filter != "All" and "asset_type" in filtered.columns:
            filtered = filtered[filtered["asset_type"] == type_filter]
        if signal_filter != "All" and "signal" in filtered.columns:
            filtered = filtered[filtered["signal"] == signal_filter]
        if query and "ticker" in filtered.columns:
            filtered = filtered[filtered["ticker"].str.contains(query.strip(), case=False, na=False)]

        display = prepare_display_table(filtered)
        st.dataframe(display, use_container_width=True, hide_index=True, height=540)

        csv = filtered.drop(columns=["_stage"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download selected CSV",
            data=csv,
            file_name=selected_row["filename"],
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
