"""
Verify the agent's timestomp detector against held-out forensic cases.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

AGENT_SCRIPT = Path("/app/audit.py")
SAMPLE_CASE = Path("/app/data/sample_case")
HELD_CASES = [
    "/app/data/held_case_0",
    "/app/data/held_case_1",
    "/app/data/held_case_2",
]
EXPECTED_DIR = Path("/tests/expected")


def run_analyzer(case_dir):
    """Run the agent's analyzer and return the parsed JSON output."""
    out = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    out_path = out.name
    out.close()
    try:
        result = subprocess.run(
            ["python3", str(AGENT_SCRIPT), case_dir, out_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return None, result.stderr
        with open(out_path) as f:
            return json.load(f), None
    finally:
        os.unlink(out_path)


def test_agent_script_exists():
    """The agent must write /app/audit.py."""
    assert AGENT_SCRIPT.exists(), f"{AGENT_SCRIPT} does not exist"
    assert not os.path.islink(str(AGENT_SCRIPT)), "script must not be a symlink"


def test_sample_case():
    """The sample case must produce the correct result."""
    if not AGENT_SCRIPT.exists():
        pytest.skip("Agent script missing")

    output, err = run_analyzer(str(SAMPLE_CASE))
    assert output is not None, f"Analyzer failed on sample: {err}"
    assert "tampered" in output, "Output missing 'tampered' key"
    assert isinstance(output["tampered"], list), "'tampered' must be a list"

    with open(EXPECTED_DIR / "sample_case.json") as f:
        expected = json.load(f)

    assert output["tampered"] == expected["tampered"], (
        f"Sample case mismatch: got {output['tampered']}, expected {expected['tampered']}"
    )


@pytest.mark.parametrize("case_path", HELD_CASES)
def test_held_out_case(case_path):
    """Each held-out case must produce the exact correct tampered file list."""
    if not AGENT_SCRIPT.exists():
        pytest.skip("Agent script missing")

    case_name = os.path.basename(case_path)
    output, err = run_analyzer(case_path)
    assert output is not None, f"Analyzer failed on {case_name}: {err}"
    assert "tampered" in output
    assert isinstance(output["tampered"], list)

    # All elements must be strings (absolute paths)
    for p in output["tampered"]:
        assert isinstance(p, str), f"Non-string path in tampered list: {p}"

    with open(EXPECTED_DIR / f"{case_name}.json") as f:
        expected = json.load(f)

    assert output["tampered"] == expected["tampered"], (
        f"{case_name} mismatch:\n  got:      {output['tampered']}\n  expected: {expected['tampered']}"
    )
