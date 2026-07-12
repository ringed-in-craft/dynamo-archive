"""Verifier — runs agent's solution.py against held-out test vectors.

Before importing solution.py, the binary is removed from /app/xform.
Tests check byte-exact output against precomputed golden values.
"""
import os, sys, json, shutil, tempfile
from pathlib import Path
import pytest

GOLDEN = "/tests/expected/golden.json"
SOLUTION_PATH = "/app/output/solution.py"


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
