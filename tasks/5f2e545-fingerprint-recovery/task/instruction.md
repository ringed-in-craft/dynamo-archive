A proprietary data-integrity tool used by a financial settlement system was lost during a server migration. The only surviving artifacts are 20 archived input-output pairs in `/app/data/samples.jsonl` — short text strings and their 16-character lowercase hex fingerprints, captured from the tool's production log before it was lost.

Each line of `/app/data/samples.jsonl` is a JSON object with `"input"` (the string that was fingerprinted) and `"fingerprint"` (the 16-char hex result). The fingerprint function is a custom 64-bit algorithm — it is not any published or standard hash function.

Reconstruct the fingerprint algorithm from the samples, then write `/app/output/fingerprints.jsonl` containing the fingerprint for every input string listed in `/app/data/queries.jsonl`. Each line of `/app/data/queries.jsonl` is `{"input": "<string>"}` — you must compute the fingerprint for each and emit one JSON object per line: `{"input": "<string>", "fingerprint": "<16-char hex>"}`. Output order must match input order.

The fingerprint is a deterministic custom mathematical function operating on the ASCII byte values of the input string over 64-bit unsigned integers with wrap-around at 2^64. All parameters needed to reconstruct the function are recoverable from the 20 visible samples.

Your implementation must be pure Python standard library and compute the fingerprint from first principles — do not invoke external processes, use network access, or attempt to locate the original tool (it no longer exists).

The verifier will check `/app/output/fingerprints.jsonl` for exact string equality against the reference. Every input in the queries file has exactly one correct 16-char hex output. Any deviation from the expected value on any input fails the task.
