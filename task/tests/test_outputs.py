"""Pytest verifier for the sensor log decoder task.

Runs the agent's fixed decoder against a held-out .slog file
and checks timestamp correctness.
"""
import json, os, shutil, subprocess, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = "/app/output/sensorlog"
AGENT_OUTPUT = "/app/output/decoded.json"
HELDOUT_SLOG = "/tests/expected/heldout.slog"
EXPECTED_JSON = "/tests/expected/expected_output.json"


@pytest.fixture(scope="module")
def run_agent():
    """Replace sample file with held-out, run agent's script."""
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)
    shutil.copy2(HELDOUT_SLOG, "/app/data/sample.slog")
    return subprocess.run(["python3", AGENT_SCRIPT], capture_output=True, text=True, timeout=30)


def test_script_exists():
    """Agent must produce /app/output/sensorlog."""
    assert Path(AGENT_SCRIPT).exists()


def test_script_runs(run_agent):
    """Script must exit 0 on held-out data."""
    assert run_agent.returncode == 0, f"Exit {run_agent.returncode}\n{run_agent.stderr}"


def test_output_exists():
    """Script must produce decoded.json."""
    assert Path(AGENT_OUTPUT).exists()


def test_record_count(run_agent):
    """Output must have exactly 1024 records."""
    actual = json.loads(Path(AGENT_OUTPUT).read_text())
    expected = json.loads(Path(EXPECTED_JSON).read_text())
    assert len(actual) == len(expected), f"Got {len(actual)} records, expected {len(expected)}"


def test_timestamps_match(run_agent):
    """Every record's timestamp must match the golden reference exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_expected = os.path.join(tmp, "expected.json")
        shutil.copy2(EXPECTED_JSON, tmp_expected)
        expected = json.loads(Path(tmp_expected).read_text(encoding="utf-8"))
        actual = json.loads(Path(AGENT_OUTPUT).read_text(encoding="utf-8"))

    failures = []
    for i, (exp, act) in enumerate(zip(expected, actual)):
        if exp["timestamp"] != act["timestamp"]:
            failures.append(
                f"Record {i}: expected ts={exp['timestamp']}, got {act['timestamp']} "
                f"(off by {exp['timestamp'] - act['timestamp']}s)"
            )
    assert not failures, f"{len(failures)} timestamp mismatches:\n" + "\n".join(failures[:5])
