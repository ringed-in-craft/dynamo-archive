"""
Verify the agent's fingerprint reconstruction against held-out data.
"""

import json
import os
from pathlib import Path

import pytest

AGENT_OUTPUT = Path("/app/output/fingerprints.jsonl")
EXPECTED_PATH = Path("/tests/expected/held_out.jsonl")


def load_jsonl(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def test_agent_output_exists():
    """The agent must write /app/output/fingerprints.jsonl."""
    assert AGENT_OUTPUT.exists(), f"{AGENT_OUTPUT} does not exist"
    assert not os.path.islink(str(AGENT_OUTPUT)), "output must not be a symlink"
    assert os.path.realpath(str(AGENT_OUTPUT)).startswith(
        "/app/"
    ), "output must be a real file under /app/"


def test_fingerprints_exact_match():
    """Every queried input must produce the exact correct 16-char hex fingerprint."""
    if not AGENT_OUTPUT.exists():
        pytest.skip("Agent output missing")

    agent_results = load_jsonl(AGENT_OUTPUT)
    expected = load_jsonl(EXPECTED_PATH)

    expected_map = {e["input"]: e["fingerprint"] for e in expected}
    agent_map = {a["input"]: a["fingerprint"] for a in agent_results}

    assert set(agent_map.keys()) == set(expected_map.keys()), (
        f"Input set mismatch: agent has {len(agent_map)} entries, "
        f"expected {len(expected_map)}"
    )

    failures = []
    for inp in expected_map:
        if agent_map.get(inp) != expected_map[inp]:
            failures.append(
                f"  {inp!r}: got {agent_map.get(inp)}, expected {expected_map[inp]}"
            )

    assert not failures, (
        f"{len(failures)}/{len(expected_map)} fingerprint mismatches:\n"
        + "\n".join(failures[:10])
    )
