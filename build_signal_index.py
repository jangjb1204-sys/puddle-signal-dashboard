from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


SCAN_DIR = Path(__file__).resolve().parent / "signal_scans"
RAW_BASE_URL = "https://raw.githubusercontent.com/jangjb1204-sys/puddle-signal-dashboard/main/signal_scans"


def build_index() -> list[dict]:
    rows = []
    for path in sorted(SCAN_DIR.glob("signal_scan_*.csv")):
        raw = path.stem.replace("signal_scan_", "")
        try:
            scan_date = pd.to_datetime(raw, format="%Y%m%d").date()
        except Exception:
            continue
        rows.append(
            {
                "date": scan_date.isoformat(),
                "filename": path.name,
                "url": f"{RAW_BASE_URL}/{path.name}",
                "size": path.stat().st_size,
                "mtime_ns": path.stat().st_mtime_ns,
            }
        )
    return rows


def main() -> None:
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    index_path = SCAN_DIR / "index.json"
    index_path.write_text(json.dumps(build_index(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
