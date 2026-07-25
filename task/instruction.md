A computational linear algebra team lost the source code for a custom sparse-matrix transform used in their iterative solver framework. The routine takes a dense input vector and produces an encoded output vector. The only surviving artifacts are 21 archived input-output vector pairs in `/app/data/samples.jsonl`.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (a list of integers) and `"output"` (the resulting integer vector). The transform first applies a banded sparse linear operator and then applies an element-wise non-linear encoding — all operations are on 64-bit unsigned integers with wrap-around at 2^64. The linear operator couples each element to its immediate neighbors. Both the linear operator's diagonal weight and the non-linear encoding depend on position index within the vector. All parameters needed to produce correct outputs are recoverable from the 21 visible samples.

Reconstruct the full transform from the samples, then write `/app/output/transforms.jsonl` containing the encoded output for every input vector listed in `/app/data/queries.jsonl`. Each query line is `{"input": [v0, v1, ...]}` — compute the output vector for each and emit `{"input": [...], "output": [...]}` preserving input order. The queries include vectors of different lengths than any visible sample.

Your implementation must be pure Python standard library — do not invoke external processes or use network access. The original source code no longer exists.

The verifier checks `/app/output/transforms.jsonl` for exact element-by-element integer equality against the reference. Every input vector has exactly one correct output. Any deviation on any element fails the task.
