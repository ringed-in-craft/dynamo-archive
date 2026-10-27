"""
Reference solution: derive tridiagonal + non-linear transform from I/O pairs.

Derivation (all over Z/2^64):
  1. From zero vector of length >= 2:
     z[0] = C_NL + SEED, z[1] = 2*C_NL + SEED
     => C_NL = z[1] - z[0], SEED = z[0] - C_NL
  2. With C_NL and SEED known, strip the non-linear layer from each sample
  3. From unit basis vectors, isolate C_OFF and C_DIAG from the tridiagonal
"""

import json
import sys

MASK64 = (1 << 64) - 1


def derive_constants(samples):
    sig = {json.dumps(s["input"]): s["output"] for s in samples}

    # Step 1: C_NL and SEED from zero vector of length >= 2
    zero_vec = [0, 0]
    z_key = json.dumps(zero_vec)
    z = sig.get(z_key)
    if z is None:
        # Find any zero vector with len >= 2
        for s in samples:
            if len(s["input"]) >= 2 and all(v == 0 for v in s["input"]):
                z = s["output"]
                break
    if z is None:
        raise RuntimeError("No zero vector of length >= 2 in samples")

    C_NL = (z[1] - z[0]) & MASK64
    SEED = (z[0] - C_NL) & MASK64

    # Step 2: Strip non-linear layer to get linear output y
    def strip_nl(vec_in, vec_out):
        return [((vec_out[i] - SEED) & MASK64) ^ (C_NL * (i + 1)) for i in range(len(vec_out))]

    # Step 3: From unit basis vectors, recover C_DIAG and C_OFF
    # Find a unit vector [1,0,0,...] of length >= 3
    unit_samples = [s for s in samples if len(s["input"]) >= 3 and sum(1 for v in s["input"] if v != 0) == 1]
    if len(unit_samples) < 2:
        raise RuntimeError("Need at least 2 unit-vector samples")

    # From a unit at position 0 (e.g. [1,0,0,0,0]):
    #   y[0] = C_DIAG * 1, y[1] = C_OFF * 1 (right neighbor)
    # From a unit at position n-1 (e.g. [0,0,0,0,1]):
    #   y[n-2] = C_OFF * 1 (left neighbor)

    C_DIAG = None
    C_OFF = None

    for s in unit_samples:
        vec = s["input"]
        n = len(vec)
        y = strip_nl(vec, s["output"])
        for i, v in enumerate(vec):
            if v == 1:
                if i == 0:
                    # y[0] = C_DIAG * 1 * 1 = C_DIAG
                    C_DIAG = y[0]
                    if n >= 2 and C_OFF is None:
                        # y[1] = C_OFF * 1 (right neighbor of position 0)
                        C_OFF = y[1]
                elif i == n - 1:
                    # y[n-2] = C_OFF * 1 (left neighbor of position n-1)
                    if C_OFF is None:
                        C_OFF = y[n - 2]
                else:
                    # interior unit: y[i-1] = C_OFF, y[i] = C_DIAG*(i+1)
                    if C_OFF is None:
                        C_OFF = y[i - 1]
                    if C_DIAG is None:
                        C_DIAG = y[i]
                        # y[i] = C_DIAG * (i+1)
                        # Actually: y[i] = vec[i] * C_DIAG * (i+1) = C_DIAG * (i+1)
                        # So C_DIAG = y[i] / (i+1), but over Z/2^64 we need modular inverse
                        # Since i+1 is usually small and the result fits, we can compute directly
                        # BUT: C_DIAG is the multiplier, not the product
                        # y[i] = C_DIAG * (i+1)
                        # Check: is y[i] divisible by (i+1)?
                        # In our algorithm, C_DIAG is the constant, and C_DIAG*(i+1) is the value
                        # So extracting C_DIAG from interior requires proper handling

    # Better approach: use the unit-at-0 to get C_DIAG directly
    # y[0] = x[0] * C_DIAG * 1 = C_DIAG (for x[0]=1)
    # y[1] = x[1] * C_DIAG * 2 + x[0] * C_OFF = 0 + C_OFF (for x[0]=1, x[1]=0)

    if C_DIAG is None or C_OFF is None:
        # Try a different approach: look for [1,0,0,...]
        for s in unit_samples:
            vec = s["input"]
            n = len(vec)
            y = strip_nl(vec, s["output"])
            for i, v in enumerate(vec):
                if v == 1 and i == 0:
                    C_DIAG = y[0]
                    if n >= 2:
                        C_OFF = y[1]
                    break

    if C_DIAG is None or C_OFF is None:
        raise RuntimeError(f"Could not derive C_DIAG ({C_DIAG}) or C_OFF ({C_OFF})")

    return C_OFF, C_DIAG, C_NL, SEED


def transform(vector, C_OFF, C_DIAG, C_NL, SEED):
    n = len(vector)
    y = [0] * n
    for i in range(n):
        diag = vector[i] * C_DIAG * (i + 1)
        left = vector[i-1] * C_OFF if i > 0 else 0
        right = vector[i+1] * C_OFF if i < n-1 else 0
        y[i] = (diag + left + right) & MASK64
    z = [((y[i] ^ (C_NL * (i + 1))) + SEED) & MASK64 for i in range(n)]
    return z


def solve(in_path, out_path):
    with open(in_path) as f:
        queries = [json.loads(line) for line in f if line.strip()]
    with open("/app/data/samples.jsonl") as f:
        samples = [json.loads(line) for line in f if line.strip()]

    C_OFF, C_DIAG, C_NL, SEED = derive_constants(samples)

    results = []
    for q in queries:
        vec = q["input"]
        out = transform(vec, C_OFF, C_DIAG, C_NL, SEED)
        results.append({"input": vec, "output": out})

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <queries.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)
    solve(sys.argv[1], sys.argv[2])
