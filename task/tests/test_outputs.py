"""Pytest verifier — runs agent's decoder and reference binary on held-out data, compares."""
import json, os, shutil, subprocess, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = "/app/output/sensorlog"
AGENT_OUTPUT = "/app/output/decoded.json"
REFERENCE_BIN = "/app/data/slogdec"
HELDOUT_SLOG = "/tests/expected/heldout.slog"


@pytest.fixture(scope="module")
def run_both():
    """Run reference binary and agent script on held-out data."""
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)
    shutil.copy2(HELDOUT_SLOG, "/app/data/sample.slog")

    ref = subprocess.run([REFERENCE_BIN, "/app/data/sample.slog"],
                         capture_output=True, text=True, timeout=10)
    agent = subprocess.run(["python3", AGENT_SCRIPT, "/app/data/sample.slog"],
                           capture_output=True, text=True, timeout=30)
    return ref, agent


def test_script_exists():
    assert Path(AGENT_SCRIPT).exists()


def test_agent_runs(run_both):
    ref, agent = run_both
    assert ref.returncode == 0, f"Reference binary failed: {ref.stderr}"
    assert agent.returncode == 0, f"Agent script failed (exit {agent.returncode}): {agent.stderr}"


def test_output_exists():
    assert Path(AGENT_OUTPUT).exists()


def test_output_matches_reference(run_both):
    ref, agent = run_both
    expected = json.loads(ref.stdout)
    actual = json.loads(Path(AGENT_OUTPUT).read_text())

    assert len(actual) == len(expected), f"Count: {len(actual)} vs {len(expected)}"
    for i, (e, a) in enumerate(zip(expected, actual)):
        assert a["timestamp"] == e["timestamp"], f"Record {i}: ts {a['timestamp']} vs {e['timestamp']}"
