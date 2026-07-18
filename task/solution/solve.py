#!/usr/bin/env python3
"""
Reference solution: reads /app/data/samples.jsonl, derives ALL constants
(C_VAR, C_EXP, SEED, C_NL) directly from the sample data, then writes
/app/fingerprint.py.

Algorithm (per term with coeff c, variable v, exponent e):
    state += c * ord(v) * C_VAR + e * C_EXP
    state ^= (c * C_NL)
Final: (state + SEED) & MASK64

Derivation:
  From "0": SEED = sig("0")
  From "1": C_NL = sig("1") ^ SEED
  From pairs: solve linear system for C_VAR, C_EXP
"""

import json
import math
import re
import sys

MASK64 = (1 << 64) - 1


# =========================================================================
# Parser + canonicalization (same as what agent discovers)
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
    g = 0
    for t in result: g = math.gcd(g, abs(t['coeff']))
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
        if i == 0: parts.append(ts)
        else:
            if t['coeff'] < 0:
                nt = {**t, 'coeff': -t['coeff']}
                nts = str(nt['coeff']) if not nt['vars'] else ('*'.join(f"{v}^{e}" if e != 1 else v for v, e in sorted(nt['vars'].items())))
                parts.append(f" - {nts}")
            else: parts.append(f" + {ts}")
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


def xorsum(expr, C_nl):
    """XOR over all terms: XOR_i (c_i * C_nl)."""
    grouped = canonical_terms(expr)
    result = 0
    for k in sorted(grouped.keys()):
        c = grouped[k]
        result ^= ((c * C_nl) & MASK64)
    return result


def lin_features(expr):
    """sum(c * ord(var)) and sum(exp) over all terms."""
    grouped = canonical_terms(expr)
    sc = 0; se = 0
    for k in sorted(grouped.keys()):
        c = grouped[k]
        for var, exp in k:
            sc += c * ord(var); se += exp
    return sc, se


def fingerprint_with(expr, Cv, Ce, S, C_nl):
    """Compute signature: linear sum first, then XOR, then + SEED."""
    grouped = canonical_terms(expr)
    state = 0
    xor_acc = 0
    for k in sorted(grouped.keys()):
        c = grouped[k]
        for var, exp in k:
            state = (state + c * ord(var) * Cv + exp * Ce) & MASK64
        xor_acc ^= ((c * C_nl) & MASK64)
    state ^= xor_acc
    return (state + S) & MASK64


# =========================================================================
# Derivation of all constants from samples
# =========================================================================

def extended_gcd(a, b):
    if b == 0: return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def modinv(a, m):
    g, x, _ = extended_gcd(a, m)
    if g != 1: return None
    return x % m


def derive_all(samples):
    """Derive C_VAR, C_EXP, SEED, C_NL from the 20 sample pairs."""
    sig_map = {s['expr']: int(s['signature']) for s in samples}

    # Step 1: SEED from "0"
    if '0' not in sig_map:
        raise Exception("Sample set must include the expression '0'")
    S = sig_map['0']

    # Step 2: C_NL from "1"
    # sig("1") = Cn + SEED  (only term is constant 1, xorsum = 1*Cn = Cn, state=0 ^ Cn = Cn)
    if '1' not in sig_map:
        raise Exception("Sample set must include the expression '1'")
    C_nl = (sig_map['1'] - S) & MASK64

    # Step 3: C_VAR, C_EXP from expressions with known XOR contribution
    # sig = Cv*sc + Ce*se + xorsum(C_nl) + S
    # → Cv*sc + Ce*se = sig - xorsum - S
    for s in samples:
        expr = s['expr']
        sc, se = lin_features(expr)
        xor_c = xorsum(expr, C_nl)
        rhs = (int(s['signature']) - xor_c - S) & MASK64
        # Store: Cv*sc + Ce*se = rhs
        s['_sc'] = sc; s['_se'] = se; s['_rhs'] = rhs

    # Find two independent equations
    for i in range(len(samples)):
        for j in range(i+1, len(samples)):
            si, sj = samples[i], samples[j]
            dsc = (si['_sc'] - sj['_sc']) & MASK64
            dse = (si['_se'] - sj['_se']) & MASK64
            if not (dsc & 1): continue
            drhs = (si['_rhs'] - sj['_rhs']) & MASK64

            if dse == 0:
                Cv = (drhs * modinv(dsc, 1 << 64)) & MASK64
                # Find second equation for Ce
                for p in range(len(samples)):
                    se_p = samples[p]['_se']; sc_p = samples[p]['_sc']
                    rhs_p = samples[p]['_rhs']
                    if se_p & 1:  # se is odd → invertible
                        Ce = ((rhs_p - Cv * sc_p) & MASK64) * modinv(se_p, 1 << 64) & MASK64
                        if verify_all(samples, Cv, Ce, S, C_nl):
                            return Cv, Ce, S, C_nl
            else:
                for p in range(len(samples)):
                    for q in range(p+1, len(samples)):
                        sp, sq = samples[p], samples[q]
                        dsc2 = (sp['_sc'] - sq['_sc']) & MASK64
                        dse2 = (sp['_se'] - sq['_se']) & MASK64
                        det = (dsc * dse2 - dsc2 * dse) & MASK64
                        if det & 1:
                            drhs2 = (sp['_rhs'] - sq['_rhs']) & MASK64
                            inv = modinv(det, 1 << 64)
                            Cv = ((drhs * dse2 - drhs2 * dse) & MASK64) * inv & MASK64
                            Ce = ((dsc * drhs2 - dsc2 * drhs) & MASK64) * inv & MASK64
                            if verify_all(samples, Cv, Ce, S, C_nl):
                                return Cv, Ce, S, C_nl
    raise Exception("Cannot solve for C_VAR, C_EXP")


def verify_all(samples, Cv, Ce, S, C_nl):
    for s in samples:
        if fingerprint_with(s['expr'], Cv, Ce, S, C_nl) != int(s['signature']):
            return False
    return True


# =========================================================================
# Write /app/fingerprint.py
# =========================================================================

FP_CODE = '''"""Expression fingerprint for polynomial expression deduplication."""

import math
import re

MASK64 = (1 << 64) - 1

_SEED  = {SEED}
_C_VAR = {C_VAR}
_C_EXP = {C_EXP}
_C_NL  = {C_NL}

_TOKEN_RE = re.compile(r'\\d+|[a-z]|\\+|\\-|\\*|\\^|\\(|\\)')

class _Node:
    __slots__ = ('op', 'coeff', 'var', 'exponent', 'left', 'right')
    def __init__(self):
        self.op = None; self.coeff = 1; self.var = None
        self.exponent = 1; self.left = None; self.right = None

def _parse(expr_str):
    tokens = _TOKEN_RE.findall(expr_str); pos = [0]
    def peek(): return tokens[pos[0]] if pos[0] < len(tokens) else None
    def consume(): t = tokens[pos[0]]; pos[0] += 1; return t
    def parse_expr():
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume(); right = parse_term()
            n = _Node(); n.op = op; n.left = left; n.right = right; left = n
        return left
    def parse_term():
        left = parse_pow()
        while peek() == '*':
            consume(); right = parse_pow()
            n = _Node(); n.op = '*'; n.left = left; n.right = right; left = n
        return left
    def parse_pow():
        left = parse_atom()
        if peek() == '^':
            consume(); right = parse_pow()
            n = _Node(); n.op = '^'; n.left = left; n.right = right; return n
        return left
    def parse_atom():
        t = peek()
        if t == '(': consume(); n = parse_expr(); consume(); return n
        if t == '-':
            consume(); inner = parse_atom()
            neg = _Node(); neg.coeff = -1; neg.exponent = 0
            n = _Node(); n.op = '*'; n.left = neg; n.right = inner; return n
        if t.isdigit(): consume(); n = _Node(); n.coeff = int(t); n.exponent = 0; return n
        consume(); n = _Node(); n.var = t; return n
    return parse_expr()

def _normalize_sub(node):
    if node.op is None: return node
    node.left = _normalize_sub(node.left); node.right = _normalize_sub(node.right)
    if node.op == '-':
        node.op = '+'; neg = _Node(); neg.coeff = -1; neg.exponent = 0
        wrap = _Node(); wrap.op = '*'; wrap.left = neg; wrap.right = node.right
        node.right = wrap
    return node

def _extract_terms(node):
    if node.op is None:
        if node.var is None: return [{{'coeff': node.coeff, 'vars': {{}}}}]
        return [{{'coeff': node.coeff, 'vars': {{node.var: node.exponent}}}}]
    if node.op == '+': return _extract_terms(node.left) + _extract_terms(node.right)
    if node.op == '*':
        result = []
        for lt in _extract_terms(node.left):
            for rt in _extract_terms(node.right):
                mv = dict(lt['vars'])
                for vv, ee in rt['vars'].items(): mv[vv] = mv.get(vv, 0) + ee
                result.append({{'coeff': lt['coeff'] * rt['coeff'], 'vars': mv}})
        return result
    if node.op == '^':
        base = _extract_terms(node.left)
        exp = node.right.coeff if (node.right.op is None and node.right.var is None) else _extract_terms(node.right)[0]['coeff']
        return [{{'coeff': t['coeff'] ** exp, 'vars': {{v: e * exp for v, e in t['vars'].items()}}}} for t in base]
    return []

def _canonicalize(node):
    node = _normalize_sub(node); terms = _extract_terms(node)
    grouped = {{}}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    result = [{{'coeff': c, 'vars': dict(k)}} for k, c in grouped.items() if c != 0]
    if not result: return "0"
    g = 0
    for t in result: g = math.gcd(g, abs(t['coeff']))
    if g == 0: g = 1
    if result[0]['coeff'] < 0: g = -g
    for t in result: t['coeff'] //= g
    result.sort(key=lambda t: (sum(t['vars'].values()), sorted(t['vars'].items())))
    parts = []
    for i, t in enumerate(result):
        if not t['vars']: ts = str(t['coeff'])
        else:
            vs = '*'.join(f"{{v}}^{{e}}" if e != 1 else v for v, e in sorted(t['vars'].items()))
            c = t['coeff']
            ts = vs if c == 1 else (f"(-1)*{{vs}}" if c == -1 else f"{{c}}*{{vs}}")
        if i == 0: parts.append(ts)
        else:
            if t['coeff'] < 0:
                nt = {{**t, 'coeff': -t['coeff']}}
                nts = str(nt['coeff']) if not nt['vars'] else ('*'.join(f"{{v}}^{{e}}" if e != 1 else v for v, e in sorted(nt['vars'].items())))
                parts.append(f" - {{nts}}")
            else: parts.append(f" + {{ts}}")
    canon = ' '.join(parts)
    if abs(g) > 1: canon = f"{{g}}*({{canon}})"
    return canon

def _group_terms(expr_str):
    tree = _parse(expr_str)
    canon = _canonicalize(tree)
    canon_tree = _parse(canon)
    node = _normalize_sub(canon_tree)
    terms = _extract_terms(node)
    grouped = {{}}
    for t in terms:
        k = tuple(sorted(t['vars'].items()))
        grouped[k] = grouped.get(k, 0) + t['coeff']
    return grouped

def fingerprint(expr):
    grouped = _group_terms(expr)
    state = 0
    xor_acc = 0
    for k in sorted(grouped.keys()):
        c = grouped[k]
        for var, exp in k:
            state = (state + c * ord(var) * _C_VAR + exp * _C_EXP) & MASK64
        xor_acc ^= ((c * _C_NL) & MASK64)
    state ^= xor_acc
    return (state + _SEED) & MASK64
'''


# =========================================================================
# Main
# =========================================================================

if __name__ == '__main__':
    with open('/app/data/samples.jsonl') as f:
        samples = [json.loads(line) for line in f if line.strip()]

    print("Deriving all constants from samples...", file=sys.stderr)
    Cv, Ce, S, C_nl = derive_all(samples)
    print(f"  SEED  = {S:#018x}", file=sys.stderr)
    print(f"  C_NL  = {C_nl:#018x}", file=sys.stderr)
    print(f"  C_VAR = {Cv:#018x}", file=sys.stderr)
    print(f"  C_EXP = {Ce:#018x}", file=sys.stderr)

    ok = sum(1 for s in samples if fingerprint_with(s['expr'], Cv, Ce, S, C_nl) == int(s['signature']))
    print(f"  Verified: {ok}/{len(samples)}", file=sys.stderr)
    if ok != len(samples):
        print("ERROR", file=sys.stderr)
        sys.exit(1)

    fp_code = FP_CODE.format(SEED=hex(S), C_NL=hex(C_nl), C_VAR=hex(Cv), C_EXP=hex(Ce))
    with open('/app/fingerprint.py', 'w') as f:
        f.write(fp_code)
    print("Written /app/fingerprint.py", file=sys.stderr)
