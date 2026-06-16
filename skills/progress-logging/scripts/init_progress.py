#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_text(path: Path, text: str, force: bool) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def progress_header(metric: str, candidate_number: bool) -> str:
    columns = ["timestamp", "candidate"]
    if candidate_number:
        columns.append("candidate_number")
    columns.extend([metric, "decision", "tokens_total", "tokens_delta", "wall_seconds", "label"])
    return "\t".join(columns) + "\n"


def state_json(args: argparse.Namespace, timestamp: str) -> str:
    data = {
        "schema_version": 1,
        "created_at": timestamp,
        "last_updated": timestamp,
        "metric": args.metric,
        "direction": args.direction,
        "progress": {
            "table": str(args.work_dir / "progress.tsv"),
            "log": str(args.work_dir / "log.md"),
            "state": str(args.work_dir / "state.json"),
            "chart": str(args.work_dir / "progress.svg"),
            "dashboard": str(args.work_dir / "dashboard.html"),
            "usage_source": "explicit get_goal snapshots in work/log.md",
            "latest_usage_snapshot": {
                "source": "get_goal",
                "recorded_at": None,
                "label": None,
                "wall_seconds": None,
                "total_tokens": None,
                "tokens_delta": None,
                "input_tokens": None,
                "cached_input_tokens": None,
                "output_tokens": None,
                "reasoning_output_tokens": None,
                "cache_creation_input_tokens": None,
                "cache_read_input_tokens": None,
            },
        },
    }
    if args.target is not None:
        data["target_score"] = args.target
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def log_md(args: argparse.Namespace, timestamp: str) -> str:
    return f"""# Progress Log

## {timestamp} :: progress_log_initialized

- metric: {args.metric}
- direction: {args.direction}
- token source: explicit get_goal snapshots recorded with scripts/record_usage.py
- score rows: scripts/record_progress.py
- render command: scripts/render_progress.py
"""


def placeholder_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720" role="img">
<rect width="100%" height="100%" fill="#fbfbf7"/>
<rect x="92" y="72" width="943" height="318" fill="#f9fafb" stroke="#e5e7eb"/>
<rect x="92" y="475" width="943" height="165" fill="#fffbeb" stroke="#fde68a"/>
<text x="560" y="170" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="700" fill="#17202a">Progress chart waiting for first measurement</text>
<text x="560" y="205" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#697386">Append rows with scripts/record_progress.py.</text>
<text x="560" y="555" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#92400e">Record get_goal snapshots with scripts/record_usage.py.</text>
</svg>
"""


def placeholder_dashboard() -> str:
    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Progress Dashboard</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;background:#f7f7f2;color:#17202a;margin:40px">
<main style="max-width:860px;margin:auto;background:#fff;border:1px solid #ded8cc;border-radius:8px;padding:28px">
<h1>Progress Dashboard</h1>
<p>Waiting for the first measurement.</p>
<p>Use <code>scripts/record_usage.py</code>, then <code>scripts/record_progress.py</code>, then <code>scripts/render_progress.py</code>.</p>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize progress logging artifacts.")
    parser.add_argument("--work-dir", type=Path, default=Path("work"))
    parser.add_argument("--metric", default="score")
    parser.add_argument("--direction", choices=("lower", "higher"), default="lower")
    parser.add_argument("--target", type=float)
    parser.add_argument("--candidate-number", action="store_true", help="Include candidate_number column in progress.tsv")
    parser.add_argument("--force", action="store_true", help="Overwrite existing progress artifacts")
    args = parser.parse_args()

    timestamp = utc_now()
    files = {
        args.work_dir / "progress.tsv": progress_header(args.metric, args.candidate_number),
        args.work_dir / "log.md": log_md(args, timestamp),
        args.work_dir / "state.json": state_json(args, timestamp),
        args.work_dir / "progress.svg": placeholder_svg(),
        args.work_dir / "dashboard.html": placeholder_dashboard(),
    }
    written = []
    skipped = []
    for path, text in files.items():
        if write_text(path, text, args.force):
            written.append(str(path))
        else:
            skipped.append(str(path))
    print(json.dumps({"written": written, "skipped_existing": skipped}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
