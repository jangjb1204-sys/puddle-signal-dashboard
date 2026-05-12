from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
REPO_URL = "https://github.com/jangjb1204-sys/puddle-signal-dashboard"
ACTIONS_URL = f"{REPO_URL}/actions/workflows/update-signals.yml"


def output_path_for(target_date: pd.Timestamp) -> Path:
    return APP_DIR / f"signal_scan_{target_date:%Y%m%d}.csv"


def saved_result_paths() -> list[Path]:
    return sorted(APP_DIR.glob("signal_scan_*.csv"), reverse=True)


def latest_saved_date(default: pd.Timestamp) -> pd.Timestamp:
    paths = saved_result_paths()
    if not paths:
        return default
    latest = paths[0].stem.replace("signal_scan_", "")
    try:
        return pd.to_datetime(latest, format="%Y%m%d").normalize()
    except Exception:
        return default


def render_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #18212f;
            --muted: #667085;
            --line: #e4e7ec;
            --surface: #f8fafc;
            --accent: #0f766e;
            --warn: #b45309;
        }
        .stApp {
            background: #f5f7fb;
            color: var(--ink);
        }
        [data-testid="stHeader"] {
            background: rgba(245, 247, 251, 0.84);
            backdrop-filter: blur(10px);
        }
        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }
        .app-title {
            font-size: 2.15rem;
            line-height: 1.12;
            font-weight: 780;
            letter-spacing: 0;
            margin: 0 0 .35rem 0;
        }
        .app-subtitle {
            color: var(--muted);
            font-size: .98rem;
            margin-bottom: 1.1rem;
        }
        .section-label {
            color: var(--muted);
            font-size: .78rem;
            font-weight: 760;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin: 1.2rem 0 .35rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .85rem .95rem;
            box-shadow: 0 1px 2px rgba(16, 24, 40, .04);
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.55rem;
        }
        .status-note {
            border: 1px solid var(--line);
            background: #ffffff;
            border-radius: 8px;
            padding: .8rem .95rem;
            color: var(--muted);
            font-size: .92rem;
        }
        .stButton > button {
            border-radius: 7px;
            font-weight: 720;
        }
        .stDownloadButton > button {
            border-radius: 7px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_existing_result(target_date: pd.Timestamp) -> pd.DataFrame:
    path = output_path_for(target_date)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def format_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    table = df.copy()
    for col in ["close", "change_pct", "rsi"]:
        if col in table.columns:
            table[col] = pd.to_numeric(table[col], errors="coerce").round(2)
    return table


def main() -> None:
    st.set_page_config(
        page_title="Puddle Signal Scanner",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_css()

    today = pd.Timestamp.today().normalize()
    default_date = latest_saved_date(today)

    st.markdown('<div class="app-title">Puddle Signal Scanner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">상위 주식/ETF에서 오늘 기준 Puddle 및 RSI & Puddle 신호를 빠르게 확인합니다.</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Data")
        selected_date = st.date_input("Date", value=default_date.date())
        st.link_button("Update on GitHub", ACTIONS_URL, use_container_width=True)
        st.caption("데이터 업데이트는 GitHub Actions에서 실행하고, 이 앱은 저장된 CSV를 빠르게 표시합니다.")

    target_date = pd.Timestamp(selected_date).normalize()

    if "result" not in st.session_state or st.session_state.get("target_date") != str(target_date.date()):
        existing = load_existing_result(target_date)
        st.session_state.result = existing
        st.session_state.output_path = output_path_for(target_date)
        st.session_state.target_date = str(target_date.date())

    result = st.session_state.get("result", pd.DataFrame())
    output_path = st.session_state.get("output_path", output_path_for(target_date))

    total = len(result)
    rsi_count = int((result.get("signal") == "RSI & Puddle").sum()) if not result.empty else 0
    stock_count = int((result.get("asset_type") == "Stock").sum()) if not result.empty else 0
    etf_count = int((result.get("asset_type") == "ETF").sum()) if not result.empty else 0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Signals", total)
    metric_cols[1].metric("RSI & Puddle", rsi_count)
    metric_cols[2].metric("Stocks", stock_count)
    metric_cols[3].metric("ETFs", etf_count)

    st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)

    if result.empty:
        st.markdown(
            '<div class="status-note">저장된 결과가 없거나 해당 날짜에 신호가 없습니다. 왼쪽의 Update on GitHub에서 workflow를 실행하면 CSV가 repo에 저장됩니다.</div>',
            unsafe_allow_html=True,
        )
    else:
        filters = st.columns([1, 1, 2])
        asset_filter = filters[0].multiselect(
            "Asset type",
            options=["Stock", "ETF"],
            default=["Stock", "ETF"],
        )
        signal_filter = filters[1].multiselect(
            "Signal",
            options=["RSI & Puddle", "Puddle"],
            default=["RSI & Puddle", "Puddle"],
        )
        ticker_query = filters[2].text_input("Ticker search", placeholder="AAPL, SPY...")

        filtered = result.copy()
        if asset_filter:
            filtered = filtered[filtered["asset_type"].isin(asset_filter)]
        if signal_filter:
            filtered = filtered[filtered["signal"].isin(signal_filter)]
        if ticker_query:
            filtered = filtered[filtered["ticker"].str.contains(ticker_query.strip(), case=False, na=False)]

        st.dataframe(
            format_table(filtered),
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "asset_type": st.column_config.TextColumn("Type", width="small"),
                "ticker": st.column_config.TextColumn("Ticker", width="small"),
                "signal": st.column_config.TextColumn("Signal"),
                "close": st.column_config.NumberColumn("Close", format="%.2f"),
                "change_pct": st.column_config.NumberColumn("Change %", format="%.2f"),
                "rsi": st.column_config.NumberColumn("RSI", format="%.2f"),
                "puddle": st.column_config.TextColumn("Puddle"),
            },
        )

        csv_bytes = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered CSV",
            data=csv_bytes,
            file_name=output_path.name,
            mime="text/csv",
        )

    with st.expander("Data source", expanded=False):
        st.write(f"Repository: {REPO_URL}")
        st.write(f"Selected file: {output_path.name}")
        st.write("GitHub Actions updates and commits `signal_scan_YYYYMMDD.csv` files.")


if __name__ == "__main__":
    main()
