"""
Standalone scanner for Puddle and RSI & Puddle signals.

GitHub Actions runs this script on a schedule and overwrites one daily CSV file
inside the signal_scans folder.

Examples:
    python puddle_rsi_signal_scanner.py --date 2026-05-11

    python puddle_rsi_signal_scanner.py \
        --date 2026-05-11 \
        --stocks-csv stocks.csv \
        --etfs-csv etfs.csv \
        --output scan.csv

Optional CSV universe format:
    ticker
    AAPL
    MSFT
    SPY
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests
import yfinance as yf

pd.set_option("future.no_silent_downcasting", True)


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
)

DEFAULT_STOCK_URL = "https://www.slickcharts.com/sp500"
DEFAULT_NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
YF_REQUEST_PAUSE_SECONDS = 3.0
YF_RETRIES = 0
YF_RETRY_PAUSE_SECONDS = 15.0
CACHE_DIR = Path(__file__).resolve().parent / ".puddle_yf_cache"
CACHE_MAX_HOURS = 0.0
REFRESH_CACHE = False
UNIVERSE_CACHE_FILENAME = "ticker_universe.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "signal_scans"
DEFAULT_ETF_TICKERS = [
    "SPY", "IVV", "VOO", "VTI", "QQQ", "VEA", "VTV", "IEFA", "VUG", "AGG",
    "BND", "IEMG", "VWO", "IJH", "VIG", "IJR", "IWF", "IWM", "GLD", "IWD",
    "VO", "VB", "VXUS", "XLK", "VGT", "SCHD", "VNQ", "XLV", "XLF", "XLE",
    "XLY", "XLI", "XLP", "XLU", "XLB", "XLRE", "XLC", "TLT", "HYG", "LQD",
    "TIP", "SHY", "IEF", "BIL", "SGOV", "DIA", "RSP", "MDY", "SMH", "SOXX",
    "ARKK", "EFA", "EEM", "EWJ", "EWZ", "FXI", "VGK", "GDX", "SLV", "USO",
]


class YahooRateLimitError(RuntimeError):
    pass


def normalize_ticker(ticker: str) -> str:
    clean = str(ticker).strip().upper()
    if not clean:
        return ""
    return clean.replace(".", "-")


def unique_tickers(tickers: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for ticker in tickers:
        clean = normalize_ticker(ticker)
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def load_tickers_from_csv(path: str | Path, limit: int) -> list[str]:
    df = pd.read_csv(path)
    if df.empty:
        return []

    lower_cols = {str(col).strip().lower(): col for col in df.columns}
    ticker_col = lower_cols.get("ticker") or lower_cols.get("symbol") or df.columns[0]
    return unique_tickers(df[ticker_col].dropna().tolist())[:limit]


def universe_cache_path() -> Path:
    return CACHE_DIR / UNIVERSE_CACHE_FILENAME


def load_universe_cache(key: str, limit: int | None = None) -> list[str] | None:
    path = universe_cache_path()
    if not path.exists() or REFRESH_CACHE:
        return None
    try:
        data = json.loads(path.read_text())
        tickers = unique_tickers(data.get(key, []))
        if tickers:
            print(f"{key}: universe cache hit ({len(tickers)} tickers)", flush=True)
            return tickers[:limit] if limit else tickers
    except Exception as exc:
        print(f"{key}: universe cache read failed ({format_error(exc)})", flush=True)
    return None


def save_universe_cache(key: str, tickers: list[str]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = universe_cache_path()
        data = json.loads(path.read_text()) if path.exists() else {}
        data[key] = unique_tickers(tickers)
        path.write_text(json.dumps(data, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"{key}: universe cache write failed ({format_error(exc)})", flush=True)


def extract_tickers_with_cache(key: str, url: str, limit: int | None = None) -> list[str]:
    cached = load_universe_cache(key, limit)
    if cached is not None:
        return cached
    try:
        tickers = extract_tickers_from_html_table(url, limit)
    except Exception as exc:
        print(f"{key}: universe download failed ({format_error(exc)})", flush=True)
        return []
    if tickers:
        save_universe_cache(key, tickers)
    return tickers


def extract_tickers_from_html_table(url: str, limit: int | None = None) -> list[str]:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    for table in tables:
        lower_cols = {str(col).strip().lower(): col for col in table.columns}
        ticker_col = lower_cols.get("symbol") or lower_cols.get("ticker") or lower_cols.get("fund")
        if ticker_col is None:
            continue

        tickers = unique_tickers(table[ticker_col].dropna().tolist())
        if tickers:
            return tickers[:limit] if limit else tickers

    return []


def merge_stock_universes(sp500_tickers: list[str], nasdaq100_tickers: list[str]) -> tuple[list[str], dict[str, str]]:
    source_map: dict[str, list[str]] = {}
    for ticker in unique_tickers(sp500_tickers):
        source_map.setdefault(ticker, []).append("S&P500")
    for ticker in unique_tickers(nasdaq100_tickers):
        source_map.setdefault(ticker, []).append("NASDAQ100")

    merged = unique_tickers([*sp500_tickers, *nasdaq100_tickers])
    universe_map = {ticker: ",".join(source_map.get(ticker, ["Stock"])) for ticker in merged}
    return merged, universe_map


def load_universe(
    stocks_csv: str | None,
    etfs_csv: str | None,
    stock_limit: int,
    etf_limit: int,
) -> tuple[list[str], list[str], dict[str, str]]:
    if stocks_csv:
        stock_tickers = load_tickers_from_csv(stocks_csv, stock_limit)
        stock_universe_map = {ticker: "CustomStock" for ticker in stock_tickers}
    else:
        sp500_tickers = extract_tickers_with_cache("sp500_top", DEFAULT_STOCK_URL, stock_limit)
        nasdaq100_tickers = extract_tickers_with_cache("nasdaq100", DEFAULT_NASDAQ100_URL)
        stock_tickers, stock_universe_map = merge_stock_universes(sp500_tickers, nasdaq100_tickers)

    if etfs_csv:
        etf_tickers = load_tickers_from_csv(etfs_csv, etf_limit)
    else:
        etf_tickers = unique_tickers(DEFAULT_ETF_TICKERS)[:etf_limit]

    return stock_tickers, etf_tickers, stock_universe_map


def fetch_common_market_data(period: str = "2y") -> dict:
    results = {}
    market_specs = [
        ("treasury", "^TNX", "10Y Treasury"),
        ("vix", "^VIX", "VIX"),
        ("vix1d", "^VIX1D", "VIX1D"),
        ("skew", "^SKEW", "SKEW"),
    ]

    def fetch_market_series(spec):
        key, ticker_sym, col_name = spec
        try:
            history = fetch_history_with_retries(ticker_sym, period=period)
            if history.empty or not {"Date", "Close"}.issubset(history.columns):
                return key, pd.DataFrame()
            df = history[["Date", "Close"]].rename(columns={"Close": col_name})
            df = normalize_date_column(df)
            df[col_name] = df[col_name].round(2)
            return key, df
        except YahooRateLimitError as exc:
            print(f"Common market data {ticker_sym}: skipped ({exc})", flush=True)
            return key, pd.DataFrame()
        except Exception as exc:
            print(f"Common market data {ticker_sym}: failed ({format_error(exc)})", flush=True)
            return key, pd.DataFrame()

    for spec in market_specs:
        key, df = fetch_market_series(spec)
        results[key] = df
        time.sleep(YF_REQUEST_PAUSE_SECONDS)

    return results


def format_error(error: Exception) -> str:
    message = str(error).strip()
    return f"{error.__class__.__name__}: {message}" if message else error.__class__.__name__


def is_yahoo_rate_limit_error(error: Exception) -> bool:
    text = format_error(error).lower()
    return "yfratelimiterror" in text or "too many requests" in text or "rate limit" in text


def normalize_date_column(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty or "Date" not in data.columns:
        return data
    data = data.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    return data.dropna(subset=["Date"])


def cache_path_for(ticker: str, period: str) -> Path:
    raw_name = f"{ticker}_{period}"
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in raw_name)
    return CACHE_DIR / f"{safe_name}.csv"


def load_history_cache(ticker: str, period: str, allow_stale: bool = False) -> pd.DataFrame | None:
    path = cache_path_for(ticker, period)
    if not path.exists():
        return None

    if not allow_stale and CACHE_MAX_HOURS > 0:
        age_hours = (time.time() - path.stat().st_mtime) / 3600
        if age_hours > CACHE_MAX_HOURS:
            return None

    try:
        data = normalize_date_column(pd.read_csv(path))
        if data.empty:
            return None
        data.attrs["source"] = "cache"
        print(f"    {ticker}: cache hit ({len(data)} rows)", flush=True)
        return data
    except Exception as exc:
        print(f"    {ticker}: cache read failed ({format_error(exc)})", flush=True)
        return None


def save_history_cache(ticker: str, period: str, data: pd.DataFrame) -> None:
    if data.empty or "Date" not in data.columns:
        return
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data.to_csv(cache_path_for(ticker, period), index=False)
    except Exception as exc:
        print(f"    {ticker}: cache write failed ({format_error(exc)})", flush=True)


def fetch_history_with_retries(ticker: str, period: str) -> pd.DataFrame:
    if not REFRESH_CACHE:
        cached = load_history_cache(ticker, period)
        if cached is not None:
            return cached

    stale_cache = load_history_cache(ticker, period, allow_stale=True)
    last_error = ""
    for attempt in range(1, YF_RETRIES + 2):
        try:
            data = normalize_date_column(yf.Ticker(ticker).history(period=period).dropna(how="all").reset_index())
            if not data.empty:
                data.attrs["source"] = "yahoo"
                save_history_cache(ticker, period, data)
            return data
        except Exception as exc:
            last_error = format_error(exc)
            if is_yahoo_rate_limit_error(exc) and attempt > YF_RETRIES:
                if stale_cache is not None:
                    print(f"    {ticker}: using stale cache because Yahoo is rate limited", flush=True)
                    stale_cache.attrs["source"] = "stale_cache"
                    return stale_cache
                raise YahooRateLimitError(last_error) from exc
            if attempt <= YF_RETRIES:
                print(
                    f"    {ticker}: {last_error}; retrying in {YF_RETRY_PAUSE_SECONDS:g}s "
                    f"({attempt}/{YF_RETRIES})",
                    flush=True,
                )
                time.sleep(YF_RETRY_PAUSE_SECONDS)
            else:
                print(f"    {ticker}: {last_error}", flush=True)
    return pd.DataFrame()


def fetch_batch_stock_data(
    tickers: list[str],
    period: str,
    progress_start: int = 0,
    progress_total: int | None = None,
) -> dict[str, pd.DataFrame]:
    if not tickers:
        return {}

    results = {}
    total = progress_total or len(tickers)
    for index, ticker in enumerate(tickers, start=1):
        progress_index = progress_start + index
        print(f"  [{progress_index}/{total}] Downloading {ticker}...", flush=True)
        try:
            data = fetch_history_with_retries(ticker, period=period)
            if data.empty:
                results[ticker] = pd.DataFrame()
                print(f"  [{progress_index}/{total}] {ticker}: no data", flush=True)
                continue
            if "Date" not in data.columns:
                data = data.rename(columns={data.columns[0]: "Date"})
            source = data.attrs.get("source", "yahoo")
            data = normalize_date_column(data)
            data.attrs["source"] = source
            results[ticker] = data
            print(f"  [{progress_index}/{total}] {ticker}: {len(data)} rows", flush=True)
        except YahooRateLimitError:
            print(f"  [{progress_index}/{total}] {ticker}: stopped by Yahoo rate limit", flush=True)
            raise
        except Exception as exc:
            results[ticker] = pd.DataFrame()
            print(f"  [{progress_index}/{total}] {ticker}: failed ({format_error(exc)})", flush=True)
        if results.get(ticker, pd.DataFrame()).attrs.get("source") not in {"cache", "stale_cache"}:
            time.sleep(YF_REQUEST_PAUSE_SECONDS)
    return results


def calculate_rsi(data: pd.DataFrame, window: int = 14) -> pd.Series:
    if len(data) < window:
        return pd.Series([np.nan] * len(data), index=data.index)
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return (100 - (100 / (1 + rs))).round(2)


def calculate_moving_averages(data: pd.DataFrame, windows: list[int] | None = None) -> pd.DataFrame:
    windows = windows or [20, 60, 120, 200]
    for window in windows:
        data[f"MA{window}"] = data["Close"].rolling(window=window).mean().round(2) if len(data) >= window else np.nan
    return data


def generate_puddle_signals(data: pd.DataFrame) -> pd.DataFrame:
    alerts = [""]
    for i in range(1, len(data)):
        row, prev = data.iloc[i], data.iloc[i - 1]
        conditions = {
            1: (
                not pd.isna(row.get("MA20"))
                and row["Close"] < row["MA20"]
                and prev["Close"] >= prev.get("MA20", np.nan)
            ),
            2: (
                not pd.isna(row.get("MA60"))
                and row["Close"] < row["MA60"]
                and prev["Close"] >= prev.get("MA60", np.nan)
            ),
            3: (
                not pd.isna(row.get("MA120"))
                and row["Close"] < row["MA120"]
                and prev["Close"] >= prev.get("MA120", np.nan)
            ),
            4: (
                not pd.isna(row.get("MA200"))
                and not pd.isna(prev.get("MA200"))
                and row["Close"] < row["MA200"]
                and prev["Close"] >= prev.get("MA200", np.nan)
                and not pd.isna(row.get("RSI"))
                and row["RSI"] < 30
            ),
        }
        timings = [k for k, v in conditions.items() if v]
        alerts.append(
            {
                4: "4th: MA200, RSI<=30, 100% cash, 40d",
                3: "3rd: MA120, 50% cash, 5d",
                2: "2nd: MA60, 50% cash, 5d",
                1: "1st: MA20, 10% cash",
            }.get(max(timings))
            if timings
            else ""
        )
    data["Puddle"] = alerts
    return data


def calculate_vix_skew_signals(data: pd.DataFrame) -> pd.DataFrame:
    if "VIX" in data.columns and "VIX1D" in data.columns:
        data["VIX1D>VIX"] = np.where(
            data["VIX"].notna()
            & data["VIX1D"].notna()
            & (data["VIX"] >= 25)
            & (data["VIX1D"] > data["VIX"]),
            "BUY",
            "",
        )
    else:
        data["VIX1D>VIX"] = ""
    return data


def process_stock_frame(data: pd.DataFrame, ticker: str, common_data: dict) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()

    data = data.copy()
    required_cols = ["Close", "Open", "High", "Low"]
    if not set(required_cols).issubset(data.columns):
        return pd.DataFrame()

    data[required_cols] = data[required_cols].round(2)
    data["Change(%)"] = (data["Close"].pct_change() * 100).round(2)
    log_returns = np.log(data["Close"] / data["Close"].shift(1))
    data["2sigma(%)"] = round(log_returns.std() * 100 * 2, 1)

    data = calculate_moving_averages(data)
    data["RSI"] = calculate_rsi(data)

    for df_extra in [
        common_data.get("treasury"),
        common_data.get("vix"),
        common_data.get("vix1d"),
        common_data.get("skew"),
    ]:
        if df_extra is not None and not df_extra.empty:
            data = pd.merge(data, df_extra, on="Date", how="left")

    data = generate_puddle_signals(data)
    data = calculate_vix_skew_signals(data)
    data["Tick"] = ticker
    return data.reset_index(drop=True)


def has_text_signal(value) -> bool:
    if pd.isna(value):
        return False
    return any(ch.isalpha() for ch in str(value))


def has_rsi_puddle_signal(rsi, puddle) -> bool:
    try:
        return float(rsi) <= 30 and has_text_signal(puddle)
    except Exception:
        return False


def row_on_or_before(df: pd.DataFrame, target_date: pd.Timestamp) -> pd.Series | None:
    if df.empty or "Date" not in df.columns:
        return None

    df = normalize_date_column(df)
    dates = df["Date"]
    eligible = df.loc[dates <= target_date].copy()
    if eligible.empty:
        return None

    eligible["_scan_date"] = eligible["Date"]
    return eligible.sort_values("_scan_date").iloc[-1]


def scan_batch(
    tickers: list[str],
    universe_name: str,
    target_date: pd.Timestamp,
    period: str,
    common_data: dict,
    stock_universe_map: dict[str, str] | None = None,
    progress_start: int = 0,
    progress_total: int | None = None,
) -> tuple[list[dict], bool]:
    raw_frames = fetch_batch_stock_data(
        tickers,
        period=period,
        progress_start=progress_start,
        progress_total=progress_total,
    )
    results = []
    used_yahoo = any(
        frame.attrs.get("source") not in {"cache", "stale_cache"}
        for frame in raw_frames.values()
        if not frame.empty
    )

    for ticker in tickers:
        raw = raw_frames.get(ticker, pd.DataFrame())
        if raw.empty:
            continue

        processed = process_stock_frame(raw, ticker=ticker, common_data=common_data)
        row = row_on_or_before(processed, target_date)
        if row is None:
            continue

        puddle = row.get("Puddle", "")
        rsi = row.get("RSI")
        puddle_signal = has_text_signal(puddle)
        rsi_puddle_signal = has_rsi_puddle_signal(rsi, puddle)

        if not puddle_signal and not rsi_puddle_signal:
            continue

        is_etf = universe_name == "etf_top"
        signal = "RSI & Puddle" if rsi_puddle_signal else "Puddle"
        actual_date = pd.to_datetime(row.get("Date")).strftime("%Y-%m-%d")

        results.append(
            {
                "date": actual_date,
                "asset_type": "ETF" if is_etf else "Stock",
                "universe": "ETF" if is_etf else (stock_universe_map or {}).get(ticker, "Stock"),
                "ticker": ticker,
                "signal": signal,
                "close": row.get("Close"),
                "change_pct": row.get("Change(%)"),
                "rsi": rsi,
                "puddle": puddle,
            }
        )

    return results, used_yahoo


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def scan_universe(
    stock_tickers: list[str],
    etf_tickers: list[str],
    stock_universe_map: dict[str, str],
    target_date: pd.Timestamp,
    period: str,
    batch_size: int,
    pause_seconds: float,
) -> pd.DataFrame:
    common_data = fetch_common_market_data(period=period)
    all_results = []

    jobs = [
        ("stock_top", unique_tickers(stock_tickers)),
        ("etf_top", unique_tickers(etf_tickers)),
    ]

    for universe_name, tickers in jobs:
        print(f"Scanning {universe_name}: {len(tickers)} tickers", flush=True)
        batch_start = 0
        for batch in chunked(tickers, batch_size):
            batch_results, used_yahoo = scan_batch(
                tickers=batch,
                universe_name=universe_name,
                target_date=target_date,
                period=period,
                common_data=common_data,
                stock_universe_map=stock_universe_map,
                progress_start=batch_start,
                progress_total=len(tickers),
            )
            all_results.extend(batch_results)
            batch_start += len(batch)
            if used_yahoo and pause_seconds > 0:
                time.sleep(pause_seconds)

    columns = [
        "scan_timestamp_utc",
        "date",
        "asset_type",
        "universe",
        "ticker",
        "signal",
        "close",
        "change_pct",
        "rsi",
        "puddle",
    ]

    if not all_results:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(all_results)
    signal_rank = {"RSI & Puddle": 0, "Puddle": 1}
    df["_rank"] = df["signal"].map(signal_rank).fillna(99)
    df = df.sort_values(["date", "_rank", "asset_type", "universe", "ticker"], ascending=[False, True, True, True, True])
    return df.drop(columns=["_rank"]).reset_index(drop=True)


def daily_output_path(target_date: pd.Timestamp) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"signal_scan_{target_date:%Y%m%d}.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan large-cap stocks and ETFs for Puddle / RSI & Puddle signals."
    )
    parser.add_argument("--date", help="Scan date in YYYY-MM-DD. Defaults to today UTC.")
    parser.add_argument("--period", default="2y", help="Historical download period. Default: 2y.")
    parser.add_argument("--stock-limit", type=int, default=100, help="Number of S&P 500 stock tickers. Nasdaq 100 is added separately.")
    parser.add_argument("--etf-limit", type=int, default=100, help="Number of ETF tickers.")
    parser.add_argument("--stocks-csv", help="Optional CSV containing stock tickers.")
    parser.add_argument("--etfs-csv", help="Optional CSV containing ETF tickers.")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch download size.")
    parser.add_argument("--pause", type=float, default=1.0, help="Pause between batches in seconds.")
    parser.add_argument("--request-pause", type=float, default=YF_REQUEST_PAUSE_SECONDS, help="Pause after each Yahoo request.")
    parser.add_argument("--retries", type=int, default=YF_RETRIES, help="Retries per Yahoo request.")
    parser.add_argument("--retry-pause", type=float, default=YF_RETRY_PAUSE_SECONDS, help="Pause before retrying a Yahoo request.")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR), help="Directory for cached Yahoo price data.")
    parser.add_argument("--cache-max-hours", type=float, default=CACHE_MAX_HOURS, help="Use cache files newer than this many hours. Use 0 to never expire.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignore cached Yahoo data and download again.")
    parser.add_argument("--output", help="Optional CSV output path. Defaults to signal_scans/signal_scan_YYYYMMDD.csv.")
    return parser.parse_args()


def main() -> None:
    global YF_REQUEST_PAUSE_SECONDS, YF_RETRIES, YF_RETRY_PAUSE_SECONDS
    global CACHE_DIR, CACHE_MAX_HOURS, REFRESH_CACHE

    args = parse_args()
    scan_timestamp = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    YF_REQUEST_PAUSE_SECONDS = max(0.0, args.request_pause)
    YF_RETRIES = max(0, args.retries)
    YF_RETRY_PAUSE_SECONDS = max(0.0, args.retry_pause)
    CACHE_DIR = Path(args.cache_dir).expanduser()
    CACHE_MAX_HOURS = max(0.0, args.cache_max_hours)
    REFRESH_CACHE = bool(args.refresh_cache)
    target_date = pd.Timestamp(args.date or scan_timestamp.date()).normalize()
    print(f"Scan timestamp UTC: {scan_timestamp.isoformat()}", flush=True)
    print(f"Yahoo cache: {CACHE_DIR}", flush=True)

    stock_tickers, etf_tickers, stock_universe_map = load_universe(
        stocks_csv=args.stocks_csv,
        etfs_csv=args.etfs_csv,
        stock_limit=args.stock_limit,
        etf_limit=args.etf_limit,
    )

    if not stock_tickers and not etf_tickers:
        raise SystemExit(
            "No tickers found. Provide --stocks-csv and/or --etfs-csv with a ticker column."
        )

    try:
        result = scan_universe(
            stock_tickers=stock_tickers,
            etf_tickers=etf_tickers,
            stock_universe_map=stock_universe_map,
            target_date=target_date,
            period=args.period,
            batch_size=args.batch_size,
            pause_seconds=args.pause,
        )
    except YahooRateLimitError as exc:
        raise SystemExit(
            "\nYahoo Finance rate limit에 걸려서 스캔을 중단했습니다.\n"
            f"마지막 오류: {exc}\n"
            "10-30분 정도 기다린 뒤 다시 실행하거나, 네트워크를 바꿔서 시도하세요.\n"
            "빠른 테스트는 --stock-limit 2 --etf-limit 2 처럼 작은 범위로 먼저 해보는 게 좋습니다."
        ) from exc

    result.insert(0, "scan_timestamp_utc", scan_timestamp.isoformat())

    output_path = Path(args.output) if args.output else daily_output_path(target_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.to_csv(index=False))

    print(f"Scanned stocks: {len(stock_tickers)}")
    print(f"Scanned ETFs:   {len(etf_tickers)}")
    print(f"Signals found:  {len(result)}")
    print(f"Saved:          {output_path}")
    if not result.empty:
        print()
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
