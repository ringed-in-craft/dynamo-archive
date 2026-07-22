A computational mathematics team lost the source code for a custom sparse-matrix transform used in their spectral element solver. The routine applies a banded linear operator followed by a numerical stability encoding. The only surviving artifacts are 20 archived input-output vector pairs in `/app/data/samples.jsonl`, captured from the solver's production runs before the source was lost.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (a list of integers) and `"output"` (the resulting encoded vector as a list of integers). The transform is a deterministic mathematical function operating on 64-bit unsigned integers with wrap-around at 2^64 — it is not any published algorithm.

Reconstruct the transform from the samples, then write `/app/output/transforms.jsonl` containing the encoded output for every input vector listed in `/app/data/queries.jsonl`. Each line of `/app/data/queries.jsonl` is `{"input": [v1, v2, ...]}` — compute the encoded output vector for each and emit `{"input": [...], "output": [...]}`, preserving input order. All parameters needed to reconstruct the transform are recoverable from the 20 visible samples.

Your implementation must be pure Python standard library and compute the transform from first principles — do not invoke external processes or use network access. The original source code no longer exists and cannot be located online.

The verifier checks `/app/output/transforms.jsonl` for exact element-by-element integer equality against the reference. Every input vector has exactly one correct output. Any deviation on any element of any vector fails the task.
