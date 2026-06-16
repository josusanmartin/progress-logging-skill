from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SRC = REPO_ROOT / "skills" / "progress-logging"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_skill.py"

spec = importlib.util.spec_from_file_location("validate_skill", VALIDATOR_PATH)
assert spec is not None
validate_skill = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validate_skill)


def copy_skill(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "progress-logging"
    shutil.copytree(SKILL_SRC, skill_dir)
    return skill_dir


def test_valid_skill_passes(tmp_path: Path) -> None:
    validate_skill.validate_skill(copy_skill(tmp_path))


def test_missing_openai_yaml_is_structured_error(tmp_path: Path) -> None:
    skill_dir = copy_skill(tmp_path)
    (skill_dir / "agents" / "openai.yaml").unlink()

    with pytest.raises(validate_skill.ValidationError, match="missing required file: agents/openai.yaml"):
        validate_skill.validate_skill(skill_dir)


def test_invalid_skill_frontmatter_yaml_fails(tmp_path: Path) -> None:
    skill_dir = copy_skill(tmp_path)
    skill = skill_dir / "SKILL.md"
    skill.write_text("---\nname: [unterminated\ndescription: bad\n---\n# Body\n", encoding="utf-8")

    with pytest.raises(validate_skill.ValidationError, match="frontmatter is invalid YAML"):
        validate_skill.validate_skill(skill_dir)


@pytest.mark.parametrize("script_name", validate_skill.REQUIRED_SKILL_SCRIPTS)
def test_missing_skill_script_fails(tmp_path: Path, script_name: str) -> None:
    skill_dir = copy_skill(tmp_path)
    (skill_dir / "scripts" / script_name).unlink()

    with pytest.raises(validate_skill.ValidationError, match=f"missing required file: scripts/{script_name}"):
        validate_skill.validate_skill(skill_dir)
