from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time

from new8021x.eapol import observe_eapol, render_observation_report
from new8021x.report import write_json, write_report


def run_observation_loop(
    iface: str,
    window_seconds: int,
    interval_seconds: int,
    output_dir: str,
    cycles: int | None = None,
) -> None:
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if interval_seconds < 0:
        raise ValueError("interval_seconds cannot be negative")

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    cycle = 0
    while cycles is None or cycle < cycles:
        cycle += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        basename = f"observe-{timestamp}"

        summary = observe_eapol(iface=iface, duration_seconds=window_seconds)
        markdown_path = output_root / f"{basename}.md"
        json_path = output_root / f"{basename}.json"

        write_report(str(markdown_path), render_observation_report(summary))
        write_json(str(json_path), summary.to_dict())

        print(f"[cycle {cycle}] wrote {markdown_path} and {json_path}")

        if cycles is not None and cycle >= cycles:
            break
        if interval_seconds:
            time.sleep(interval_seconds)
