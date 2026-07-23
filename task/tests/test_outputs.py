"""
Verify the agent's mesh scoring function against held-out triangles.
"""

import json, os, subprocess, tempfile
from pathlib import Path
import pytest

AGENT_SCRIPT = Path("/app/audit.py")
QUERIES_PATH = Path("/app/data/queries.jsonl")
EXPECTED_PATH = Path("/tests/expected/held_out.jsonl")


def run_agent():
    out = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    out_path = out.name; out.close()
    try:
        result = subprocess.run(
            ["python3", str(AGENT_SCRIPT), str(QUERIES_PATH), out_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0: return None, result.stderr
        with open(out_path) as f:
            return [json.loads(line) for line in f if line.strip()], None
    finally: os.unlink(out_path)


def test_agent_script_exists():
    """The agent must write /app/audit.py."""
    assert AGENT_SCRIPT.exists()
    assert not os.path.islink(str(AGENT_SCRIPT))


def test_scores_exact_match():
    """Every held-out triangle must produce the exact correct score."""
    if not AGENT_SCRIPT.exists():
        pytest.skip("Agent script missing")
    output, err = run_agent()
    assert output is not None, f"Agent failed: {err}"

    with open(EXPECTED_PATH) as f:
        expected = [json.loads(line) for line in f if line.strip()]
    expected_map = {json.dumps(e["input"]): e["score"] for e in expected}
    agent_map = {}
    for item in output:
        key = json.dumps(item["input"])
        agent_map[key] = item["score"]

    assert set(agent_map.keys()) == set(expected_map.keys()), "Input set mismatch"
    failures = [f"  {k[:60]} got {agent_map[k]} expected {expected_map[k]}"
                for k in expected_map if agent_map.get(k) != expected_map[k]]
    assert not failures, f"{len(failures)}/{len(expected_map)} mismatches:\n" + "\n".join(failures[:5])
