A document services firm lost the source code for their filing-preparation pipeline during a server migration. The pipeline reads raw client submission files and produces cleaned, template-filled final documents for court filing. The only surviving artifacts are 20 archived input-output pairs in `/app/data/samples.jsonl`, plus the raw input files themselves under `/app/data/inputs/`.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (the filename under `/app/data/inputs/`), `"output"` (the finalized text), and `"data"` (the dictionary used for template substitution). The pipeline processes files in three stages applied in order:

1. The raw input file is decoded from its character encoding. Files may be UTF-8, UTF-16LE with BOM (two bytes `0xFF 0xFE` at the start), or ISO-8859-1. For files that lack a BOM or null-byte pattern, the pipeline attempts UTF-8 decoding first; if that fails with a decoding error, it falls back to ISO-8859-1.

2. Template substitution is applied to the decoded text. Substrings of the form `{KEY}` are replaced with the value of `KEY` from the data dictionary provided alongside that query. Doubled braces `{{` and `}}` are escape sequences that produce a single literal brace character and do not trigger substitution. An unmatched closing brace `}` appearing without a corresponding opening brace passes through unchanged. Empty braces `{}` are not substituted. Valid keys consist of alphanumeric characters, underscores, and hyphens.

3. Whitespace normalization processes the expanded text. Tabs are expanded to 4-space stops. Trailing whitespace on each line is removed. Consecutive blank lines (lines that are empty or contain only whitespace before stripping) are collapsed to a single empty line.

Reconstruct the full pipeline from the 20 visible samples, then write `/app/output/documents.jsonl` containing the processed output for every query in `/app/data/queries.jsonl`. Each query line is `{"input": "<filename>", "data": {...}}` — read the raw bytes from `/app/data/inputs/<filename>`, apply the pipeline using the provided data dictionary, and emit `{"input": "<filename>", "output": "<processed text>"}` preserving input order. The queries include held-out files distinct from the 20 samples.

Your implementation must be pure Python standard library — do not invoke external processes or use network access. The original pipeline source code no longer exists.

The verifier checks `/app/output/documents.jsonl` for exact byte-for-byte string equality against the reference. Every input file has exactly one correct output. Any character-level difference fails the task.
