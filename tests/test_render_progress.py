from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = REPO_ROOT / "skills" / "progress-logging" / "scripts" / "init_progress.py"
USAGE_SCRIPT = REPO_ROOT / "skills" / "progress-logging" / "scripts" / "record_usage.py"
PROGRESS_SCRIPT = REPO_ROOT / "skills" / "progress-logging" / "scripts" / "record_progress.py"
RENDER_SCRIPT = REPO_ROOT / "skills" / "progress-logging" / "scripts" / "render_progress.py"


def test_end_to_end_progress_dashboard_smoke(tmp_path: Path) -> None:
    work = tmp_path / "work"
    progress = work / "progress.tsv"
    log = work / "log.md"
    state = work / "state.json"
    svg = work / "progress.svg"
    html = work / "dashboard.html"

    subprocess.run(
        [sys.executable, str(INIT_SCRIPT), "--work-dir", str(work), "--metric", "cycles", "--direction", "lower", "--candidate-number"],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(USAGE_SCRIPT),
            "--log",
            str(log),
            "--state",
            str(state),
            "--timestamp",
            "2026-06-01T00:00:00Z",
            "--label",
            "cand_0000",
            "--tokens-total",
            "1000",
            "--input-tokens",
            "800",
            "--output-tokens",
            "200",
            "--wall-seconds",
            "0",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PROGRESS_SCRIPT),
            "--progress",
            str(progress),
            "--timestamp",
            "2026-06-01T00:00:00Z",
            "--candidate",
            "cand_0000",
            "--candidate-number",
            "0",
            "--metric",
            "cycles=3000",
            "--decision",
            "baseline",
            "--tokens-total",
            "1000",
            "--wall-seconds",
            "0",
            "--label",
            "baseline",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(USAGE_SCRIPT),
            "--log",
            str(log),
            "--state",
            str(state),
            "--timestamp",
            "2026-06-01T00:05:00Z",
            "--label",
            "cand_0001",
            "--tokens-total",
            "2400",
            "--cached-input-tokens",
            "500",
            "--wall-seconds",
            "300",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PROGRESS_SCRIPT),
            "--progress",
            str(progress),
            "--timestamp",
            "2026-06-01T00:05:00Z",
            "--candidate",
            "cand_0001",
            "--candidate-number",
            "1",
            "--metric",
            "cycles=2226",
            "--decision",
            "promote",
            "--tokens-total",
            "2400",
            "--wall-seconds",
            "300",
            "--label",
            "first win",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(RENDER_SCRIPT),
            str(progress),
            "--chart-output",
            str(svg),
            "--dashboard-output",
            str(html),
            "--log",
            str(log),
            "--state",
            str(state),
            "--title",
            "Cycles",
            "--ylabel",
            "cycles",
            "--direction",
            "lower",
            "--generated-at",
            "2026-06-01T00:06:00Z",
        ],
        check=True,
    )

    svg_text = svg.read_text(encoding="utf-8")
    html_text = html.read_text(encoding="utf-8")
    assert "<svg" in svg_text
    assert "Cycles With Tokens" in svg_text
    assert "Recorded Token Usage" in svg_text
    assert "https://github.com/josusanmartin/progress-logging-skill" in svg_text
    assert "first win" in html_text
    assert "explicit get_goal snapshots" in html_text
    assert "current usage snapshot: 2k tokens" in html_text
