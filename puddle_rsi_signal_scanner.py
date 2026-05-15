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
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf

pd.set_option("future.no_silent_downcasting", True)


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
)

CENTRAL_TZ = ZoneInfo("America/Chicago")
DEFAULT_STOCK_URL = "https://www.slickcharts.com/sp500"
DEFAULT_NASDAQ100_URL = "https://www.slickcharts.com/nasdaq100"
FALLBACK_NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
DEFAULT_ETF_URL = "https://etfdb.com/compare/market-cap/"
YF_REQUEST_PAUSE_SECONDS = 3.0
YF_RETRIES = 0
YF_RETRY_PAUSE_SECONDS = 15.0
CACHE_DIR = Path(__file__).resolve().parent / ".puddle_yf_cache"
CACHE_MAX_HOURS = 0.0
REFRESH_CACHE = False
UNIVERSE_CACHE_FILENAME = "ticker_universe.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "signal_scans"
DEFAULT_ETF_TICKERS = [
    "VOO", "IVV", "SPY", "VTI", "QQQ", "VEA", "VUG", "IEFA", "GLD", "VTV",
    "BND", "IEMG", "VXUS", "AGG", "IWF", "VWO", "VGT", "IJH", "SPYM", "VIG",
    "IJR", "VO", "XLK", "RSP", "SCHD", "ITOT", "IAU", "EFA", "IWM", "BNDX",
    "VYM", "VB", "SGOV", "QQQM", "IWD", "IVW", "VT", "SCHX", "VCIT", "VEU",
    "SCHF", "IXUS", "XLF", "IBIT", "SCHG", "IVE", "QUAL", "IWR", "VV", "IEF",
    "IWB", "SMH", "DIA", "SLV", "SPYG", "TLT", "JEPI", "BSV", "BIL", "MUB",
    "DFAC", "VTEB", "XLV", "VCSH", "VGIT", "MBB", "SCHB", "DGRO", "SPDW", "VONG",
    "XLE", "JPST", "VNQ", "GOVT", "IUSB", "VBR", "JEPQ", "GDX", "SPYV", "DYNF",
    "GLDM", "VGK", "EFV", "CGDV", "XLI", "MGK", "LQD", "OEF", "IDEV", "TQQQ",
    "BIV", "EEM", "ACWI", "VGSH", "IUSG", "JAAA", "XLC", "VXF", "USHY", "MDY",
]
DEFAULT_ETF_NAMES = {
    "VOO": "Vanguard S&P 500 ETF", "IVV": "iShares Core S&P 500 ETF", "SPY": "State Street SPDR S&P 500 ETF", "VTI": "Vanguard Total Stock Market ETF", "QQQ": "Invesco QQQ Trust Series I",
    "VEA": "Vanguard FTSE Developed Markets ETF", "VUG": "Vanguard Growth ETF", "IEFA": "iShares Core MSCI EAFE ETF", "GLD": "SPDR Gold Shares", "VTV": "Vanguard Value ETF",
    "BND": "Vanguard Total Bond Market ETF", "IEMG": "iShares Core MSCI Emerging Markets ETF", "VXUS": "Vanguard Total International Stock ETF", "AGG": "iShares Core U.S. Aggregate Bond ETF", "IWF": "iShares Russell 1000 Growth ETF",
    "VWO": "Vanguard FTSE Emerging Markets ETF", "VGT": "Vanguard Information Technology ETF", "IJH": "iShares Core S&P Mid-Cap ETF", "SPYM": "State Street SPDR Portfolio S&P 500 ETF", "VIG": "Vanguard Dividend Appreciation ETF",
    "IJR": "iShares Core S&P Small-Cap ETF", "VO": "Vanguard Mid-Cap ETF", "XLK": "State Street Technology Select Sector SPDR ETF", "RSP": "Invesco S&P 500 Equal Weight ETF", "SCHD": "Schwab US Dividend Equity ETF",
    "ITOT": "iShares Core S&P Total U.S. Stock Market ETF", "IAU": "iShares Gold Trust", "EFA": "iShares MSCI EAFE ETF", "IWM": "iShares Russell 2000 ETF", "BNDX": "Vanguard Total International Bond ETF",
    "VYM": "Vanguard High Dividend Yield Index ETF", "VB": "Vanguard Small Cap ETF", "SGOV": "iShares 0-3 Month Treasury Bond ETF", "QQQM": "Invesco NASDAQ 100 ETF", "IWD": "iShares Russell 1000 Value ETF",
    "IVW": "iShares S&P 500 Growth ETF", "VT": "Vanguard Total World Stock ETF", "SCHX": "Schwab U.S. Large-Cap ETF", "VCIT": "Vanguard Intermediate-Term Corporate Bond ETF", "VEU": "Vanguard FTSE All-World ex-US Index Fund",
    "SCHF": "Schwab International Equity ETF", "IXUS": "iShares Core MSCI Total International Stock ETF", "XLF": "State Street Financial Select Sector SPDR ETF", "IBIT": "iShares Bitcoin Trust ETF", "SCHG": "Schwab U.S. Large-Cap Growth ETF",
    "IVE": "iShares S&P 500 Value ETF", "QUAL": "iShares MSCI USA Quality Factor ETF", "IWR": "iShares Russell Midcap ETF", "VV": "Vanguard Large Cap ETF", "IEF": "iShares 7-10 Year Treasury Bond ETF",
    "IWB": "iShares Russell 1000 ETF", "SMH": "VanEck Semiconductor ETF", "DIA": "SPDR Dow Jones Industrial Average ETF Trust", "SLV": "iShares Silver Trust", "SPYG": "State Street SPDR Portfolio S&P 500 Growth ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF", "JEPI": "JPMorgan Equity Premium Income Fund", "BSV": "Vanguard Short-Term Bond ETF", "BIL": "State Street SPDR Bloomberg 1-3 Month T-Bill ETF", "MUB": "iShares National Muni Bond ETF",
    "DFAC": "Dimensional U.S. Core Equity 2 ETF", "VTEB": "Vanguard Tax-Exempt Bond ETF", "XLV": "State Street Health Care Select Sector SPDR ETF", "VCSH": "Vanguard Short-Term Corporate Bond ETF", "VGIT": "Vanguard Intermediate-Term Treasury ETF",
    "MBB": "iShares MBS ETF", "SCHB": "Schwab U.S. Broad Market ETF", "DGRO": "iShares Core Dividend Growth ETF", "SPDW": "State Street SPDR Portfolio Developed World ex-US ETF", "VONG": "Vanguard Russell 1000 Growth ETF",
    "XLE": "State Street Energy Select Sector SPDR ETF", "JPST": "JPMorgan Ultra-Short Income ETF", "VNQ": "Vanguard Real Estate ETF", "GOVT": "iShares U.S. Treasury Bond ETF", "IUSB": "iShares Core Total USD Bond Market ETF",
    "VBR": "Vanguard Small Cap Value ETF", "JEPQ": "JPMorgan NASDAQ Equity Premium Income ETF", "GDX": "VanEck Gold Miners ETF", "SPYV": "State Street SPDR Portfolio S&P 500 Value ETF", "DYNF": "iShares U.S. Equity Factor Rotation Active ETF",
    "GLDM": "SPDR Gold Minishares Trust", "VGK": "Vanguard FTSE Europe ETF", "EFV": "iShares MSCI EAFE Value ETF", "CGDV": "Capital Group Dividend Value ETF", "XLI": "State Street Industrial Select Sector SPDR ETF",
    "MGK": "Vanguard Mega Cap Growth ETF", "LQD": "iShares iBoxx Investment Grade Corporate Bond ETF", "OEF": "iShares S&P 100 ETF", "IDEV": "iShares Core MSCI International Developed Markets ETF", "TQQQ": "ProShares UltraPro QQQ",
    "BIV": "Vanguard Intermediate-Term Bond ETF", "EEM": "iShares MSCI Emerging Markets ETF", "ACWI": "iShares MSCI ACWI ETF", "VGSH": "Vanguard Short-Term Treasury ETF", "IUSG": "iShares Core S&P U.S. Growth ETF",
    "JAAA": "Janus Henderson AAA CLO ETF", "XLC": "State Street Communication Services Select Sector SPDR ETF", "VXF": "Vanguard Extended Market ETF", "USHY": "iShares Broad USD High Yield Corporate Bond ETF", "MDY": "SPDR S&P MIDCAP 400 ETF Trust",
}


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


def pick_column(table: pd.DataFrame, candidates: list[str]):
    lower_cols = {str(col).strip().lower(): col for col in table.columns}
    for candidate in candidates:
        if candidate.lower() in lower_cols:
            return lower_cols[candidate.lower()]
    return None


def parse_asset_amount(value) -> float | None:
    text = str(value or "").strip().replace("$", "").replace(",", "")
    if not text or text == "-" or text.lower() == "nan":
        return None

    multiplier = 1.0
    suffix = text[-1:].upper()
    if suffix in {"T", "B", "M", "K"}:
        text = text[:-1].strip()
        multiplier = {"T": 1_000_000_000_000, "B": 1_000_000_000, "M": 1_000_000, "K": 1_000}[suffix]

    try:
        return float(text) * multiplier
    except Exception:
        return None


def parse_float(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def fast_info_value(info, keys: list[str]) -> float | None:
    for key in keys:
        value = None
        try:
            value = info.get(key)
        except Exception:
            pass
        if value is None:
            try:
                value = info[key]
            except Exception:
                pass
        if value is None:
            try:
                value = getattr(info, key)
            except Exception:
                pass
        parsed = parse_float(value)
        if parsed is not None:
            return parsed
    return None


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
        raw_items = data.get(key, [])
        if raw_items and isinstance(raw_items[0], dict):
            tickers = unique_tickers(item.get("ticker", "") for item in raw_items)
        else:
            tickers = unique_tickers(raw_items)
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
    records = extract_universe_records_from_html_table(url, limit, rank_from_position=True)
    return [record["ticker"] for record in records]


def extract_universe_records_from_html_table(
    url: str,
    limit: int | None = None,
    rank_from_position: bool = False,
) -> list[dict]:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    for table in tables:
        ticker_col = pick_column(table, ["symbol", "ticker", "fund"])
        if ticker_col is None:
            continue
        name_col = pick_column(table, ["company", "company name", "security", "name", "fund name"])
        rank_col = pick_column(table, ["#", "rank"])
        records = []
        seen = set()
        for idx, row in table.iterrows():
            ticker = normalize_ticker(row.get(ticker_col, ""))
            if not ticker or ticker in seen:
                continue
            seen.add(ticker)
            rank = None
            if rank_col is not None:
                rank_value = row.get(rank_col)
                try:
                    rank = int(float(str(rank_value).replace(",", "")))
                except Exception:
                    rank = None
            elif rank_from_position:
                rank = len(records) + 1
            name = str(row.get(name_col, "")).strip() if name_col is not None else ""
            records.append({"ticker": ticker, "name": name, "rank": rank})
            if limit and len(records) >= limit:
                break
        if records:
            return records
    return []


def extract_ranked_etf_records_from_html_table(url: str, limit: int | None = None) -> list[dict]:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    for table in tables:
        ticker_col = pick_column(table, ["symbol", "ticker", "fund"])
        name_col = pick_column(table, ["fund name", "name", "fund"])
        asset_col = pick_column(table, ["assets", "aum"])
        if ticker_col is None:
            continue

        records = []
        seen = set()
        for _, row in table.iterrows():
            ticker = normalize_ticker(row.get(ticker_col, ""))
            if not ticker or ticker in seen:
                continue
            seen.add(ticker)
            name = str(row.get(name_col, "")).strip() if name_col is not None else ""
            assets = parse_asset_amount(row.get(asset_col)) if asset_col is not None else None
            records.append({"ticker": ticker, "name": name, "assets": assets})

        if not records:
            continue
        if any(record.get("assets") is not None for record in records):
            records.sort(key=lambda record: record.get("assets") or -1, reverse=True)
        for idx, record in enumerate(records, start=1):
            record["rank"] = idx
        return records[:limit] if limit else records

    return []


def try_extract_universe_records(
    key: str,
    url: str,
    limit: int | None = None,
    rank_from_position: bool = False,
) -> list[dict]:
    try:
        return extract_universe_records_from_html_table(url, limit, rank_from_position=rank_from_position)
    except Exception as exc:
        print(f"{key}: universe download failed ({format_error(exc)})", flush=True)
        return []


def try_extract_etf_records(key: str, url: str, limit: int | None = None) -> list[dict]:
    try:
        return extract_ranked_etf_records_from_html_table(url, limit)
    except Exception as exc:
        print(f"{key}: ETF universe download failed ({format_error(exc)})", flush=True)
        return []


def rank_label_for_universe(meta: dict, universe: str) -> str:
    ranks = meta.get("ranks") or {}
    if universe == "ETF":
        return str(meta.get("rank") or "")
    if universe == "S&P500,NASDAQ100":
        parts = []
        if ranks.get("S&P500"):
            parts.append(f"S{ranks['S&P500']}")
        if ranks.get("NASDAQ100"):
            parts.append(f"N{ranks['NASDAQ100']}")
        return "/".join(parts)
    if ranks.get(universe):
        return str(ranks[universe])
    return str(meta.get("rank") or "")


def rank_sort_value_for_universe(meta: dict, universe: str) -> int | None:
    ranks = meta.get("ranks") or {}
    if universe == "ETF":
        return meta.get("rank")
    if universe == "S&P500,NASDAQ100":
        values = [ranks.get("S&P500"), ranks.get("NASDAQ100")]
        values = [value for value in values if value is not None]
        return min(values) if values else meta.get("rank")
    return ranks.get(universe) or meta.get("rank")


def merge_stock_universes(sp500_tickers: list[str], nasdaq100_tickers: list[str]) -> tuple[list[str], dict[str, str]]:
    source_map: dict[str, list[str]] = {}
    for ticker in unique_tickers(sp500_tickers):
        source_map.setdefault(ticker, []).append("S&P500")
    for ticker in unique_tickers(nasdaq100_tickers):
        source_map.setdefault(ticker, []).append("NASDAQ100")

    merged = unique_tickers([*sp500_tickers, *nasdaq100_tickers])
    universe_map = {ticker: ",".join(source_map.get(ticker, ["Stock"])) for ticker in merged}
    return merged, universe_map


def merge_stock_metadata(sp500_records: list[dict], nasdaq_records: list[dict]) -> tuple[list[str], dict[str, str], dict[str, dict]]:
    sp500_tickers = [record["ticker"] for record in sp500_records]
    nasdaq_tickers = [record["ticker"] for record in nasdaq_records]
    merged, universe_map = merge_stock_universes(sp500_tickers, nasdaq_tickers)
    metadata: dict[str, dict] = {}
    for record in nasdaq_records:
        ticker = record["ticker"]
        metadata.setdefault(ticker, {}).setdefault("ranks", {})
        metadata[ticker].setdefault("company_name", record.get("name") or "")
        metadata[ticker]["ranks"]["NASDAQ100"] = record.get("rank")
    for record in sp500_records:
        ticker = record["ticker"]
        metadata.setdefault(ticker, {}).setdefault("ranks", {})
        if record.get("name"):
            metadata[ticker]["company_name"] = record.get("name")
        metadata[ticker]["ranks"]["S&P500"] = record.get("rank")
    for ticker, meta in metadata.items():
        universe = universe_map.get(ticker, "Stock")
        meta["rank"] = rank_sort_value_for_universe(meta, universe)
    return merged, universe_map, metadata


def load_universe(
    stocks_csv: str | None,
    etfs_csv: str | None,
    stock_limit: int,
    etf_limit: int,
) -> tuple[list[str], list[str], dict[str, str], dict[str, dict]]:
    metadata: dict[str, dict] = {}
    if stocks_csv:
        stock_tickers = load_tickers_from_csv(stocks_csv, stock_limit)
        stock_universe_map = {ticker: "CustomStock" for ticker in stock_tickers}
        for idx, ticker in enumerate(stock_tickers, start=1):
            metadata[ticker] = {"company_name": "", "rank": idx}
    else:
        sp500_records = try_extract_universe_records("sp500", DEFAULT_STOCK_URL, stock_limit)
        nasdaq_records = try_extract_universe_records("nasdaq100", DEFAULT_NASDAQ100_URL)
        if not nasdaq_records:
            nasdaq_records = try_extract_universe_records("nasdaq100_fallback", FALLBACK_NASDAQ100_URL)
        if not sp500_records:
            sp500_tickers = extract_tickers_with_cache("sp500_top", DEFAULT_STOCK_URL, stock_limit)
            sp500_records = [{"ticker": ticker, "name": "", "rank": idx} for idx, ticker in enumerate(sp500_tickers, start=1)]
        if not nasdaq_records:
            nasdaq_tickers = extract_tickers_with_cache("nasdaq100", FALLBACK_NASDAQ100_URL)
            nasdaq_records = [{"ticker": ticker, "name": "", "rank": None} for ticker in nasdaq_tickers]
        stock_tickers, stock_universe_map, metadata = merge_stock_metadata(sp500_records, nasdaq_records)

    if etfs_csv:
        etf_tickers = load_tickers_from_csv(etfs_csv, etf_limit)
        etf_records = [{"ticker": ticker, "name": DEFAULT_ETF_NAMES.get(ticker, ""), "rank": idx} for idx, ticker in enumerate(etf_tickers, start=1)]
    else:
        etf_records = try_extract_etf_records("etf_aum", DEFAULT_ETF_URL, etf_limit)
        if not etf_records:
            etf_records = [
                {"ticker": ticker, "name": DEFAULT_ETF_NAMES.get(ticker, ""), "rank": idx}
                for idx, ticker in enumerate(unique_tickers(DEFAULT_ETF_TICKERS)[:etf_limit], start=1)
            ]
        etf_tickers = [record["ticker"] for record in etf_records]
    for record in etf_records:
        ticker = record["ticker"]
        metadata[ticker] = {"company_name": record.get("name") or DEFAULT_ETF_NAMES.get(ticker, ""), "rank": record.get("rank")}

    return stock_tickers, etf_tickers, stock_universe_map, metadata


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


def fetch_current_quote(ticker: str) -> dict[str, float | None]:
    try:
        quote = yf.Ticker(ticker)
        info = quote.fast_info
        price = fast_info_value(
            info,
            ["last_price", "lastPrice", "regular_market_price", "regularMarketPrice"],
        )
        previous_close = fast_info_value(
            info,
            ["regular_market_previous_close", "regularMarketPreviousClose", "previous_close", "previousClose"],
        )

        if price is None:
            intraday = quote.history(period="1d", interval="1m").dropna(how="all")
            if not intraday.empty and "Close" in intraday.columns:
                price = parse_float(intraday["Close"].dropna().iloc[-1])

        change_pct = None
        if price is not None and previous_close not in {None, 0}:
            change_pct = round((price / previous_close - 1) * 100, 2)

        return {
            "price": round(price, 2) if price is not None else None,
            "price_change_pct": change_pct,
        }
    except Exception as exc:
        print(f"    {ticker}: quote failed ({format_error(exc)})", flush=True)
        return {"price": None, "price_change_pct": None}


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


def row_for_exact_date(df: pd.DataFrame, target_date: pd.Timestamp) -> pd.Series | None:
    if df.empty or "Date" not in df.columns:
        return None

    df = normalize_date_column(df)
    dates = df["Date"]
    eligible = df.loc[dates == target_date].copy()
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
    ticker_metadata: dict[str, dict] | None = None,
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
        row = row_for_exact_date(processed, target_date)
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
        universe = "ETF" if is_etf else (stock_universe_map or {}).get(ticker, "Stock")
        meta = (ticker_metadata or {}).get(ticker, {})
        display_rank = rank_label_for_universe(meta, universe)
        sort_rank = rank_sort_value_for_universe(meta, universe)
        current_quote = fetch_current_quote(ticker)

        results.append(
            {
                "date": actual_date,
                "asset_type": "ETF" if is_etf else "Stock",
                "universe": universe,
                "rank": display_rank,
                "_sort_rank": sort_rank,
                "ticker": ticker,
                "company_name": meta.get("company_name", ""),
                "price": current_quote.get("price"),
                "price_change_pct": current_quote.get("price_change_pct"),
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
    ticker_metadata: dict[str, dict],
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
                ticker_metadata=ticker_metadata,
                progress_start=batch_start,
                progress_total=len(tickers),
            )
            all_results.extend(batch_results)
            batch_start += len(batch)
            if used_yahoo and pause_seconds > 0:
                time.sleep(pause_seconds)

    columns = [
        "scan_timestamp_ct",
        "date",
        "asset_type",
        "universe",
        "rank",
        "ticker",
        "company_name",
        "price",
        "price_change_pct",
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
    df["_display_rank"] = pd.to_numeric(df.get("_sort_rank"), errors="coerce").fillna(999999)
    df = df.sort_values(["date", "_rank", "asset_type", "_display_rank", "ticker"], ascending=[False, True, True, True, True])
    return df.drop(columns=["_rank", "_display_rank", "_sort_rank"]).reset_index(drop=True)


def daily_output_path(target_date: pd.Timestamp) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"signal_scan_{target_date:%Y%m%d}.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan large-cap stocks and ETFs for Puddle / RSI & Puddle signals."
    )
    parser.add_argument("--date", help="Scan date in YYYY-MM-DD. Defaults to today in America/Chicago.")
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
    scan_timestamp_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    scan_timestamp_ct = scan_timestamp_utc.astimezone(CENTRAL_TZ)
    YF_REQUEST_PAUSE_SECONDS = max(0.0, args.request_pause)
    YF_RETRIES = max(0, args.retries)
    YF_RETRY_PAUSE_SECONDS = max(0.0, args.retry_pause)
    CACHE_DIR = Path(args.cache_dir).expanduser()
    CACHE_MAX_HOURS = max(0.0, args.cache_max_hours)
    REFRESH_CACHE = bool(args.refresh_cache)
    target_date = pd.Timestamp(args.date or scan_timestamp_ct.date()).normalize()
    print(f"Scan timestamp CT:  {scan_timestamp_ct.isoformat()}", flush=True)
    print(f"Scan timestamp UTC: {scan_timestamp_utc.isoformat()}", flush=True)
    print(f"Yahoo cache: {CACHE_DIR}", flush=True)

    stock_tickers, etf_tickers, stock_universe_map, ticker_metadata = load_universe(
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
            ticker_metadata=ticker_metadata,
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

    result.insert(0, "scan_timestamp_ct", scan_timestamp_ct.isoformat())

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
