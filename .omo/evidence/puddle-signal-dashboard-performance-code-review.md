# Puddle Signal Dashboard Performance Diff Code Review

## Verdict

- codeQualityStatus: BLOCK
- recommendation: REQUEST_CHANGES
- reportPath: .omo/evidence/puddle-signal-dashboard-performance-code-review.md
- blockers:
  - `puddle_rsi_signal_scanner.py:688` / `puddle_rsi_signal_scanner.py:691` / `puddle_rsi_signal_scanner.py:699` do not preserve rate-limit abort behavior for `yf.download` batch failures that yfinance records as empty per-ticker frames instead of raising.

## Skill-Perspective Check

- `omo:remove-ai-slops` consulted: yes. Applied overfit/slop review to changed production code and tests.
- `omo:programming` consulted: yes. Loaded the Python reference and applied its review criteria pragmatically to this existing pandas/yfinance script.
- Skill violations affecting approval: yes. The new tests are meaningful for the happy path, but they overfit to successful `yf.download` MultiIndex output and do not cover the high-risk yfinance error channel. The production diff also adds broad empty-frame normalization without parsing yfinance's batch error boundary, which creates false confidence around rate-limit behavior.

## Findings

### CRITICAL

None.

### HIGH

1. Rate-limit failures from batched `yf.download` can be silently converted into "no data" instead of stopping the scan.

   References:
   - `puddle_rsi_signal_scanner.py:688` calls the batch download.
   - `puddle_rsi_signal_scanner.py:691` normalizes each returned ticker frame.
   - `puddle_rsi_signal_scanner.py:692` through `puddle_rsi_signal_scanner.py:700` treat an empty ticker frame as stale cache or no data.
   - `puddle_rsi_signal_scanner.py:718` through `puddle_rsi_signal_scanner.py:729` only raise `YahooRateLimitError` if the outer batch call raises.

   Why this blocks approval:
   - The old per-ticker path used `yf.Ticker(...).history()`, whose yfinance implementation re-raises `YFRateLimitError`; `fetch_history_with_retries()` then raises `YahooRateLimitError` when no stale cache exists.
   - The new `yf.download()` path calls yfinance's internal per-ticker history with `raise_errors=True`, but `yf.download()` catches those per-ticker exceptions, stores them in `yfinance.shared._ERRORS`, and returns empty frames to the caller.
   - The scanner does not inspect that yfinance batch error channel, so a whole rate-limited uncached batch can be recorded as empty Yahoo frames. The workflow can then continue and write a misleading incomplete or empty signal CSV instead of failing fast.

   Evidence:
   - `python -m unittest discover -s tests -v` passed, but the tests only cover successful batch downloads.
   - `python -m py_compile puddle_rsi_signal_scanner.py tests/test_scanner_batching.py` passed.
   - Local reproduction using a yfinance-shaped batch result with `yfinance.shared._ERRORS` containing `YFRateLimitError(...)` returned `{'AAA': (True, 'yahoo'), 'BBB': (True, 'yahoo')}` from `fetch_batch_stock_data()` instead of raising `YahooRateLimitError`.
   - Control reproduction of the old per-ticker retry function with a rate-limit exception raised `YahooRateLimitError`.

### MEDIUM

None.

### LOW

1. Test coverage is too narrow for the changed risk surface.

   References:
   - `tests/test_scanner_batching.py:30` covers successful stock batch download.
   - `tests/test_scanner_batching.py:57` covers successful common market batch download.

   These tests are relevant, not deletion-only or tautological, but they miss partial failures, all-empty batch errors, stale-cache fallback after yfinance batch errors, and the actual yfinance `shared._ERRORS` behavior. This is low by itself but supports the high-severity production finding.

## Scope And Evidence Checked

- Inspected diff for:
  - `puddle_rsi_signal_scanner.py`
  - `.github/workflows/update-signals.yml`
  - `tests/test_scanner_batching.py`
- Verified commands:
  - `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`
  - `PYTHONDONTWRITEBYTECODE=1 python -m py_compile puddle_rsi_signal_scanner.py tests/test_scanner_batching.py`
  - `git diff --check -- puddle_rsi_signal_scanner.py .github/workflows/update-signals.yml tests/test_scanner_batching.py`
- Inspected generated CSV evidence at `signal_scans/signal_scan_20260623.csv`; it exists and contains signal rows, but this cached-success artifact does not exercise the blocking uncached rate-limit path.
