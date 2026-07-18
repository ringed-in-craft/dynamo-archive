"""Expression fingerprint module.
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
