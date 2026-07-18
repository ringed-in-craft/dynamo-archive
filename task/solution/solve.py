#!/usr/bin/env python3
"""
Reference implementation: expression tree canonicalization + fingerprint
computation for polynomial expression strings.

The fingerprint function:
1. Parses an infix polynomial expression into a tree
2. Canonicalizes it (term ordering, GCD factoring, coefficient normalization)
3. Computes a 64-bit signature using a threshold-gated accumulator:
   - For coefficients < 2^24 (~16M): purely linear combination
   - For coefficients >= 2^24: non-linear rotation + XOR mixing activates

Linear trap: all 20 sample pairs use small coefficients (<100), so a linear
model overfits perfectly. Held-out expressions use coefficients in the
10^9–10^12 range, triggering the non-linear path and breaking linear
extrapolation.
"""

import math
import re
import sys
import json
import random

MASK64 = (1 << 64) - 1

# ---- Hidden constants ----
SEED      = 0x9E3779B97F4A7C15
C_VAR     = 0x517CC1B727220A95  # linear coefficient for variable term
C_EXP     = 0x7E29A9F1B3F04D6C  # linear coefficient for exponent
C_NL      = 0x3A8C1D297E593B5F  # non-linear spike multiplier
NL_ROT    = [7, 13, 17]          # rotation amounts (cycle by term index mod 3)
THRESHOLD = 1 << 24              # ~16.7M — below this, purely linear


def rotl64(x, n):
    """Rotate 64-bit integer left by n bits."""
    x &= MASK64
    n &= 63
    return ((x << n) | (x >> (64 - n))) & MASK64


# =========================================================================
# Parser — infix polynomial expressions
# =========================================================================

TOKEN_RE = re.compile(r'\d+|[a-z]|\+|\-|\*|\^|\(|\)')


class Node:
    __slots__ = ('op', 'coeff', 'var', 'exponent', 'left', 'right')
    def __init__(self):
        self.op = None
        self.coeff = 1
        self.var = None
        self.exponent = 1
        self.left = None
        self.right = None


def parse(expr_str):
    """Parse an infix polynomial expression into a Node tree."""
    tokens = TOKEN_RE.findall(expr_str)
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume():
        t = tokens[pos[0]]
        pos[0] += 1
        return t

    def parse_expr():
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            n = Node(); n.op = op; n.left = left; n.right = right
            left = n
        return left

    def parse_term():
        left = parse_pow()
        while peek() == '*':
            consume()
            right = parse_pow()
            n = Node(); n.op = '*'; n.left = left; n.right = right
            left = n
        return left

    def parse_pow():
        left = parse_atom()
        if peek() == '^':
            consume()
            right = parse_pow()  # right-associative
            n = Node(); n.op = '^'; n.left = left; n.right = right
            return n
        return left

    def parse_atom():
        t = peek()
        if t == '(':
            consume()
            n = parse_expr()
            consume()  # ')'
            return n
        if t == '-':
            consume()
            inner = parse_atom()
            neg = Node(); neg.coeff = -1; neg.exponent = 0
            n = Node(); n.op = '*'; n.left = neg; n.right = inner
            return n
        if t.isdigit():
            consume()
            n = Node(); n.coeff = int(t); n.exponent = 0
            return n
        consume()
        n = Node(); n.var = t
        return n

    return parse_expr()


# =========================================================================
# Canonicalization
# =========================================================================

def _normalize_sub(node):
    """Convert subtraction to addition with negative coefficient."""
    if node.op is None:
        return node
    node.left = _normalize_sub(node.left)
    node.right = _normalize_sub(node.right)
    if node.op == '-':
        node.op = '+'
        neg = Node(); neg.coeff = -1; neg.exponent = 0
        wrap = Node(); wrap.op = '*'; wrap.left = neg; wrap.right = node.right
        node.right = wrap
    return node


def _extract_terms(node):
    """Flatten a normalized expression tree into a list of term dicts.
    Each term: {'coeff': int, 'vars': {var_name: exponent, ...}}"""
    if node.op is None:
        if node.var is None:
            return [{'coeff': node.coeff, 'vars': {}}]
        return [{'coeff': node.coeff, 'vars': {node.var: node.exponent}}]
    if node.op == '+':
        return _extract_terms(node.left) + _extract_terms(node.right)
    if node.op == '*':
        result = []
        for lt in _extract_terms(node.left):
            for rt in _extract_terms(node.right):
                mv = dict(lt['vars'])
                for vv, ee in rt['vars'].items():
                    mv[vv] = mv.get(vv, 0) + ee
                result.append({'coeff': lt['coeff'] * rt['coeff'], 'vars': mv})
        return result
    if node.op == '^':
        base = _extract_terms(node.left)
        if node.right.op is None and node.right.var is None:
            exp = node.right.coeff
        else:
            exp = _extract_terms(node.right)[0]['coeff']
        result = []
        for t in base:
            boosted = {}
            for vv, ee in t['vars'].items():
                boosted[vv] = ee * exp
            result.append({'coeff': t['coeff'] ** exp, 'vars': boosted})
        return result
    return []


def canonicalize(node):
    """Normalize and return the canonical string form of an expression tree."""
    node = _normalize_sub(node)
    terms = _extract_terms(node)

    # Group like terms
    grouped = {}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']

    result = [{'coeff': c, 'vars': dict(k)} for k, c in grouped.items() if c != 0]
    if not result:
        return "0"

    # Factor GCD, normalize leading sign
    g = 0
    for t in result:
        g = math.gcd(g, abs(t['coeff']))
    if g == 0:
        g = 1
    if result[0]['coeff'] < 0:
        g = -g
    for t in result:
        t['coeff'] //= g

    # Sort: by total degree ascending, then lexicographic by variable names
    result.sort(key=lambda t: (sum(t['vars'].values()), sorted(t['vars'].items())))

    # Build canonical string
    parts = []
    for i, t in enumerate(result):
        if not t['vars']:
            ts = str(t['coeff'])
        else:
            vs = '*'.join(
                f"{v}^{e}" if e != 1 else v
                for v, e in sorted(t['vars'].items())
            )
            c = t['coeff']
            if c == 1:
                ts = vs
            elif c == -1:
                ts = f"(-1)*{vs}"
            else:
                ts = f"{c}*{vs}"
        if i == 0:
            parts.append(ts)
        else:
            if t['coeff'] < 0:
                nt = {**t, 'coeff': -t['coeff']}
                if not nt['vars']:
                    nts = str(nt['coeff'])
                else:
                    vs2 = '*'.join(
                        f"{v}^{e}" if e != 1 else v
                        for v, e in sorted(nt['vars'].items())
                    )
                    nts = f"{nt['coeff']}*{vs2}" if nt['coeff'] != 1 else vs2
                parts.append(f" - {nts}")
            else:
                parts.append(f" + {ts}")

    canon = ' '.join(parts)
    if abs(g) > 1:
        canon = f"{g}*({canon})"
    return canon


# =========================================================================
# Fingerprint computation
# =========================================================================

def _group_terms(expr_str):
    """Parse, canonicalize, and return grouped term dict."""
    tree = parse(expr_str)
    canon = canonicalize(tree)
    canon_tree = parse(canon)
    node = _normalize_sub(canon_tree)
    terms = _extract_terms(node)
    grouped = {}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    return grouped


def fingerprint(expr_str):
    """Compute the 64-bit integer signature for a polynomial expression.

    For small coefficients (< ~16M): purely linear combination.
    For large coefficients: non-linear rotation + XOR mixing activates.
    """
    grouped = _group_terms(expr_str)
    state = 0
    term_idx = 0

    for k, coeff in sorted(grouped.items()):
        c = coeff

        # Linear contribution (always active)
        for var, exp in k:
            state = (state + c * ord(var) * C_VAR + exp * C_EXP) & MASK64

        # Non-linear spike — only for large coefficients
        if abs(c) >= THRESHOLD:
            spike = (abs(c) >> 24) & 0xFFFFFFFFFF  # top 40 bits
            state = (state ^ (spike * C_NL)) & MASK64
            state = rotl64(state, NL_ROT[term_idx % 3])

        term_idx += 1

    # Finalize: add seed (NOT XOR — keeps small-coeff path purely linear)
    return (state + SEED) & MASK64


# =========================================================================
# Fingerprint module template — written to /app/fingerprint.py by oracle
# =========================================================================

FINGERPRINT_PY = r'''"""Expression fingerprint module.
Canonicalizes polynomial expressions and computes 64-bit integer signatures
for sub-expression deduplication in a symbolic computation system."""

import math
import re

MASK64 = (1 << 64) - 1


def _rotl64(x, n):
    x &= MASK64
    n &= 63
    return ((x << n) | (x >> (64 - n))) & MASK64


# Hidden constants — must be inferred from the sample pairs
_SEED  = 0x9E3779B97F4A7C15
_C_VAR = 0x517CC1B727220A95
_C_EXP = 0x7E29A9F1B3F04D6C
_C_NL  = 0x3A8C1D297E593B5F
_NL_ROT = (7, 13, 17)
_THRESHOLD = 1 << 24

_TOKEN_RE = re.compile(r'\d+|[a-z]|\+|\-|\*|\^|\(|\)')


class _Node:
    __slots__ = ('op', 'coeff', 'var', 'exponent', 'left', 'right')
    def __init__(self):
        self.op = None
        self.coeff = 1
        self.var = None
        self.exponent = 1
        self.left = None
        self.right = None


def _parse(expr_str):
    tokens = _TOKEN_RE.findall(expr_str)
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume():
        t = tokens[pos[0]]
        pos[0] += 1
        return t

    def parse_expr():
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            n = _Node(); n.op = op; n.left = left; n.right = right
            left = n
        return left

    def parse_term():
        left = parse_pow()
        while peek() == '*':
            consume()
            right = parse_pow()
            n = _Node(); n.op = '*'; n.left = left; n.right = right
            left = n
        return left

    def parse_pow():
        left = parse_atom()
        if peek() == '^':
            consume()
            right = parse_pow()
            n = _Node(); n.op = '^'; n.left = left; n.right = right
            return n
        return left

    def parse_atom():
        t = peek()
        if t == '(':
            consume()
            n = parse_expr()
            consume()
            return n
        if t == '-':
            consume()
            inner = parse_atom()
            neg = _Node(); neg.coeff = -1; neg.exponent = 0
            n = _Node(); n.op = '*'; n.left = neg; n.right = inner
            return n
        if t.isdigit():
            consume()
            n = _Node(); n.coeff = int(t); n.exponent = 0
            return n
        consume()
        n = _Node(); n.var = t
        return n

    return parse_expr()


def _normalize_sub(node):
    if node.op is None:
        return node
    node.left = _normalize_sub(node.left)
    node.right = _normalize_sub(node.right)
    if node.op == '-':
        node.op = '+'
        neg = _Node(); neg.coeff = -1; neg.exponent = 0
        wrap = _Node(); wrap.op = '*'; wrap.left = neg; wrap.right = node.right
        node.right = wrap
    return node


def _extract_terms(node):
    if node.op is None:
        if node.var is None:
            return [{'coeff': node.coeff, 'vars': {}}]
        return [{'coeff': node.coeff, 'vars': {node.var: node.exponent}}]
    if node.op == '+':
        return _extract_terms(node.left) + _extract_terms(node.right)
    if node.op == '*':
        result = []
        for lt in _extract_terms(node.left):
            for rt in _extract_terms(node.right):
                mv = dict(lt['vars'])
                for vv, ee in rt['vars'].items():
                    mv[vv] = mv.get(vv, 0) + ee
                result.append({'coeff': lt['coeff'] * rt['coeff'], 'vars': mv})
        return result
    if node.op == '^':
        base = _extract_terms(node.left)
        if node.right.op is None and node.right.var is None:
            exp = node.right.coeff
        else:
            exp = _extract_terms(node.right)[0]['coeff']
        result = []
        for t in base:
            boosted = {}
            for vv, ee in t['vars'].items():
                boosted[vv] = ee * exp
            result.append({'coeff': t['coeff'] ** exp, 'vars': boosted})
        return result
    return []


def _canonicalize(node):
    node = _normalize_sub(node)
    terms = _extract_terms(node)
    grouped = {}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    result = [{'coeff': c, 'vars': dict(k)} for k, c in grouped.items() if c != 0]
    if not result:
        return "0"
    g = 0
    for t in result:
        g = math.gcd(g, abs(t['coeff']))
    if g == 0:
        g = 1
    if result[0]['coeff'] < 0:
        g = -g
    for t in result:
        t['coeff'] //= g
    result.sort(key=lambda t: (sum(t['vars'].values()), sorted(t['vars'].items())))
    parts = []
    for i, t in enumerate(result):
        if not t['vars']:
            ts = str(t['coeff'])
        else:
            vs = '*'.join(f"{v}^{e}" if e != 1 else v for v, e in sorted(t['vars'].items()))
            c = t['coeff']
            if c == 1:
                ts = vs
            elif c == -1:
                ts = f"(-1)*{vs}"
            else:
                ts = f"{c}*{vs}"
        if i == 0:
            parts.append(ts)
        else:
            if t['coeff'] < 0:
                nt = {**t, 'coeff': -t['coeff']}
                if not nt['vars']:
                    nts = str(nt['coeff'])
                else:
                    vs2 = '*'.join(f"{v}^{e}" if e != 1 else v for v, e in sorted(nt['vars'].items()))
                    nts = f"{nt['coeff']}*{vs2}" if nt['coeff'] != 1 else vs2
                parts.append(f" - {nts}")
            else:
                parts.append(f" + {ts}")
    canon = ' '.join(parts)
    if abs(g) > 1:
        canon = f"{g}*({canon})"
    return canon


def _group_terms(expr_str):
    tree = _parse(expr_str)
    canon = _canonicalize(tree)
    canon_tree = _parse(canon)
    node = _normalize_sub(canon_tree)
    terms = _extract_terms(node)
    grouped = {}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    return grouped


def fingerprint(expr):
    """Compute the 64-bit integer signature for a polynomial expression.

    Args:
        expr: Infix polynomial expression string.
              Variables a-z, integer coefficients, operators + - * ^.

    Returns:
        64-bit integer signature.
    """
    grouped = _group_terms(expr)
    state = 0
    term_idx = 0

    for k, coeff in sorted(grouped.items()):
        c = coeff
        for var, exp in k:
            state = (state + c * ord(var) * _C_VAR + exp * _C_EXP) & MASK64
        if abs(c) >= _THRESHOLD:
            spike = (abs(c) >> 24) & 0xFFFFFFFFFF
            state = (state ^ (spike * _C_NL)) & MASK64
            state = _rotl64(state, _NL_ROT[term_idx % 3])
        term_idx += 1

    return (state + _SEED) & MASK64
'''


# =========================================================================
# Data generation
# =========================================================================

def generate_data():
    """Generate sample pairs (visible to agent) and held-out pairs (hidden)."""
    random.seed(42)

    # Sample expressions — most with small coefficients, but 4 include
    # coefficients >= 2^24 to make the non-linear path observable.
    # This way an agent CAN infer the threshold-gated mixing from the samples.
    large_coeffs = [
        random.randint(2**24, 2**28),
        random.randint(2**24, 2**28),
        random.randint(2**24, 2**28),
        random.randint(2**24, 2**28),
    ]
    sample_exprs = [
        "x + 1",
        "2*x + 3",
        "x^2 + x + 1",
        "3*x^2 + 2*x + 5",
        "x*y + y",
        "x^2 + 2*x*y + y^2",
        "a + b",
        "2*a + 3*b",
        "x^3 + x",
        "a^2 + 2*a*b + b^2",
        "x^2 - 1",
        "x^3 - x",
        "3*x + 5*y + 7*z",
        f"{large_coeffs[0]}*x + {large_coeffs[1]}",
        f"{large_coeffs[2]}*a^2 + {large_coeffs[3]}*b",
        "x^4 + x^2 + 1",
        "2*x^2*y + 3*x*y^2",
        "5*x + 10*y + 15*z",
        "7*a + 11*b + 13*c",
        "x^2 + 3*x + 2",
    ]

    samples = []
    for expr in sample_exprs:
        sig = fingerprint(expr)
        samples.append({"expr": expr, "signature": str(sig)})

    # Held-out — large coefficients + edge cases
    heldout_exprs = []

    # Large coefficient simple forms
    for _ in range(5):
        a = random.randint(10**9, 10**12)
        b = random.randint(10**9, 10**12)
        heldout_exprs.append(f"{a}*x + {b}")

    for _ in range(5):
        a = random.randint(10**9, 10**12)
        b = random.randint(10**9, 10**12)
        c = random.randint(10**9, 10**12)
        heldout_exprs.append(f"{a}*x^2 + {b}*x + {c}")

    # Deeply nested
    heldout_exprs += [
        "(x + 1)^3",
        "(a + b)^4",
        "(2*x + 3*y)^3",
        "((x + 1)^2 + 1)^2",
        "(a + b)*(b + c)*(c + a)",
        "(x + y + z)^2",
        "(x^2 + x + 1)*(x^2 - x + 1)",
        "(x + y)^2*(x - y)^2",
    ]

    # Edge cases
    heldout_exprs += [
        "0",
        "1",
        "-x",
        "-3*y",
        "x^0 + 1",
        "1*x + 2*x + 3*x",
        "x*y + y*x",
        "3*x + 5*x",
        "a*b - b*a",
        "(x + y) - (y + x)",
        "x^1",
        "x^0",
    ]

    heldout = []
    for expr in heldout_exprs:
        sig = fingerprint(expr)
        heldout.append({"expr": expr, "signature": str(sig)})

    return samples, heldout


# =========================================================================
# Verification — confirm linear overfit trap works
# =========================================================================

def verify_trap(samples, heldout):
    """Confirm: linear model fits samples, fails held-out catastrophically."""
    # Extract linear features
    def lin_features(expr):
        grouped = _group_terms(expr)
        sum_cv = 0
        sum_exp = 0
        for k, coeff in sorted(grouped.items()):
            for var, exp in k:
                sum_cv += coeff * ord(var)
                sum_exp += exp
        return [sum_cv, sum_exp]

    # Solve least squares: pred = A*sum_cv + B*sum_exp + bias
    X = [lin_features(s['expr']) + [1] for s in samples]
    y = [int(s['signature']) for s in samples]

    # Normal equations
    m, n = len(X), len(X[0])
    XtX = [[sum(X[i][p] * X[i][q] for i in range(m)) for q in range(n)] for p in range(n)]
    Xty = [sum(X[i][p] * y[i] for i in range(m)) for p in range(n)]

    # Gaussian elimination
    aug = [XtX[i] + [Xty[i]] for i in range(n)]
    for col in range(n):
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        if abs(pivot) < 1e-20:
            continue
        for j in range(col, n + 1):
            aug[col][j] /= pivot
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                for j in range(col, n + 1):
                    aug[row][j] -= factor * aug[col][j]
    coeffs = [aug[i][n] for i in range(n)]

    # Sample errors
    pred_samp = [sum(X[i][j] * coeffs[j] for j in range(n)) for i in range(m)]
    samp_errs = [abs(p - y[i]) for i, p in enumerate(pred_samp)]

    # Held-out errors
    X_ho = [lin_features(s['expr']) + [1] for s in heldout]
    y_ho = [int(s['signature']) for s in heldout]
    pred_ho = [sum(X_ho[i][j] * coeffs[j] for j in range(n)) for i in range(len(X_ho))]
    ho_errs = [abs(p - y_ho[i]) for i, p in enumerate(pred_ho)]

    max_samp_err = max(samp_errs)
    large_ho = sum(1 for e in ho_errs if e > 1e6)

    return {
        'sample_max_err': max_samp_err,
        'sample_mean_err': sum(samp_errs) / len(samp_errs),
        'heldout_max_err': max(ho_errs),
        'heldout_large_count': large_ho,
        'heldout_total': len(ho_errs),
        'perfect_samples': sum(1 for e in samp_errs if e == 0),
    }


# =========================================================================
# Main
# =========================================================================

if __name__ == '__main__':
    # Generate data
    samples, heldout = generate_data()

    # Verify trap
    result = verify_trap(samples, heldout)
    print(f"=== TRAP VERIFICATION ===", file=sys.stderr)
    print(f"Samples: {len(samples)}, Held-out: {len(heldout)}", file=sys.stderr)
    print(f"Sample max err: {result['sample_max_err']:.0f}", file=sys.stderr)
    print(f"Sample perfect fits: {result['perfect_samples']}/{len(samples)}", file=sys.stderr)
    print(f"Held-out max err: {result['heldout_max_err']:.0f}", file=sys.stderr)
    print(f"Held-out large errs: {result['heldout_large_count']}/{result['heldout_total']}", file=sys.stderr)

    if result['sample_max_err'] > 100:
        print("WARNING: Linear model does NOT perfectly fit samples!", file=sys.stderr)
        print("  The trap won't work — agents will see non-linearity immediately.", file=sys.stderr)
    else:
        print("OK: Linear model fits samples within tolerance", file=sys.stderr)

    if result['heldout_large_count'] < result['heldout_total'] * 0.5:
        print("WARNING: Held-out errors not large enough — trap too weak!", file=sys.stderr)
    else:
        print("OK: Held-out breaks linear model thoroughly", file=sys.stderr)

    # Write data files
    if '--write' in sys.argv:
        # Sample pairs go to environment/data/
        import os
        os.makedirs('environment/data', exist_ok=True)
        with open('environment/data/samples.jsonl', 'w') as f:
            for s in samples:
                f.write(json.dumps(s) + '\n')

        # Held-out pairs go to tests/expected/
        os.makedirs('tests/expected', exist_ok=True)
        with open('tests/expected/heldout.jsonl', 'w') as f:
            for h in heldout:
                f.write(json.dumps(h) + '\n')

        print(f"Wrote {len(samples)} sample pairs to environment/data/samples.jsonl", file=sys.stderr)
        print(f"Wrote {len(heldout)} held-out pairs to tests/expected/heldout.jsonl", file=sys.stderr)

    # Oracle mode: write fingerprint.py
    if '--oracle' in sys.argv:
        with open('/app/fingerprint.py', 'w') as f:
            f.write(FINGERPRINT_PY)
        print("Written /app/fingerprint.py", file=sys.stderr)
