"""
Verify the agent's mesh scoring output against held-out triangles.
Does NOT execute agent code at verify time — grades static output.
"""

import json, os
from pathlib import Path
import pytest

AGENT_OUTPUT = Path("/app/output/scores.jsonl")
EXPECTED_PATH = Path("/tests/expected/held_out.jsonl")


def test_agent_output_exists():
    """The agent must write /app/output/scores.jsonl."""
    assert AGENT_OUTPUT.exists(), f"{AGENT_OUTPUT} does not exist"
    assert not os.path.islink(str(AGENT_OUTPUT)), "output must not be a symlink"
    assert os.path.realpath(str(AGENT_OUTPUT)).startswith(
        "/app/"
    ), "output must be a real file under /app/"


def test_scores_exact_match():
    """Every held-out triangle must produce the exact correct score."""
    if not AGENT_OUTPUT.exists():
        pytest.skip("Agent output missing")

    with open(AGENT_OUTPUT) as f:
        agent_results = [json.loads(line) for line in f if line.strip()]
    with open(EXPECTED_PATH) as f:
        expected = [json.loads(line) for line in f if line.strip()]

    expected_map = {json.dumps(e["input"]): e["score"] for e in expected}
    agent_map = {}
    for item in agent_results:
        key = json.dumps(item["input"])
        agent_map[key] = item["score"]

    assert set(agent_map.keys()) == set(expected_map.keys()), (
        f"Input set mismatch: agent has {len(agent_map)}, expected {len(expected_map)}"
    )
    failures = [
        f"  {k[:60]} got {agent_map[k]} expected {expected_map[k]}"
        for k in expected_map if agent_map.get(k) != expected_map[k]
    ]
    assert not failures, (
        f"{len(failures)}/{len(expected_map)} mismatches:\n" + "\n".join(failures[:5])
    )
