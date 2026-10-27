"""Pytest verifier for the telemetry codec reconstruction task.

Imports the agent's solution.py and runs transform() against held-out
test vectors stored in tests/expected/golden.json.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

GOLDEN_PATH = "/tests/expected/golden.json"
SOLUTION_PATH = "/app/output/solution.py"


def _load_transform():
    """Import the agent's transform function from solution.py."""
    spec = importlib.util.spec_from_file_location("solution", SOLUTION_PATH)
    assert spec is not None, f"Could not load {SOLUTION_PATH}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["solution"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.transform


def _load_golden():
    """Load held-out test vectors."""
    with open(GOLDEN_PATH) as f:
        return json.load(f)


def test_module_loads():
    """The agent's solution.py must expose a callable transform function."""
    transform = _load_transform()
    assert callable(transform), "transform is not callable"


def test_empty_input():
    """Empty input must produce empty output."""
    transform = _load_transform()
    result = transform(b"")
    assert result == b"", f"transform(b'') returned {result.hex()}"


def test_all_held_out_vectors():
    """All held-out test vectors must match byte-exact."""
    transform = _load_transform()
    golden = _load_golden()
    
    for name, entry in golden.items():
        inp = bytes.fromhex(entry["input_hex"])
        expected = bytes.fromhex(entry["output_hex"])
        actual = transform(inp)
        assert actual == expected, (
            f"Vector '{name}' mismatch:\n"
            f"  input length: {len(inp)}\n"
            f"  expected: {expected[:32].hex()}...\n"
            f"  got:      {actual[:32].hex() if actual else '(empty)'}..."
        )
