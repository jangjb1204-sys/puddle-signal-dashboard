# Puddle Signal Dashboard

Streamlit dashboard for scanning top stocks and ETFs for Puddle and RSI & Puddle signals.

## Run locally

```bash
streamlit run app.py
```

## Files

- `app.py`: Streamlit dashboard
- `puddle_rsi_signal_scanner.py`: scanner, signal logic, and Yahoo cache
- `requirements.txt`: deployment dependencies

## Cache

Yahoo price data is cached in `.puddle_yf_cache/`. The cache folder is ignored by Git.

## Deploy

On Streamlit Community Cloud, set the main file path to:

```text
app.py
```
