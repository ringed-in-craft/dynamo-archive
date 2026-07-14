"""Verifier — runs agent's solution.py against held-out test vectors.

Before importing solution.py, the binary is removed and the source is scanned
for smuggling attempts (subprocess imports, ELF embedding, base64 blobs).
Tests check byte-exact output against precomputed golden values.
"""
import os, sys, json, shutil, tempfile, re
from pathlib import Path
import pytest

GOLDEN = "/tests/expected/golden.json"
SOLUTION_PATH = "/app/output/solution.py"

FORBIDDEN = [
    r'\bimport\s+subprocess\b',
    r'\bfrom\s+subprocess\b',
    r'\bimport\s+ctypes\b',
    r'\bfrom\s+ctypes\b',
    r'\bimport\s+mmap\b',
    r'\bfrom\s+mmap\b',
    r'\bos\.system\b',
    r'\bos\.popen\b',
    r'\bos\.exec',
    r'\bexec\s*\(',
    r'\beval\s*\(',
    r'\b__import__\s*\(',
    r'/app/xform',
]


def test_solution_purity():
    """Reject solutions that try to shell out, embed the binary, or exec code."""
    src = Path(SOLUTION_PATH).read_text()

    for pattern in FORBIDDEN:
        if re.search(pattern, src):
            pytest.fail(f"solution.py contains forbidden pattern: {pattern}")

    # Check for smuggled ELF — base64 of ELF header would be f0VMRg==
    # or the raw bytes escaped in the source
    if 'f0VMR' in src or '\\x7fELF' in src or '\\x7f\\x45\\x4c\\x46' in src:
        pytest.fail("solution.py appears to contain an embedded ELF binary")

    # Reject unusually large solutions (binary embedding)
    if len(src) > 50000:
        pytest.fail(f"solution.py is too large ({len(src)} bytes) — possible binary embedding")


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
