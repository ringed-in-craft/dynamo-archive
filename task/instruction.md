A computational geometry team lost the source code for their mesh-quality scoring routine during a server migration. The routine takes a triangle defined by three 2D vertex coordinate pairs and produces a 64-bit quality score used to prioritize mesh refinement in a finite-element solver. The only surviving artifacts are 20 archived triangle-score pairs in `/app/data/samples.jsonl`.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (three coordinate pairs, each a list of two integers) and `"score"` (the 16-character lowercase hex quality score). The score is a linear combination of the triangle's three sorted squared edge lengths modulo 2^64 — compute the squared edge lengths from the integer vertex coordinates using exact integer arithmetic, sort them ascending, then combine them with hidden coefficients. All coefficients are recoverable from the 20 visible samples.

Reconstruct the scoring function from the samples, then write `/app/output/scores.jsonl` containing the score for every triangle listed in `/app/data/queries.jsonl`. Each query line is `{"input": [[x1,y1],[x2,y2],[x3,y3]]}` — compute the score for each and emit one JSON object per line: `{"input": [...], "score": "<16-char hex>"}` preserving input order.

Your implementation must be pure Python standard library — do not invoke external processes or use network access. The original source code no longer exists.

The verifier checks the output against a pre-computed golden reference for exact hex string equality. Every triangle has exactly one correct score. Any deviation fails.
