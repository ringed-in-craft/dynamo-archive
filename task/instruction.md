A computational geometry team lost the source code for their mesh-quality scoring routine during a server migration. The routine takes a triangle defined by three 2D vertex coordinate pairs and produces a 64-bit quality score used to prioritize mesh refinement in a finite-element solver. The only surviving artifacts are 20 archived triangle-score pairs in `/app/data/samples.jsonl`.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (three coordinate pairs, each a list of two integers) and `"score"` (the 16-character lowercase hex quality score). The score is a deterministic mathematical function of the triangle's sorted squared edge lengths, operating on 64-bit unsigned integers with wrap-around at 2^64. All parameters needed to produce correct scores are recoverable from the 20 visible samples.

Reconstruct the scoring function from the samples, then write `/app/audit.py` runnable as `python3 /app/audit.py <queries.jsonl> <output.jsonl>`. The queries file has the same format as the samples file but without score values — compute the score for each triangle and write `<output.jsonl>` with one JSON object per line: `{"input": [...], "score": "<16-char hex>"}` preserving input order.

Your implementation must be pure Python standard library — do not invoke external processes or use network access. The original source code no longer exists.

The verifier checks the output against a pre-computed golden reference for exact hex string equality. Every triangle has exactly one correct score. Any deviation fails.
