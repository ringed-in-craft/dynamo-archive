"""Verifier — runs agent's recover.py on held-out archive, checks SHA-256 of each extracted file."""
import os, shutil, subprocess, hashlib, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = "/app/output/recover.py"
HELDOUT_ARCHIVE = "/tests/expected/heldout.bin"
GOLDEN_HASHES = "/tests/expected/golden_hashes.txt"
OUTDIR = "/app/output"


@pytest.fixture(scope="module")
def run_agent():
    """Replace sample archive with held-out, run agent's fixed script, return result."""
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs("/app/data", exist_ok=True)
    # Clear any leftover extracted files from oracle run, but keep recover.py artifact
    for f in os.listdir(OUTDIR):
        fpath = os.path.join(OUTDIR, f)
        if os.path.isfile(fpath) and f != "recover.py":
            os.remove(fpath)
    shutil.copy2(HELDOUT_ARCHIVE, "/app/data/archive.bin")
    return subprocess.run(
        ["python3", AGENT_SCRIPT], capture_output=True, text=True, timeout=30
    )


def test_script_exists():
    """Agent must produce /app/output/recover.py."""
    assert Path(AGENT_SCRIPT).exists(), f"{AGENT_SCRIPT} not found"


def test_script_runs_cleanly(run_agent):
    """Agent's script must exit 0 on held-out data."""
    assert run_agent.returncode == 0, (
        f"Exit {run_agent.returncode}: {run_agent.stderr}"
    )


def test_extracted_files_match_golden(run_agent):
    """Every extracted file must match its golden SHA-256 hash byte-for-byte."""
    # Read expected hashes from tamper-proof copy
    with tempfile.TemporaryDirectory() as tmp:
        tmp_golden = os.path.join(tmp, "hashes.txt")
        shutil.copy2(GOLDEN_HASHES, tmp_golden)
        expected = {}
        for line in Path(tmp_golden).read_text().strip().split("\n"):
            if line.strip():
                name, h = line.split()
                expected[name] = h

    # Collect actual hashes from extracted files (excluding recover.py artifact)
    actual = {}
    for fname in os.listdir(OUTDIR):
        fpath = os.path.join(OUTDIR, fname)
        if os.path.isfile(fpath) and fname != "recover.py":
            actual[fname] = hashlib.sha256(Path(fpath).read_bytes()).hexdigest()

    assert set(actual.keys()) == set(expected.keys()), (
        f"File mismatch: got {sorted(actual.keys())}, expected {sorted(expected.keys())}"
    )

    for name in sorted(expected):
        assert actual[name] == expected[name], (
            f"Hash mismatch for {name}: got {actual[name]}, expected {expected[name]}"
        )
