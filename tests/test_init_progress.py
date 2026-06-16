from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = REPO_ROOT / "skills" / "progress-logging" / "scripts" / "init_progress.py"


def test_init_progress_creates_canonical_artifacts(tmp_path: Path) -> None:
    work = tmp_path / "work"

    result = subprocess.run(
        [
            sys.executable,
            str(INIT_SCRIPT),
            "--work-dir",
            str(work),
            "--metric",
            "cycles",
            "--direction",
            "lower",
            "--target",
            "1000",
            "--candidate-number",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    created = json.loads(result.stdout)
    assert str(work / "progress.tsv") in created["written"]
    assert (work / "progress.tsv").read_text(encoding="utf-8") == (
        "timestamp\tcandidate\tcandidate_number\tcycles\tdecision\ttokens_total\ttokens_delta\twall_seconds\tlabel\n"
    )
    state = json.loads((work / "state.json").read_text(encoding="utf-8"))
    assert state["metric"] == "cycles"
    assert state["direction"] == "lower"
    assert state["target_score"] == 1000.0
    assert state["progress"]["latest_usage_snapshot"]["total_tokens"] is None
    assert "progress_log_initialized" in (work / "log.md").read_text(encoding="utf-8")
    assert "record_progress.py" in (work / "progress.svg").read_text(encoding="utf-8")
    assert "Progress Dashboard" in (work / "dashboard.html").read_text(encoding="utf-8")


def test_init_progress_does_not_overwrite_without_force(tmp_path: Path) -> None:
    work = tmp_path / "work"
    subprocess.run([sys.executable, str(INIT_SCRIPT), "--work-dir", str(work)], check=True)
    (work / "progress.tsv").write_text("custom\n", encoding="utf-8")

    subprocess.run([sys.executable, str(INIT_SCRIPT), "--work-dir", str(work)], check=True)

    assert (work / "progress.tsv").read_text(encoding="utf-8") == "custom\n"


def test_init_progress_force_overwrites(tmp_path: Path) -> None:
    work = tmp_path / "work"
    subprocess.run([sys.executable, str(INIT_SCRIPT), "--work-dir", str(work)], check=True)
    (work / "progress.tsv").write_text("custom\n", encoding="utf-8")

    subprocess.run([sys.executable, str(INIT_SCRIPT), "--work-dir", str(work), "--force"], check=True)

    assert (work / "progress.tsv").read_text(encoding="utf-8").startswith("timestamp\tcandidate\tscore\t")
