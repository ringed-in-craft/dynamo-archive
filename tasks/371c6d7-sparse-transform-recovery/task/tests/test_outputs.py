"""
Verify the agent's transform reconstruction against held-out vector pairs.
"""

import json
import os
from pathlib import Path

import pytest

AGENT_OUTPUT = Path("/app/output/transforms.jsonl")
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
    """The agent must write /app/output/transforms.jsonl."""
    assert AGENT_OUTPUT.exists(), f"{AGENT_OUTPUT} does not exist"
    assert not os.path.islink(str(AGENT_OUTPUT)), "output must not be a symlink"
    assert os.path.realpath(str(AGENT_OUTPUT)).startswith(
        "/app/"
    ), "output must be a real file under /app/"


def test_transforms_exact_match():
    """Every input vector must produce the exact correct output vector element-by-element."""
    if not AGENT_OUTPUT.exists():
        pytest.skip("Agent output missing")

    agent_results = load_jsonl(AGENT_OUTPUT)
    expected = load_jsonl(EXPECTED_PATH)

    expected_map = {json.dumps(e["input"]): e["output"] for e in expected}
    agent_map = {json.dumps(a["input"]): a["output"] for a in agent_results}

    assert set(agent_map.keys()) == set(expected_map.keys()), (
        f"Input set mismatch: agent has {len(agent_map)} entries, "
        f"expected {len(expected_map)}"
    )

    failures = []
    for inp_str in expected_map:
        agent_out = agent_map.get(inp_str)
        exp_out = expected_map[inp_str]
        if agent_out != exp_out:
            inp = json.loads(inp_str)
            failures.append(
                f"  {inp}: got {agent_out[:3]}..., expected {exp_out[:3]}..."
            )

    assert not failures, (
        f"{len(failures)}/{len(expected_map)} output mismatches:\n"
        + "\n".join(failures[:10])
    )
