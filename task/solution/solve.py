"""
Reference solution for fingerprint reconstruction.

Derives all 4 constants from the visible samples, then implements
the fingerprint algorithm and applies it to the query inputs.
"""

import json
import sys

MASK64 = (1 << 64) - 1


def mod_inv(a, mod):
    return pow(a, -1, mod)


def derive_constants(samples):
    sig = {s["input"]: int(s["fingerprint"], 16) for s in samples}
    SEED = sig[""]

    # C_NL from "1" (ord=49, odd → invertible mod 2^64)
    c_nl = ((sig["1"] - SEED) * mod_inv(49, 1 << 64)) & MASK64

    def xor_contrib(text):
        acc = 0
        for ch in text:
            c = ord(ch) & 0x7F
            acc ^= ((c * c_nl) & MASK64)
        return acc

    eq_rows = []
    for s in samples:
        text = s["input"]
        if len(text) <= 1:
            continue
        sig = int(s["fingerprint"], 16)
        linear_part = ((sig - SEED) & MASK64) ^ xor_contrib(text)
        rhs = linear_part
        sc = se = 0
        for i, ch in enumerate(text):
            if i == 0:
                continue
            c = ord(ch) & 0x7F
            sc = (sc + c * i) & MASK64
            se = (se + c * c) & MASK64
        eq_rows.append((sc, se, rhs))

    for i in range(len(eq_rows)):
        sc1, se1, rhs1 = eq_rows[i]
        for j in range(i + 1, len(eq_rows)):
            sc2, se2, rhs2 = eq_rows[j]
            det = (sc1 * se2 - sc2 * se1) & MASK64
            if det & 1 == 0:
                continue
            inv_det = mod_inv(det, 1 << 64)
            C_VAR = ((rhs1 * se2 - rhs2 * se1) * inv_det) & MASK64
            C_EXP = ((sc1 * rhs2 - sc2 * rhs1) * inv_det) & MASK64
            return SEED, c_nl, C_VAR, C_EXP
    raise RuntimeError("No invertible equation pair found")


def fingerprint(text, SEED, C_NL, C_VAR, C_EXP):
    state = 0
    xor_acc = 0
    for i, ch in enumerate(text):
        c = ord(ch) & 0x7F
        if i > 0:
            state = (state + c * C_VAR * i + c * c * C_EXP) & MASK64
        xor_acc ^= ((c * C_NL) & MASK64)
    state ^= xor_acc
    return (state + SEED) & MASK64


def solve(in_path, out_path):
    with open(in_path) as f:
        queries = [json.loads(line) for line in f if line.strip()]
    with open("/app/data/samples.jsonl") as f:
        samples = [json.loads(line) for line in f if line.strip()]
    SEED, C_NL, C_VAR, C_EXP = derive_constants(samples)
    results = []
    for q in queries:
        fp = fingerprint(q["input"], SEED, C_NL, C_VAR, C_EXP)
        results.append({"input": q["input"], "fingerprint": f"{fp:016x}"})
    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <queries.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)
    solve(sys.argv[1], sys.argv[2])
