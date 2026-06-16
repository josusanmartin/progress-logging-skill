#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


TOKEN_FIELDS = [
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_timestamp(value: str | None) -> str:
    if not value:
        return utc_now()
    text = value.strip()
    candidate = f"{text[:-1]}+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SystemExit("--timestamp must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_cell(value: str | None, source: str, *, allow_empty: bool = True) -> str:
    text = "" if value is None else value.strip()
    if not text and not allow_empty:
        raise SystemExit(f"{source} cannot be empty")
    if any(ch in text for ch in "\t\r\n"):
        raise SystemExit(f"{source} cannot contain tabs or newlines")
    return text


def decimal_value(value: str, source: str) -> Decimal:
    try:
        number = Decimal(value.replace(",", ""))
    except InvalidOperation as exc:
        raise SystemExit(f"{source} must be numeric") from exc
    if not number.is_finite():
        raise SystemExit(f"{source} must be finite")
    return number


def numeric(value: str | None, source: str) -> Decimal | None:
    text = clean_cell(value, source)
    if not text:
        return None
    return decimal_value(text, source)


def json_number(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    if value == value.to_integral():
        return int(value)
    return float(value)


def read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "progress": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def previous_total(state: dict[str, Any]) -> Decimal | None:
    progress = state.get("progress")
    if not isinstance(progress, dict):
        return None
    snapshot = progress.get("latest_usage_snapshot")
    if not isinstance(snapshot, dict):
        return None
    value = snapshot.get("total_tokens")
    if value is None or value == "":
        return None
    return decimal_value(str(value), "previous total_tokens")


def token_delta(args: argparse.Namespace, state: dict[str, Any], total_tokens: Decimal | None) -> Decimal | None:
    explicit = numeric(args.tokens_delta, "--tokens-delta")
    if explicit is not None or total_tokens is None:
        return explicit
    previous = previous_total(state)
    if previous is None:
        return None
    return total_tokens - previous


def snapshot(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    timestamp = utc_timestamp(args.timestamp)
    total_tokens = numeric(args.tokens_total, "--tokens-total")
    snap: dict[str, Any] = {
        "source": "get_goal",
        "recorded_at": timestamp,
        "timestamp": timestamp,
        "label": clean_cell(args.label, "--label", allow_empty=False),
        "wall_seconds": json_number(numeric(args.wall_seconds, "--wall-seconds")),
        "total_tokens": json_number(total_tokens),
        "tokens_delta": json_number(token_delta(args, state, total_tokens)),
    }
    for cli_name, field_name in [
        ("input_tokens", "input_tokens"),
        ("cached_input_tokens", "cached_input_tokens"),
        ("output_tokens", "output_tokens"),
        ("reasoning_output_tokens", "reasoning_output_tokens"),
        ("cache_creation_input_tokens", "cache_creation_input_tokens"),
        ("cache_read_input_tokens", "cache_read_input_tokens"),
    ]:
        snap[field_name] = json_number(numeric(getattr(args, cli_name), f"--{cli_name.replace('_', '-')}"))
    if all(snap.get(key) is None for key in ["wall_seconds", "total_tokens", *TOKEN_FIELDS]):
        raise SystemExit("record_usage.py needs at least one token or wall-time field")
    return snap


def append_log(path: Path, snap: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Progress Log\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {snap['recorded_at']} :: get_goal usage snapshot :: {snap['label']}\n\n")
        f.write(json.dumps(snap, sort_keys=True, separators=(",", ":")))
        f.write("\n")


def write_state(path: Path, state: dict[str, Any], snap: dict[str, Any]) -> None:
    progress = state.setdefault("progress", {})
    if not isinstance(progress, dict):
        raise SystemExit("state.progress must be a JSON object")
    progress["latest_usage_snapshot"] = snap
    progress["tokens_total"] = snap.get("total_tokens")
    progress["wall_seconds"] = snap.get("wall_seconds")
    state["last_updated"] = snap["recorded_at"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append an explicit get_goal token usage snapshot to work/log.md and state.json.")
    parser.add_argument("--log", type=Path, default=Path("work/log.md"))
    parser.add_argument("--state", type=Path, default=Path("work/state.json"))
    parser.add_argument("--timestamp")
    parser.add_argument("--label", default="snapshot")
    parser.add_argument("--wall-seconds")
    parser.add_argument("--tokens-total")
    parser.add_argument("--tokens-delta")
    parser.add_argument("--input-tokens")
    parser.add_argument("--cached-input-tokens")
    parser.add_argument("--output-tokens")
    parser.add_argument("--reasoning-output-tokens")
    parser.add_argument("--cache-creation-input-tokens")
    parser.add_argument("--cache-read-input-tokens")
    args = parser.parse_args()

    state = read_state(args.state)
    snap = snapshot(args, state)
    append_log(args.log, snap)
    write_state(args.state, state, snap)
    print(args.log)
    print(args.state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
