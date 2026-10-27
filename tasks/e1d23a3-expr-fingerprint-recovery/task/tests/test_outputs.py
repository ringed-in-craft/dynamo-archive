"""Tests for expression fingerprint task.

Verifies that the agent's /app/fingerprint.py module correctly computes
64-bit integer signatures for polynomial expressions.

The verifier checks:
1. fingerprint.py exists and exports a callable fingerprint(expr: str) -> int
2. All 20 archived sample pairs match exactly
3. All 30 held-out pairs match exactly
4. fingerprint.py uses only stdlib imports and contains no embedded lookup tables
"""

import json
import sys
import os
from pathlib import Path


def test_module_exists_and_callable():
    """fingerprint.py must exist, import cleanly, and expose a callable fingerprint()."""
    sys.path.insert(0, '/app')
    import fingerprint as fp
    assert hasattr(fp, 'fingerprint'), "fingerprint.py must expose fingerprint()"
    assert callable(fp.fingerprint), "fingerprint() must be callable"
    # Test basic call
    result = fp.fingerprint("0")
    assert isinstance(result, int), f"fingerprint() must return int, got {type(result)}"
    assert 0 <= result < (1 << 64), f"signature must be 64-bit unsigned, got {result}"


def test_all_sample_pairs():
    """All 20 archived sample pairs must match exactly."""
    sys.path.insert(0, '/app')
    import fingerprint as fp

    samples_path = '/app/data/samples.jsonl'
    assert Path(samples_path).exists(), f"Sample file missing: {samples_path}"

    with open(samples_path) as f:
        samples = [json.loads(line) for line in f if line.strip()]

    assert len(samples) == 20, f"Expected 20 sample pairs, got {len(samples)}"

    failures = []
    for i, s in enumerate(samples):
        expected = int(s['signature'])
        actual = fp.fingerprint(s['expr'])
        if actual != expected:
            failures.append((i, s['expr'], expected, actual))

    if failures:
        msg = "\n".join(
            f"  sample[{i}] '{expr}': expected {exp}, got {act}"
            for i, expr, exp, act in failures
        )
        raise AssertionError(f"{len(failures)}/{len(samples)} sample pairs failed:\n{msg}")


def test_all_heldout_pairs():
    """All 30 held-out pairs must match exactly."""
    sys.path.insert(0, '/app')
    import fingerprint as fp

    heldout_path = '/tests/expected/heldout.jsonl'
    assert Path(heldout_path).exists(), f"Held-out file missing: {heldout_path}"

    with open(heldout_path) as f:
        heldout = [json.loads(line) for line in f if line.strip()]

    assert len(heldout) == 30, f"Expected 30 held-out pairs, got {len(heldout)}"

    failures = []
    for i, h in enumerate(heldout):
        expected = int(h['signature'])
        actual = fp.fingerprint(h['expr'])
        if actual != expected:
            failures.append((i, h['expr'], expected, actual))

    if failures:
        msg = "\n".join(
            f"  heldout[{i}] '{expr}': expected {exp}, got {act}"
            for i, expr, exp, act in failures
        )
        raise AssertionError(f"{len(failures)}/{len(heldout)} held-out pairs failed:\n{msg}")


def test_purity():
    """fingerprint.py must use only stdlib imports, no embedded lookup tables, no base64."""
    fp_path = '/app/fingerprint.py'
    assert Path(fp_path).exists(), f"fingerprint.py missing: {fp_path}"

    content = Path(fp_path).read_text()
    size = len(content.encode('utf-8'))

    # Size cap: 50KB
    assert size <= 50 * 1024, f"fingerprint.py too large: {size} bytes (max 50KB)"

    # No base64-encoded data (look for common b64 headers)
    import re
    b64_patterns = [
        r'[A-Za-z0-9+/]{100,}={0,2}',  # long base64 strings
        r'f0VMR',  # ELF header
        r'UEsDB',  # ZIP header
        r'iVBOR',  # PNG header
    ]
    for pat in b64_patterns:
        assert not re.search(pat, content), f"fingerprint.py contains embedded data matching pattern: {pat}"

    # No non-stdlib imports (check import statements)
    import_src = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            import_src.append(stripped)

    stdlib_modules = {
        're', 'math', 'itertools', 'functools', 'collections', 'string',
        'typing', 'dataclasses', 'json', 'sys', 'os', 'io', 'pathlib',
        'hashlib', 'struct', 'array', 'enum', 'fractions', 'decimal',
        'random', 'copy', 'textwrap', 'inspect', 'warnings', 'abc',
        'operator', 'statistics', 'types', 'ast',
    }

    for imp in import_src:
        # Extract module name
        parts = imp.replace('import', ' ').replace('from', ' ').split()
        if parts and parts[0] not in stdlib_modules:
            # Not a hard fail — just log for review. The agent might use any
            # stdlib module legitimately.
            pass

    # Reject known non-stdlib modules
    non_stdlib = {'numpy', 'scipy', 'sympy', 'z3', 'pandas', 'torch', 'tensorflow',
                  'sklearn', 'matplotlib', 'pillow', 'requests', 'flask', 'django'}
    for imp in import_src:
        parts = imp.replace('import', ' ').replace('from', ' ').split()
        for p in parts:
            base = p.split('.')[0]
            if base in non_stdlib:
                raise AssertionError(
                    f"fingerprint.py imports non-stdlib module '{base}': {imp}"
                )


def test_no_embedded_tables():
    """fingerprint.py must not contain pre-computed lookup tables for the 20 samples."""
    content = Path('/app/fingerprint.py').read_text()

    # Count large dictionary/list literals (potential lookup tables)
    import re
    # Look for dicts with more than 5 entries
    large_dicts = re.findall(r'\{[^}]{200,}\}', content)
    # Look for large lists of tuples
    large_lists = re.findall(r'\[[^\]]{200,}\]', content)

    # Not a hard fail — just a red flag check. The agent could use constants
    # legitimately.
    # But if there are very large embedded structures (>1KB), flag it.
    for d in large_dicts:
        if len(d) > 1000:
            raise AssertionError(
                f"fingerprint.py contains large embedded data structure ({len(d)} chars)"
            )
    for lst in large_lists:
        if len(lst) > 1000:
            raise AssertionError(
                f"fingerprint.py contains large embedded data structure ({len(lst)} chars)"
            )
