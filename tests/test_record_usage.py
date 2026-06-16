from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
USAGE_SCRIPT = REPO_ROOT / "skills" / "progress-logging" / "scripts" / "record_usage.py"


def run_record_usage(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(USAGE_SCRIPT), *args],
        check=True,
        text=True,
        capture_output=True,
    )


def json_snapshots(log: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.startswith("{") and line.endswith("}")
    ]


def test_record_usage_normalizes_utc_and_records_granular_fields(tmp_path: Path) -> None:
    log = tmp_path / "work" / "log.md"
    state = tmp_path / "work" / "state.json"

    run_record_usage(
        "--log",
        str(log),
        "--state",
        str(state),
        "--timestamp",
        "2026-06-01T02:18:00+02:00",
        "--label",
        "cand_0007",
        "--wall-seconds",
        "1080",
        "--tokens-total",
        "4500",
        "--input-tokens",
        "3200",
        "--cached-input-tokens",
        "1400",
        "--output-tokens",
        "900",
        "--reasoning-output-tokens",
        "400",
        "--cache-creation-input-tokens",
        "600",
        "--cache-read-input-tokens",
        "800",
    )

    snapshot = json.loads(state.read_text(encoding="utf-8"))["progress"]["latest_usage_snapshot"]
    assert snapshot == {
        "cache_creation_input_tokens": 600,
        "cache_read_input_tokens": 800,
        "cached_input_tokens": 1400,
        "input_tokens": 3200,
        "label": "cand_0007",
        "output_tokens": 900,
        "reasoning_output_tokens": 400,
        "recorded_at": "2026-06-01T00:18:00Z",
        "source": "get_goal",
        "timestamp": "2026-06-01T00:18:00Z",
        "tokens_delta": None,
        "total_tokens": 4500,
        "wall_seconds": 1080,
    }
    assert "2026-06-01T00:18:00Z :: get_goal usage snapshot :: cand_0007" in log.read_text(encoding="utf-8")
    assert json_snapshots(log)[0]["total_tokens"] == 4500


def test_record_usage_computes_token_delta_from_previous_state(tmp_path: Path) -> None:
    log = tmp_path / "work" / "log.md"
    state = tmp_path / "work" / "state.json"

    run_record_usage("--log", str(log), "--state", str(state), "--label", "first", "--tokens-total", "1000")
    run_record_usage("--log", str(log), "--state", str(state), "--label", "second", "--tokens-total", "2400")

    snapshots = json_snapshots(log)
    assert snapshots[-1]["tokens_delta"] == 1400
    latest = json.loads(state.read_text(encoding="utf-8"))["progress"]["latest_usage_snapshot"]
    assert latest["tokens_delta"] == 1400


def test_record_usage_requires_token_or_wall_time_field(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(USAGE_SCRIPT),
            "--log",
            str(tmp_path / "log.md"),
            "--state",
            str(tmp_path / "state.json"),
            "--label",
            "empty",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "needs at least one token or wall-time field" in result.stderr


def test_record_usage_rejects_multiline_label(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(USAGE_SCRIPT),
            "--log",
            str(tmp_path / "log.md"),
            "--state",
            str(tmp_path / "state.json"),
            "--label",
            "one\ntwo",
            "--tokens-total",
            "1000",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "--label cannot contain tabs or newlines" in result.stderr
