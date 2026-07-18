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

The fingerprint module template lives in solution/fingerprint_template.py
(separate file — rubric requires large files not be inlined).
"""

import math
import re
import sys
import json
import os
import random

MASK64 = (1 << 64) - 1

# ---- Hidden constants ----
SEED      = 0x9E3779B97F4A7C15
C_VAR     = 0x517CC1B727220A95
C_EXP     = 0x7E29A9F1B3F04D6C
C_NL      = 0x3A8C1D297E593B5F
NL_ROT    = [7, 13, 17]
THRESHOLD = 1 << 24


def rotl64(x, n):
    x &= MASK64
    n &= 63
    return ((x << n) | (x >> (64 - n))) & MASK64


# =========================================================================
# Parser
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
            right = parse_pow()
            n = Node(); n.op = '^'; n.left = left; n.right = right
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
    grouped = _group_terms(expr_str)
    state = 0
    term_idx = 0
    for k, coeff in sorted(grouped.items()):
        c = coeff
        for var, exp in k:
            state = (state + c * ord(var) * C_VAR + exp * C_EXP) & MASK64
        if abs(c) >= THRESHOLD:
            spike = (abs(c) >> 24) & 0xFFFFFFFFFF
            state = (state ^ (spike * C_NL)) & MASK64
            state = rotl64(state, NL_ROT[term_idx % 3])
        term_idx += 1
    return (state + SEED) & MASK64


# =========================================================================
# Data generation
# =========================================================================

def generate_data():
    random.seed(42)
    L = [random.randint(2**24, 2**28) for _ in range(14)]
    sample_exprs = [
        # Small-coeff — establish linear weights
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
        "x^0 + y",                          # demonstrates x^0 convention
        "x^4 + x^2 + 1",
        # Large-coeff — exercise non-linear path
        f"{L[0]}*x + {L[1]}",
        f"{L[2]}*a^2 + {L[3]}*b",
        f"{L[4]}*x^2 + {L[5]}*x + {L[6]}",
        f"{L[7]}*x + {L[8]}*y + {L[9]}*z",
        f"{L[10]}*x^2 + {L[11]}*x",
        f"{L[12]}*a + {L[13]}*b",
    ]
    samples = [{"expr": e, "signature": str(fingerprint(e))} for e in sample_exprs]

    heldout_exprs = []
    for _ in range(5):
        a = random.randint(10**9, 10**12)
        b = random.randint(10**9, 10**12)
        heldout_exprs.append(f"{a}*x + {b}")
    for _ in range(5):
        a = random.randint(10**9, 10**12)
        b = random.randint(10**9, 10**12)
        c = random.randint(10**9, 10**12)
        heldout_exprs.append(f"{a}*x^2 + {b}*x + {c}")
    heldout_exprs += [
        "(x + 1)^3", "(a + b)^4", "(2*x + 3*y)^3",
        "((x + 1)^2 + 1)^2", "(a + b)*(b + c)*(c + a)",
        "(x + y + z)^2", "(x^2 + x + 1)*(x^2 - x + 1)",
        "(x + y)^2*(x - y)^2",
        "0", "1", "-x", "-3*y",
        "1*x + 2*x + 3*x", "x*y + y*x",
        "3*x + 5*x", "a*b - b*a",
        "(x + y) - (y + x)", "x^1",
        "x^0", "x^0 + 1",
    ]
    heldout = [{"expr": e, "signature": str(fingerprint(e))} for e in heldout_exprs]
    return samples, heldout


# =========================================================================
# Main
# =========================================================================

if __name__ == '__main__':
    if '--write' in sys.argv:
        samples, heldout = generate_data()
        os.makedirs('environment/data', exist_ok=True)
        os.makedirs('tests/expected', exist_ok=True)
        with open('environment/data/samples.jsonl', 'w') as f:
            for s in samples:
                f.write(json.dumps(s) + '\n')
        with open('tests/expected/heldout.jsonl', 'w') as f:
            for h in heldout:
                f.write(json.dumps(h) + '\n')
        print(f"Wrote {len(samples)} sample + {len(heldout)} held-out pairs", file=sys.stderr)

    if '--oracle' in sys.argv:
        here = os.path.dirname(os.path.abspath(__file__))
        template = os.path.join(here, 'fingerprint_template.py')
        with open(template) as src:
            with open('/app/fingerprint.py', 'w') as dst:
                dst.write(src.read())
        print("Written /app/fingerprint.py", file=sys.stderr)
