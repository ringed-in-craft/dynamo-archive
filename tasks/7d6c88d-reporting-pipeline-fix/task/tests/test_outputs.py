"""Pytest verifier for the reporting pipeline task.

The verifier gets the agent's fixed script as an artifact,
runs it against a held-out database, and checks the output.
"""
import csv
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


AGENT_FIXED_SCRIPT = "/app/output/generate_report.py"
AGENT_OUTPUT = "/app/output/report.csv"
HELDOUT_DB = "/tests/expected/heldout_db.sqlite"
EXPECTED_CSV = "/tests/expected/expected_report.csv"
TARGET_DB = "/app/data/sample_db.sqlite"


def _load_csv(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(tuple(row))
    return rows


@pytest.fixture(scope="module")
def run_fixed_script():
    """Replace sample DB with held-out, run the agent's fixed script."""
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)

    shutil.copy2(HELDOUT_DB, TARGET_DB)

    result = subprocess.run(
        ["python3", AGENT_FIXED_SCRIPT],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


def test_fixed_script_exists():
    """The agent must produce /app/output/generate_report.py."""
    assert Path(AGENT_FIXED_SCRIPT).exists(), f"{AGENT_FIXED_SCRIPT} not found"
    assert os.access(AGENT_FIXED_SCRIPT, os.R_OK), f"{AGENT_FIXED_SCRIPT} not readable"


def test_fixed_script_runs(run_fixed_script):
    """The fixed script must exit with code 0 on the held-out database."""
    assert run_fixed_script.returncode == 0, (
        f"Script exited {run_fixed_script.returncode}\n"
        f"stdout: {run_fixed_script.stdout}\nstderr: {run_fixed_script.stderr}"
    )


def test_report_exists():
    """The script must produce /app/output/report.csv."""
    assert Path(AGENT_OUTPUT).exists(), f"{AGENT_OUTPUT} not found"


def test_report_matches_golden(run_fixed_script):
    """The report CSV must exactly match the golden reference."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_expected = os.path.join(tmpdir, "expected.csv")
        shutil.copy2(EXPECTED_CSV, tmp_expected)

        expected = _load_csv(tmp_expected)
        actual = _load_csv(AGENT_OUTPUT)

        assert len(actual) == len(expected), (
            f"Row count mismatch: got {len(actual)}, expected {len(expected)}"
        )
        for i, (exp_row, act_row) in enumerate(zip(expected, actual)):
            assert act_row == exp_row, (
                f"Row {i} mismatch:\n  expected: {exp_row}\n  got:      {act_row}"
            )
