"""
Reference solution: recover tridiagonal + non-linear transform from I/O pairs.

Recovers 4 constants from 2 identity samples using 4 lines of modular arithmetic.
The remaining 19 samples are agent-facing: they confirm the model, distinguish
XOR-then-add from additive-only, and demonstrate position scaling across lengths.

Algorithm (all mod 2^64):
  y[i] = C_OFF*x[i-1] + C_DIAG*(i+1)*x[i] + C_OFF*x[i+1]
  z[i] = (y[i] ^ (C_NL * (i+1))) + SEED

Recovery (4 lines of algebra):
  Zero vector: z[0]=C_NL+SEED, z[1]=2*C_NL+SEED -> C_NL=z[1]-z[0], SEED=z[0]-C_NL
  Unit at pos 0: C_DIAG = (z[0] - SEED) ^ C_NL, C_OFF = (z[1] - SEED) ^ (2*C_NL)
"""

import json, sys

MASK64 = (1 << 64) - 1


def recover(samples):
    sig = {}
    for s in samples:
        sig[json.dumps(s["input"])] = s["output"]

    zero_key = json.dumps([0, 0])
    z = sig[zero_key]
    C_NL = (z[1] - z[0]) & MASK64
    SEED = (z[0] - C_NL) & MASK64

    unit_key = json.dumps([1, 0, 0, 0, 0])
    u = sig[unit_key]
    C_DIAG = ((u[0] - SEED) & MASK64) ^ ((C_NL * 1) & MASK64)
    C_OFF = ((u[1] - SEED) & MASK64) ^ ((C_NL * 2) & MASK64)

    return C_OFF, C_DIAG, C_NL, SEED


def transform(vec, C_OFF, C_DIAG, C_NL, SEED):
    n = len(vec)
    y = [0] * n
    for i in range(n):
        left = vec[i-1] * C_OFF if i > 0 else 0
        diag = vec[i] * C_DIAG * (i + 1)
        right = vec[i+1] * C_OFF if i < n-1 else 0
        y[i] = (left + diag + right) & MASK64
    return [((y[i] ^ (C_NL * (i + 1))) + SEED) & MASK64 for i in range(n)]


def solve(in_path, out_path):
    with open(in_path) as f:
        queries = [json.loads(line) for line in f if line.strip()]
    with open("/app/data/samples.jsonl") as f:
        samples = [json.loads(line) for line in f if line.strip()]

    C_OFF, C_DIAG, C_NL, SEED = recover(samples)

    results = []
    for q in queries:
        out = transform(q["input"], C_OFF, C_DIAG, C_NL, SEED)
        results.append({"input": q["input"], "output": out})

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <queries.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)
    solve(sys.argv[1], sys.argv[2])
