"""
Verify the agent's document processing pipeline against golden reference.
"""

import json
import os
from pathlib import Path

import pytest

AGENT_OUTPUT = Path("/app/output/documents.jsonl")
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
    """The agent must write /app/output/documents.jsonl."""
    assert AGENT_OUTPUT.exists(), f"{AGENT_OUTPUT} does not exist"
    assert not os.path.islink(str(AGENT_OUTPUT)), "output must not be a symlink"
    assert os.path.realpath(str(AGENT_OUTPUT)).startswith(
        "/app/"
    ), "output must be a real file under /app/"


def test_documents_exact_match():
    """Every input file must produce the exact byte-for-byte correct output."""
    if not AGENT_OUTPUT.exists():
        pytest.skip("Agent output missing")

    agent_results = load_jsonl(AGENT_OUTPUT)
    expected = load_jsonl(EXPECTED_PATH)

    expected_map = {e["input"]: e["output"] for e in expected}
    agent_map = {a["input"]: a["output"] for a in agent_results}

    assert set(agent_map.keys()) == set(expected_map.keys()), (
        f"Input set mismatch: agent has {len(agent_map)} entries, "
        f"expected {len(expected_map)}"
    )

    failures = []
    for inp in expected_map:
        agent_out = agent_map.get(inp)
        exp_out = expected_map[inp]
        if agent_out != exp_out:
            failures.append(f"  {inp}: mismatch (len agent={len(agent_out or '')}, expected={len(exp_out)})")

    assert not failures, (
        f"{len(failures)}/{len(expected_map)} output mismatches:\n"
        + "\n".join(failures[:10])
    )
