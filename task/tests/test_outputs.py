"""Pytest verifier for the sensor log reverse-engineering task.

Runs the agent's decoder against a held-out file and compares output
against a pre-computed golden reference (stored in tests/, never in the agent image).
"""
import json, os, shutil, subprocess, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = "/app/output/sensorlog"
AGENT_OUTPUT = "/app/output/decoded.json"
HELDOUT_SLOG = "/tests/expected/heldout.slog"
GOLDEN_JSON = "/tests/expected/expected_output.json"


@pytest.fixture(scope="module")
def run_agent():
    """Run agent script on held-out data."""
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)
    shutil.copy2(HELDOUT_SLOG, "/app/data/sample.slog")
    return subprocess.run(["python3", AGENT_SCRIPT, "/app/data/sample.slog"],
                          capture_output=True, text=True, timeout=30)


def test_script_exists():
    """Agent must produce /app/output/sensorlog."""
    assert Path(AGENT_SCRIPT).exists()


def test_agent_runs(run_agent):
    """Agent script must exit 0 on held-out data."""
    assert run_agent.returncode == 0, f"Script failed (exit {run_agent.returncode}): {run_agent.stderr}"


def test_output_exists():
    """Agent script must produce /app/output/decoded.json."""
    assert Path(AGENT_OUTPUT).exists()


def test_output_matches_golden(run_agent):
    """Agent output must match golden reference on all fields."""
    # Tamper-proof: copy golden to tmp path before comparing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_golden = os.path.join(tmpdir, "expected.json")
        shutil.copy2(GOLDEN_JSON, tmp_golden)
        expected = json.loads(Path(tmp_golden).read_text())

    actual = json.loads(Path(AGENT_OUTPUT).read_text())
    assert len(actual) == len(expected), f"Count: {len(actual)} vs {len(expected)}"
    for i, (e, a) in enumerate(zip(expected, actual)):
        for key in ("timestamp", "sensor_id", "value"):
            assert a[key] == e[key], f"Record {i}: {key} {a[key]} vs {e[key]}"
