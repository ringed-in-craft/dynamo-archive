A document services firm lost the source code for their filing-preparation pipeline during a server migration. The pipeline reads raw client submission files and produces cleaned, template-filled final documents for court filing. The only surviving artifacts are 20 archived input-output pairs in `/app/data/samples.jsonl`, plus the raw input files themselves under `/app/data/inputs/`.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (the filename under `/app/data/inputs/`), `"output"` (the finalized text), and `"data"` (the dictionary used for template substitution). The pipeline performs character decoding, placeholder substitution, and whitespace normalization — the exact rules and their ordering are all recoverable from the 20 visible samples, which exercise every parameter of the pipeline.

Reconstruct the full pipeline from the visible samples, then write `/app/output/documents.jsonl` containing the processed output for every query in `/app/data/queries.jsonl`. Each query line is `{"input": "<filename>", "data": {...}}` — read the raw bytes from `/app/data/inputs/<filename>`, apply the pipeline using the provided data dictionary, and emit `{"input": "<filename>", "output": "<processed text>"}` preserving input order. The queries include held-out files distinct from the 20 samples.

Your implementation must be pure Python standard library — do not invoke external processes or use network access. The original pipeline source code no longer exists.

The verifier checks `/app/output/documents.jsonl` for exact byte-for-byte string equality against the reference. Every input file has exactly one correct output. Any character-level difference fails the task.
