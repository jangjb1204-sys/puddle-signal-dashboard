from pathlib import Path

path = Path('puddle_rsi_signal_scanner.py')
text = path.read_text()
target = "    stock_universe_map: dict[str, str] | None = None,\n    progress_start: int = 0,"
replacement = "    stock_universe_map: dict[str, str] | None = None,\n    ticker_metadata: dict[str, dict] | None = None,\n    progress_start: int = 0,"

if replacement in text:
    print('Already patched')
elif target in text:
    path.write_text(text.replace(target, replacement, 1))
    print('Patched scan_batch signature')
else:
    raise SystemExit('Target signature block not found')
