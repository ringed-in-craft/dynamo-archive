"""Verifier — runs agent's solution.py against held-out test vectors.

Before importing solution.py, the binary is removed from /app/xform.
Tests check byte-exact output against precomputed golden values.
"""
import os, sys, json, shutil, tempfile
from pathlib import Path
import pytest

GOLDEN = "/tests/expected/golden.json"
SOLUTION_PATH = "/app/output/solution.py"


def test_solution_not_embedding_binary():
    """solution.py must not contain an embedded binary or shell-out capability."""
    src = Path(SOLUTION_PATH).read_text()
    # Instruction: "must not invoke /app/xform or any external process"
    assert 'import subprocess' not in src, (
        "solution.py imports subprocess — violates 'must not invoke external process'"
    )
    assert 'import ctypes' not in src, (
        "solution.py imports ctypes — violates 'Pure Python 3 standard library'"
    )
    # ELF base64 header would be f0VMRg==
    assert 'f0VMR' not in src, "solution.py contains embedded ELF binary"
    # Oversized file indicates binary smuggling
    assert len(src) <= 50000, f"solution.py is too large ({len(src)} bytes)"


@pytest.fixture(scope="module")
def solution_module():
    """Import the agent's solution module."""
    assert Path(SOLUTION_PATH).exists(), f"{SOLUTION_PATH} not found"

    # Verify binary was removed by test.sh
    assert not Path("/app/xform").exists(), (
        "/app/xform still present — test.sh should have removed it"
    )

    sys.path.insert(0, "/app/output")
    import solution
    return solution


@pytest.fixture(scope="module")
def golden():
    """Load golden test vectors from tamper-proof temp copy."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_golden = os.path.join(tmp, "golden.json")
        shutil.copy2(GOLDEN, tmp_golden)
        with open(tmp_golden) as f:
            return json.load(f)


def test_solution_module(solution_module, golden):
    """solution.py must expose transform(data: bytes) -> bytes."""
    assert callable(solution_module.transform), "transform is not callable"
    # Basic smoke test
    result = solution_module.transform(b"")
    assert isinstance(result, bytes), f"transform returned {type(result)}, expected bytes"


def test_heldout_vectors(solution_module, golden):
    """Every held-out vector must match golden output byte-exact."""
    for name, entry in sorted(golden.items()):
        input_data = bytes.fromhex(entry["input_hex"])
        expected = bytes.fromhex(entry["output_hex"])
        actual = solution_module.transform(input_data)
        assert actual == expected, (
            f"{name}: length {len(input_data)} -> "
            f"expected {expected.hex()[:40]}..., "
            f"got {actual.hex()[:40]}..."
        )
