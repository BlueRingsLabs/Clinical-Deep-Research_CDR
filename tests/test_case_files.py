"""Every Case File in eval/cases/ must be valid. See docs/case-files.md."""

import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "eval" / "cases"
SCHEMA = json.loads((ROOT / "schemas" / "case_file.schema.json").read_text())
CASE_PATHS = sorted(CASES_DIR.glob("*.json"))


def test_there_are_case_files():
    assert CASE_PATHS, "eval/cases/ should contain at least one case"


@pytest.mark.parametrize("path", CASE_PATHS, ids=lambda p: p.name)
def test_case_matches_schema(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(case, SCHEMA)


@pytest.mark.parametrize("path", CASE_PATHS, ids=lambda p: p.name)
def test_filename_starts_with_case_id(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    assert path.name.startswith(case["id"] + "-"), (
        f"{path.name} should be named '{case['id']}-<short-slug>.json'"
    )


def test_case_ids_are_unique():
    ids = [json.loads(p.read_text(encoding="utf-8"))["id"] for p in CASE_PATHS]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"Duplicate case IDs: {sorted(duplicates)}"


def test_eval_runner_loads_the_cases_directory():
    spec = importlib.util.spec_from_file_location("eval_runner", ROOT / "eval" / "eval_runner.py")
    eval_runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eval_runner)

    questions, _ = eval_runner.load_dataset(str(CASES_DIR))
    assert len(questions) == len(CASE_PATHS)
