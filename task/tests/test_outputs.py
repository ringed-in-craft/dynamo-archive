"""Pytest verifier for the sensor log reverse-engineering task.

Runs the agent's decoder against a held-out file and compares output
against the reference binary (run from a tamper-proof temporary copy).
The reference binary is removed before invoking the agent's script
to prevent trivial shell-out bypass.
"""
import json, os, shutil, subprocess, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = "/app/output/sensorlog"
AGENT_OUTPUT = "/app/output/decoded.json"
REFERENCE_BIN = "/app/data/slogdec"
HELDOUT_SLOG = "/tests/expected/heldout.slog"


@pytest.fixture(scope="module")
def run_both():
    """Run reference binary (from tmp copy) and agent script on held-out data."""
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)
    shutil.copy2(HELDOUT_SLOG, "/app/data/sample.slog")

    # Run reference from tamper-proof tmp copy
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_bin = os.path.join(tmpdir, "slogdec")
        shutil.copy2(REFERENCE_BIN, ref_bin)
        os.chmod(ref_bin, 0o755)
        ref = subprocess.run([ref_bin, "/app/data/sample.slog"],
                             capture_output=True, text=True, timeout=10)

    # Remove reference binary so agent script cannot shell out to it
    if os.path.exists(REFERENCE_BIN):
        os.remove(REFERENCE_BIN)

    agent = subprocess.run(["python3", AGENT_SCRIPT, "/app/data/sample.slog"],
                           capture_output=True, text=True, timeout=30)
    return ref, agent


def test_script_exists():
    """Agent must produce /app/output/sensorlog."""
    assert Path(AGENT_SCRIPT).exists()


def test_agent_runs(run_both):
    """Agent script and reference binary must both exit 0."""
    ref, agent = run_both
    assert ref.returncode == 0, f"Reference binary failed: {ref.stderr}"
    assert agent.returncode == 0, f"Agent script failed (exit {agent.returncode}): {agent.stderr}"


def test_output_exists():
    """Agent script must produce /app/output/decoded.json."""
    assert Path(AGENT_OUTPUT).exists()


def test_output_matches_reference(run_both):
    """Agent output must match reference binary output on all fields."""
    ref, agent = run_both
    expected = json.loads(ref.stdout)
    actual = json.loads(Path(AGENT_OUTPUT).read_text())

    assert len(actual) == len(expected), f"Count: {len(actual)} vs {len(expected)}"
    for i, (e, a) in enumerate(zip(expected, actual)):
        for key in ("timestamp", "sensor_id", "value"):
            assert a[key] == e[key], f"Record {i}: {key} {a[key]} vs {e[key]}"
