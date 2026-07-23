"""
Reference solution: recover mesh score from triangle-score pairs.

Score formula (all operations mod 2^64):
  score = e0*X1 + e1*X2 + e2*X3 + SEED
where e0,e1,e2 are sorted squared edge lengths, X1,X2,X3 are hidden
products (Xi = Ci * C_NL), and SEED is the final additive constant.

Recovery:
  1. Point triangle → SEED directly
  2. Line triangle L=1 → X2 + X3 = S23
  3. Proper triangles → linear system for X1, X2; then X3 = S23 - X2
  4. Only the products (X1,X2,X3,SEED) are needed for correct scores;
     individual Ci and C_NL are under-determined but irrelevant.
"""

import json, math, sys

MASK64 = (1 << 64) - 1


def sq_edges(triangle):
    (x1, y1), (x2, y2), (x3, y3) = triangle
    e1 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    e2 = (x3 - x2) ** 2 + (y3 - y2) ** 2
    e3 = (x1 - x3) ** 2 + (y1 - y3) ** 2
    return sorted([e1, e2, e3])


def score_triangle(triangle, X1, X2, X3, SEED):
    e = sq_edges(triangle)
    return (e[0] * X1 + e[1] * X2 + e[2] * X3 + SEED) & MASK64


def solve_linear_pair(a1, b1, r1, a2, b2, r2):
    """Solve a1*x + b1*y = r1, a2*x + b2*y = r2 (mod 2^64).
    Returns list of (x,y) candidate solutions."""
    det = (a1 * b2 - a2 * b1) & MASK64
    if det == 0:
        return []
    # Factor out powers of 2 from det
    v2 = det & -det
    det_r = det // v2
    mod_reduced = (1 << 64) // v2
    inv = pow(det_r % mod_reduced, -1, mod_reduced)

    num_x = (r1 * b2 - r2 * b1) & MASK64
    num_y = (a1 * r2 - a2 * r1) & MASK64

    if num_x % v2 != 0 or num_y % v2 != 0:
        return []

    x0 = ((num_x // v2) * inv) % mod_reduced
    y0 = ((num_y // v2) * inv) % mod_reduced

    # Lift: solve for dx, dy in {0,1} such that
    # a1*(x0+dx*2^63) + b1*(y0+dy*2^63) ≡ r1 (mod 2^64)
    # This gives: a1*dx + b1*dy ≡ (r1 - a1*x0 - b1*y0)/2^63 (mod 2)
    # Similarly: a2*dx + b2*dy ≡ (r2 - a2*x0 - b2*y0)/2^63 (mod 2)
    # This is a 2x2 linear system over GF(2).

    # If v2 > 2, we need multiple lifting steps. Handle v2 == 2 only for now
    # and do a general recursive lift for larger v2.

    results = []
    if v2 == 2:
        step = 1 << 63
        e1 = ((r1 - a1 * x0 - b1 * y0) >> 63) & 1
        e2 = ((r2 - a2 * x0 - b2 * y0) >> 63) & 1
        # Solve: a1*dx XOR b1*dy = e1, a2*dx XOR b2*dy = e2  over GF(2)
        for dx in (0, 1):
            for dy in (0, 1):
                if ((a1 & 1) * dx) ^ ((b1 & 1) * dy) == e1 and \
                   ((a2 & 1) * dx) ^ ((b2 & 1) * dy) == e2:
                    x = (x0 + dx * step) & MASK64
                    y = (y0 + dy * step) & MASK64
                    if ((a1 * x + b1 * y) & MASK64) == r1:
                        results.append((x, y))
    else:
        # General case: try all 2^k lifts
        step = mod_reduced
        for k in range(min(v2, 256)):  # cap to avoid huge loops
            x = (x0 + k * step) & MASK64
            y = (y0 + k * step) & MASK64
            if ((a1 * x + b1 * y) & MASK64) == r1 and \
               ((a2 * x + b2 * y) & MASK64) == r2:
                results.append((x, y))

    return results


def recover(samples_path):
    with open(samples_path) as f:
        samples = [json.loads(line) for line in f if line.strip()]

    # 1. SEED from point triangle
    pt_key = json.dumps([[0, 0], [0, 0], [0, 0]])
    sig = {}
    for s in samples:
        key = json.dumps(s["input"])
        sig[key] = int(s["score"], 16)
    SEED = sig.get(pt_key)
    if SEED is None:
        raise RuntimeError("No point triangle in samples")

    # 2. X2 + X3 from line triangle L=1
    line_key = json.dumps([[0, 0], [0, 0], [1, 0]])
    o1 = sig.get(line_key)
    S23 = (o1 - SEED) & MASK64  # X2 + X3

    # 3. Build linear system for X1, X2 from proper triangles
    rows = []
    for s in samples:
        tri = s["input"]
        e = sq_edges(tri)
        if e == [0, 0, 0]:
            continue
        if e[0] == 0 and e[1] == e[2]:
            continue  # line triangle
        obs = int(s["score"], 16)
        # e0*X1 + e1*X2 + e2*(S23-X2) + SEED = obs
        # e0*X1 + (e1-e2)*X2 = obs - SEED - e2*S23
        rhs = (obs - SEED - e[2] * S23) & MASK64
        rows.append((e[0], (e[1] - e[2]) & MASK64, rhs))

    # Try all pairs until one solves
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a1, b1, r1 = rows[i]
            a2, b2, r2 = rows[j]
            sols = solve_linear_pair(a1, b1, r1, a2, b2, r2)
            for X1, X2 in sols:
                X3 = (S23 - X2) & MASK64
                # Verify against all samples
                ok = True
                for s in samples:
                    pred = score_triangle(s["input"], X1, X2, X3, SEED)
                    if pred != int(s["score"], 16):
                        ok = False
                        break
                if ok:
                    return X1, X2, X3, SEED

    raise RuntimeError("Could not recover constants")


def solve(in_path, out_path):
    with open(in_path) as f:
        queries = [json.loads(line) for line in f if line.strip()]

    X1, X2, X3, SEED = recover("/app/data/samples.jsonl")

    results = []
    for q in queries:
        tri = q["input"]
        s = score_triangle(tri, X1, X2, X3, SEED)
        results.append({"input": tri, "score": f"{s:016x}"})

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <queries.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)
    solve(sys.argv[1], sys.argv[2])
