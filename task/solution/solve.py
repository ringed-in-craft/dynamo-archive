#!/usr/bin/env python3
"""
Reference solution: reads /app/data/samples.jsonl, derives the linear
constants (C_VAR, C_EXP, SEED) from small-coefficient samples using
modular arithmetic, then writes /app/fingerprint.py.

The linear constants are proven recoverable via modular linear algebra.
The non-linear parameters (threshold, shift, rotations, C_NL) are also
recoverable from the large-coefficient samples through GF(2) linear
system solving — the code demonstrates this strategy in comments.
For the reference solution, we use the template with all constants.
"""

import json
import math
import re
import sys
import os

MASK64 = (1 << 64) - 1


def rotl64(x, n):
    x &= MASK64; n &= 63
    return ((x << n) | (x >> (64 - n))) & MASK64


# =========================================================================
# Parser and canonicalization (same as what the agent must implement)
# =========================================================================

TOKEN_RE = re.compile(r'\d+|[a-z]|\+|\-|\*|\^|\(|\)')


class Node:
    __slots__ = ('op', 'coeff', 'var', 'exponent', 'left', 'right')
    def __init__(self):
        self.op = None; self.coeff = 1; self.var = None
        self.exponent = 1; self.left = None; self.right = None


def parse(expr_str):
    tokens = TOKEN_RE.findall(expr_str); pos = [0]
    def peek(): return tokens[pos[0]] if pos[0] < len(tokens) else None
    def consume(): t = tokens[pos[0]]; pos[0] += 1; return t
    def parse_expr():
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume(); right = parse_term()
            n = Node(); n.op = op; n.left = left; n.right = right; left = n
        return left
    def parse_term():
        left = parse_pow()
        while peek() == '*':
            consume(); right = parse_pow()
            n = Node(); n.op = '*'; n.left = left; n.right = right; left = n
        return left
    def parse_pow():
        left = parse_atom()
        if peek() == '^':
            consume(); right = parse_pow()
            n = Node(); n.op = '^'; n.left = left; n.right = right; return n
        return left
    def parse_atom():
        t = peek()
        if t == '(': consume(); n = parse_expr(); consume(); return n
        if t == '-':
            consume(); inner = parse_atom()
            neg = Node(); neg.coeff = -1; neg.exponent = 0
            n = Node(); n.op = '*'; n.left = neg; n.right = inner; return n
        if t.isdigit(): consume(); n = Node(); n.coeff = int(t); n.exponent = 0; return n
        consume(); n = Node(); n.var = t; return n
    return parse_expr()


def _normalize_sub(node):
    if node.op is None: return node
    node.left = _normalize_sub(node.left); node.right = _normalize_sub(node.right)
    if node.op == '-':
        node.op = '+'; neg = Node(); neg.coeff = -1; neg.exponent = 0
        wrap = Node(); wrap.op = '*'; wrap.left = neg; wrap.right = node.right
        node.right = wrap
    return node


def _extract_terms(node):
    if node.op is None:
        if node.var is None: return [{'coeff': node.coeff, 'vars': {}}]
        return [{'coeff': node.coeff, 'vars': {node.var: node.exponent}}]
    if node.op == '+': return _extract_terms(node.left) + _extract_terms(node.right)
    if node.op == '*':
        result = []
        for lt in _extract_terms(node.left):
            for rt in _extract_terms(node.right):
                mv = dict(lt['vars'])
                for vv, ee in rt['vars'].items(): mv[vv] = mv.get(vv, 0) + ee
                result.append({'coeff': lt['coeff'] * rt['coeff'], 'vars': mv})
        return result
    if node.op == '^':
        base = _extract_terms(node.left)
        exp = node.right.coeff if (node.right.op is None and node.right.var is None) else _extract_terms(node.right)[0]['coeff']
        return [{'coeff': t['coeff'] ** exp, 'vars': {v: e * exp for v, e in t['vars'].items()}} for t in base]
    return []


def _canonicalize(node):
    node = _normalize_sub(node); terms = _extract_terms(node)
    grouped = {}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    result = [{'coeff': c, 'vars': dict(k)} for k, c in grouped.items() if c != 0]
    if not result: return "0"
    g = 0; [g := math.gcd(g, abs(t['coeff'])) for t in result]
    if g == 0: g = 1
    if result[0]['coeff'] < 0: g = -g
    for t in result: t['coeff'] //= g
    result.sort(key=lambda t: (sum(t['vars'].values()), sorted(t['vars'].items())))
    parts = []
    for i, t in enumerate(result):
        if not t['vars']: ts = str(t['coeff'])
        else:
            vs = '*'.join(f"{v}^{e}" if e != 1 else v for v, e in sorted(t['vars'].items()))
            c = t['coeff']
            ts = vs if c == 1 else (f"(-1)*{vs}" if c == -1 else f"{c}*{vs}")
        parts.append(ts if i == 0 else (f" - {nts}" if t['coeff'] < 0 else f" + {ts}"))
    canon = ' '.join(parts)
    if abs(g) > 1: canon = f"{g}*({canon})"
    return canon


def canonical_terms(expr_str):
    tree = parse(expr_str)
    canon_str = _canonicalize(tree)
    canon_tree = parse(canon_str)
    node = _normalize_sub(canon_tree)
    terms = _extract_terms(node)
    grouped = {}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    return grouped


# =========================================================================
# Linear constant recovery from samples
# =========================================================================

def extended_gcd(a, b):
    if b == 0: return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def modinv(a, m):
    g, x, _ = extended_gcd(a, m)
    if g != 1: return None
    return x % m


def linear_features(expr):
    grouped = canonical_terms(expr)
    sc = 0; se = 0
    for k, coeff in sorted(grouped.items()):
        for var, exp in k:
            sc += coeff * ord(var); se += exp
    return sc, se


def solve_linear(samples):
    """Recover C_VAR, C_EXP, SEED from small-coefficient samples.

    For small |coeff| < 2^24, the signature function is purely linear:
      sig = C_VAR * sum(c*ord(var)) + C_EXP * sum(exp) + SEED  (mod 2^64)

    Taking differences between sample pairs eliminates SEED:
      dsig = C_VAR * dsc + C_EXP * dse

    Two independent difference equations with odd determinant yield a
    solvable 2x2 linear system over Z/2^64.
    """
    small = [s for s in samples
             if all(abs(c) < (1 << 24) for c in canonical_terms(s['expr']).values())]

    for i in range(len(small)):
        for j in range(i+1, len(small)):
            sci, sei = linear_features(small[i]['expr'])
            scj, sej = linear_features(small[j]['expr'])
            dsc = (sci - scj) & MASK64; dse = (sei - sej) & MASK64
            if not (dsc & 1): continue
            dsig = (int(small[i]['signature']) - int(small[j]['signature'])) & MASK64

            if dse == 0:
                Cv = (dsig * modinv(dsc, 1 << 64)) & MASK64
                for p in range(len(small)):
                    for q in range(p+1, len(small)):
                        scp, sep = linear_features(small[p]['expr'])
                        scq, seq = linear_features(small[q]['expr'])
                        dse2 = (sep - seq) & MASK64
                        if dse2 & 1:
                            dsc2 = (scp - scq) & MASK64
                            dsig2 = (int(small[p]['signature']) - int(small[q]['signature'])) & MASK64
                            Ce = ((dsig2 - Cv * dsc2) & MASK64) * modinv(dse2, 1 << 64) & MASK64
                            S = (int(small[i]['signature']) - Cv * sci - Ce * sei) & MASK64
                            if all(((Cv * linear_features(s['expr'])[0] + Ce * linear_features(s['expr'])[1] + S) & MASK64) == int(s['signature']) for s in small):
                                return Cv, Ce, S
            else:
                for p in range(len(small)):
                    for q in range(p+1, len(small)):
                        scp, sep = linear_features(small[p]['expr'])
                        scq, seq = linear_features(small[q]['expr'])
                        dsc2 = (scp - scq) & MASK64; dse2 = (sep - seq) & MASK64
                        det = (dsc * dse2 - dsc2 * dse) & MASK64
                        if det & 1:
                            dsig2 = (int(small[p]['signature']) - int(small[q]['signature'])) & MASK64
                            inv = modinv(det, 1 << 64)
                            Cv = ((dsig * dse2 - dsig2 * dse) & MASK64) * inv & MASK64
                            Ce = ((dsc * dsig2 - dsc2 * dsig) & MASK64) * inv & MASK64
                            S = (int(small[i]['signature']) - Cv * sci - Ce * sei) & MASK64
                            if all(((Cv * linear_features(s['expr'])[0] + Ce * linear_features(s['expr'])[1] + S) & MASK64) == int(s['signature']) for s in small):
                                return Cv, Ce, S
    raise Exception("Cannot solve linear system")


# =========================================================================
# Main
# =========================================================================

if __name__ == '__main__':
    with open('/app/data/samples.jsonl') as f:
        samples = [json.loads(line) for line in f if line.strip()]

    # Step 1: Derive linear constants from samples (proves solvability)
    print("Deriving linear constants from samples...", file=sys.stderr)
    Cv, Ce, S = solve_linear(samples)
    print(f"  C_VAR = {Cv:#018x}", file=sys.stderr)
    print(f"  C_EXP = {Ce:#018x}", file=sys.stderr)
    print(f"  SEED  = {S:#018x}", file=sys.stderr)
    print("  Linear constants successfully recovered from samples!", file=sys.stderr)

    # Verify linear fit on small-coeff samples
    small = [s for s in samples
             if all(abs(c) < (1 << 24) for c in canonical_terms(s['expr']).values())]
    ok = sum(1 for s in small
             if ((Cv * linear_features(s['expr'])[0] + Ce * linear_features(s['expr'])[1] + S) & MASK64) == int(s['signature']))
    print(f"  Linear fit: {ok}/{len(small)} small-coeff samples match", file=sys.stderr)

    # Step 2: The non-linear parameters (threshold, shift, rotations, C_NL)
    # are also recoverable from the 8 large-coefficient samples using GF(2)
    # linear algebra (see solution/fingerprint_ref.py for the derivation
    # strategy). For the reference solution, we embed the correct module.
    #
    # Recovery strategy:
    #   - threshold: max |coeff| in small samples + 1 → 2^24
    #   - shift: compare spike values across samples to find (|c| >> shift) 
    #   - rotations: brute-force 31^3 candidates, solve for C_NL via GF(2)
    #   - C_NL: solve 64x64 linear system over GF(2) from one large sample
    #     and verify against all others (system is over-determined)

    ref_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fingerprint_ref.py')
    with open(ref_path) as src:
        with open('/app/fingerprint.py', 'w') as dst:
            dst.write(src.read())
    print("Written /app/fingerprint.py", file=sys.stderr)
