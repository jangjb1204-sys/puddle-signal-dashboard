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
    background:
        radial-gradient(circle at 18% 10%, rgba(100,168,255,0.20), transparent 26%),
        radial-gradient(circle at 82% 4%, rgba(156,204,255,0.14), transparent 30%),
        linear-gradient(180deg, #091b31 0%, #061323 44%, #020711 100%) !important;
    color: #f5f5f7 !important;
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background: linear-gradient(112deg, transparent 0%, rgba(235,247,255,0.12) 18%, transparent 36%), linear-gradient(75deg, transparent 52%, rgba(86,154,255,0.09) 72%, transparent 90%);
    opacity: .74; mix-blend-mode: screen;
}
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"] { display:none!important; visibility:hidden!important; height:0!important; }
.block-container { padding-top: 1.25rem!important; padding-bottom: 2.5rem!important; max-width: 1360px; position:relative; z-index:1; }
.app-hero, .glass-card {
    border: 1px solid rgba(190,220,255,0.20);
    background: linear-gradient(145deg, rgba(241,248,255,0.14), rgba(255,255,255,0.04) 54%, rgba(117,181,255,0.03)), rgba(7,23,42,0.56);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.24), inset 0 -1px 0 rgba(255,255,255,0.05), 0 18px 54px rgba(0,0,0,0.22);
    backdrop-filter: blur(28px) saturate(1.5); -webkit-backdrop-filter: blur(28px) saturate(1.5);
}
.app-hero { position:relative; overflow:hidden; margin:.2rem 0 1.05rem; padding:1.28rem 1.36rem 1.2rem; border-radius:30px; }
.app-hero::before { content:""; position:absolute; left:22px; right:22px; top:0; height:1px; background:linear-gradient(90deg, transparent, rgba(255,255,255,.58), transparent); }
.hero-row { position:relative; z-index:1; display:flex; align-items:flex-end; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.app-hero h1 { margin:0; font-size:2.42rem!important; line-height:1.08; font-weight:760!important; color:#f7fbff!important; text-shadow:0 12px 34px rgba(0,0,0,.28); }
.app-hero p { margin:.45rem 0 0; color:rgba(207,228,255,.68); font-size:.9rem; }
.hero-meta { position:relative; z-index:1; display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }
.pill { display:inline-flex; align-items:center; gap:9px; padding:8px 13px; border:1px solid rgba(190,220,255,.22); border-radius:999px; background:linear-gradient(135deg, rgba(231,246,255,.14), rgba(255,255,255,.035)), rgba(7,24,43,.56); color:rgba(226,240,255,.72); font-size:.76rem; box-shadow:inset 0 1px 0 rgba(255,255,255,.18), 0 12px 32px rgba(0,0,0,.14); }
.pill strong { color:#9cccff; font-weight:750; }
.section-label { color:rgba(207,228,255,.64); font-size:.8rem; font-weight:700; margin:1.15rem 0 .48rem; }
.metric-grid, .stage-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:.75rem 0 1rem; }
.glass-card { position:relative; overflow:hidden; padding:16px 17px; border-radius:24px; }
.metric-card .label { color:rgba(207,228,255,.60); font-size:.72rem; font-weight:700; margin-bottom:9px; }
.metric-card .value { font-family:'DM Mono', monospace; font-size:1.58rem; font-weight:500; color:#f7fbff; }
.metric-card .hint { margin-top:7px; color:rgba(207,228,255,.48); font-size:.76rem; }
.stage-card { min-height:120px; }
.stage-title { display:flex; align-items:center; gap:8px; color:#f7fbff; font-size:1.02rem; font-weight:750; margin-bottom:10px; }
.dot { width:8px; height:8px; border-radius:999px; background:#9cccff; box-shadow:0 0 18px rgba(156,204,255,.55); }
.dot.blue{background:#64a8ff}.dot.yellow{background:#ffd166;box-shadow:0 0 18px rgba(255,209,102,.45)}.dot.red{background:#ff6b7a;box-shadow:0 0 18px rgba(255,107,122,.5)}
.stage-row { display:flex; justify-content:space-between; gap:12px; padding:7px 0; border-top:1px solid rgba(255,255,255,.08); color:rgba(235,244,255,.86); font-size:.84rem; }
.stage-row:first-of-type { border-top:none; }
.mono { font-family:'DM Mono', monospace; color:rgba(207,228,255,.58); }
.date-strip { display:flex; gap:8px; overflow-x:auto; padding:10px 2px 12px; scrollbar-width:none; }
.date-chip { min-width:82px; padding:10px 12px; border:1px solid rgba(190,220,255,.17); border-radius:18px; background:rgba(7,23,42,.44); color:rgba(226,240,255,.72); text-align:center; }
.date-chip .day { font-family:'DM Mono', monospace; font-size:1.05rem; color:#f7fbff; }
.date-chip .month { font-size:.68rem; color:rgba(207,228,255,.48); }
.filter-card { padding:14px 16px; margin-bottom:12px; }
div[data-testid="stDataFrame"] { border-radius:24px!important; overflow:hidden!important; border:1px solid rgba(190,220,255,.12); }
div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label { color:rgba(207,228,255,.64)!important; font-size:.76rem!important; font-weight:650!important; }
div[data-baseweb="select"] > div, div[data-testid="stTextInput"] [data-baseweb="input"] { background:linear-gradient(135deg, rgba(241,248,255,.12), rgba(255,255,255,.035)), rgba(9,28,50,.72)!important; border:1px solid rgba(190,220,255,.24)!important; border-radius:18px!important; min-height:46px!important; box-shadow:inset 0 1px 0 rgba(255,255,255,.18), 0 16px 42px rgba(0,0,0,.14)!important; }
div[data-baseweb="select"] span, div[data-testid="stTextInput"] input { color:#f5f5f7!important; font-weight:600!important; }
.stButton > button { width:100%; border-radius:16px; border:1px solid rgba(190,220,255,.18); background:rgba(7,23,42,.46); color:rgba(226,240,255,.82); min-height:42px; }
.stButton > button[kind="primary"] { background:linear-gradient(145deg, rgba(232,246,255,.95), rgba(156,204,255,.76)); color:#071323; border-color:rgba(231,246,255,.86); font-weight:750; }
@media (max-width:900px){ .metric-grid,.stage-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.app-hero h1{font-size:2rem!important;} }
@media (max-width:640px){ .metric-grid,.stage-grid{grid-template-columns:1fr;}.block-container{padding-left:1rem!important;padding-right:1rem!important;} }
</style>
"""

@st.cache_data(show_spinner=False)
def list_scan_files() -> pd.DataFrame:
    rows=[]
    if not SCAN_DIR.exists():
        return pd.DataFrame(columns=["date","path","filename"])
    for path in sorted(SCAN_DIR.glob("signal_scan_*.csv")):
        raw=path.stem.replace("signal_scan_","")
        try:
            scan_date=pd.to_datetime(raw,format="%Y%m%d").date()
        except Exception:
            continue
        rows.append({"date":scan_date,"path":str(path),"filename":path.name})
    return pd.DataFrame(rows).sort_values("date") if rows else pd.DataFrame(columns=["date","path","filename"])

@st.cache_data(show_spinner=False)
def load_scan_csv(path:str)->pd.DataFrame:
    try:
        df=pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    for col in ["close","change_pct","rsi"]:
        if col in df.columns:
            df[col]=pd.to_numeric(df[col],errors="coerce")
    if "date" in df.columns:
        df["date"]=pd.to_datetime(df["date"],errors="coerce").dt.date
    return df

def metric_card(label,value,hint=""):
    return f"<div class='glass-card metric-card'><div class='label'>{label}</div><div class='value'>{value}</div><div class='hint'>{hint}</div></div>"

def parse_stage(puddle):
    text=str(puddle or "")
    for stage in ["4th","3rd","2nd","1st"]:
        if text.startswith(stage):
            return stage
    return "Other"

def stage_card(title,count,subtitle,dot=""):
    return f"<div class='glass-card stage-card'><div class='stage-title'><span class='dot {dot}'></span>{title}</div><div class='stage-row'><span>Signals</span><span class='mono'>{count}</span></div><div class='stage-row'><span>{subtitle}</span><span class='mono'>active</span></div></div>"

def prepare_display_table(df):
    if df.empty:
        return df
    out=df.copy()
    preferred=["asset_type","universe","ticker","signal","close","change_pct","rsi","puddle","date"]
    out=out[[c for c in preferred if c in out.columns]]
    out=out.rename(columns={"asset_type":"Type","universe":"Universe","ticker":"Ticker","signal":"Signal","close":"Close","change_pct":"Change %","rsi":"RSI","puddle":"Puddle","date":"Price Date"})
    for col in ["Close","Change %","RSI"]:
        if col in out.columns:
            out[col]=pd.to_numeric(out[col],errors="coerce").round(2)
    return out

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    file_df=list_scan_files()
    if file_df.empty:
        st.markdown("<div class='app-hero'><h1>Puddle Signal Scanner</h1><p>No scan files found yet. Run GitHub Actions first.</p></div>", unsafe_allow_html=True)
        st.info("signal_scans 폴더에 CSV가 아직 없습니다.")
        return

    latest_date=file_df["date"].max()
    if "selected_scan_date" not in st.session_state:
        st.session_state.selected_scan_date=latest_date
    selected_date=st.session_state.selected_scan_date
    if selected_date not in set(file_df["date"].tolist()):
        selected_date=latest_date
        st.session_state.selected_scan_date=latest_date

    selected_row=file_df[file_df["date"]==selected_date].iloc[-1]
    df=load_scan_csv(selected_row["path"])
    scan_time="Unknown"
    if not df.empty and "scan_timestamp_utc" in df.columns:
        times=df["scan_timestamp_utc"].dropna()
        if not times.empty:
            scan_time=str(times.iloc[0])

    total=len(df)
    rsi_puddle=int((df.get("signal")=="RSI & Puddle").sum()) if not df.empty and "signal" in df.columns else 0
    stocks=int((df.get("asset_type")=="Stock").sum()) if not df.empty and "asset_type" in df.columns else 0
    etfs=int((df.get("asset_type")=="ETF").sum()) if not df.empty and "asset_type" in df.columns else 0

    st.markdown(f"""
    <div class='app-hero'>
      <div class='hero-row'>
        <div><h1>Puddle Signal Scanner</h1><p>Large-cap stocks and representative ETFs filtered by Puddle and RSI & Puddle signals.</p></div>
        <div class='pill'><strong>{selected_date}</strong> selected</div>
      </div>
      <div class='hero-meta'><div class='pill'>Updated <strong>{scan_time}</strong></div><div class='pill'><strong>{selected_row['filename']}</strong></div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='metric-grid'>"+metric_card("Total Signals",total,"Puddle + RSI & Puddle")+metric_card("RSI & Puddle",rsi_puddle,"stronger warning")+metric_card("Stocks",stocks,"S&P500 + NASDAQ100")+metric_card("ETFs",etfs,"representative ETF set")+"</div>", unsafe_allow_html=True)

    if not df.empty:
        df["_stage"]=df.get("puddle",pd.Series(dtype=str)).apply(parse_stage)
        counts=df["_stage"].value_counts().to_dict()
        st.markdown("<div class='section-label'>Puddle stages</div>", unsafe_allow_html=True)
        st.markdown("<div class='stage-grid'>"+stage_card("1st Puddle",counts.get("1st",0),"MA20 break","blue")+stage_card("2nd Puddle",counts.get("2nd",0),"MA60 break","")+stage_card("3rd Puddle",counts.get("3rd",0),"MA120 break","yellow")+stage_card("4th Puddle",counts.get("4th",0),"MA200 + RSI","red")+"</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Saved dates</div>", unsafe_allow_html=True)
    month_options=sorted({d.replace(day=1) for d in file_df["date"]}, reverse=True)
    selected_month=st.selectbox("Month", month_options, format_func=lambda d:f"{d.year}. {d.month:02d}")
    month_days=file_df[file_df["date"].apply(lambda d: d.year==selected_month.year and d.month==selected_month.month)].sort_values("date", ascending=False)
    st.markdown("<div class='date-strip'>", unsafe_allow_html=True)
    cols=st.columns(min(7, max(1, len(month_days))))
    for idx, (_, row) in enumerate(month_days.iterrows()):
        col=cols[idx % len(cols)]
        day=row["date"]
        if col.button(f"{day.day}\n{month_name[day.month][:3]}", key=f"date-{day.isoformat()}", type="primary" if day==selected_date else "secondary"):
            st.session_state.selected_scan_date=day
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Signal list</div>", unsafe_allow_html=True)
    f1,f2,f3=st.columns([1,1,1.4])
    type_filter=f1.selectbox("Type",["All","Stock","ETF"])
    signal_filter=f2.selectbox("Signal",["All","RSI & Puddle","Puddle"])
    query=f3.text_input("Ticker search", placeholder="AAPL, QQQ...")

    filtered=df.copy()
    if type_filter!="All" and "asset_type" in filtered.columns:
        filtered=filtered[filtered["asset_type"]==type_filter]
    if signal_filter!="All" and "signal" in filtered.columns:
        filtered=filtered[filtered["signal"]==signal_filter]
    if query and "ticker" in filtered.columns:
        filtered=filtered[filtered["ticker"].str.contains(query.strip(),case=False,na=False)]

    st.dataframe(prepare_display_table(filtered), use_container_width=True, hide_index=True, height=560)
    csv=filtered.drop(columns=["_stage"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("Download selected CSV", data=csv, file_name=selected_row["filename"], mime="text/csv", use_container_width=True)

if __name__=="__main__":
    main()
