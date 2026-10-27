"""Verifier — runs agent's reconstruct.py on held-out pcap, checks SHA-256 against golden."""
import os, shutil, subprocess, hashlib, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = "/app/output/reconstruct.py"
AGENT_OUTPUT = "/app/output/payload.bin"
HELDOUT_PCAP = "/tests/expected/heldout.pcap"
GOLDEN_HASH = "/tests/expected/golden_hash.txt"


@pytest.fixture(scope="module")
def run_agent():
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)
    shutil.copy2(HELDOUT_PCAP, "/app/data/sample.pcap")
    return subprocess.run(["python3", AGENT_SCRIPT], capture_output=True, text=True, timeout=60)


def test_script_exists():
    """Agent must produce /app/output/reconstruct.py."""
    assert Path(AGENT_SCRIPT).exists()


def test_script_runs(run_agent):
    """Script must exit 0 on held-out data."""
    assert run_agent.returncode == 0, f"Exit {run_agent.returncode}: {run_agent.stderr}"


def test_output_exists():
    """Script must produce /app/output/payload.bin."""
    assert Path(AGENT_OUTPUT).exists()


def test_hash_matches_golden(run_agent):
    """SHA-256 of payload.bin must match golden reference."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_golden = os.path.join(tmpdir, "golden.txt")
        shutil.copy2(GOLDEN_HASH, tmp_golden)
        expected = Path(tmp_golden).read_text().strip()

    actual = hashlib.sha256(Path(AGENT_OUTPUT).read_bytes()).hexdigest()
    assert actual == expected, f"Hash mismatch: got {actual}, expected {expected}"
