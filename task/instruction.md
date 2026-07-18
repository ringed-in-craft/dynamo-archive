The file `/app/data/samples.jsonl` contains 20 archived expression-signature pairs from a computational algebra group's in-house CAS. Each line is a JSON object with `"expr"` (a polynomial expression string in infix notation) and `"signature"` (the 64-bit integer the system's internal deduplication function produced for that expression).

The deduplication function maps each expression to a 64-bit fingerprint by first canonicalizing the expression then computing a signature from the canonical form. Only these 20 archived pairs survive. Reconstruct the fingerprint function.

Write a self-contained Python 3 module at `/app/fingerprint.py` that exports:

    `fingerprint(expr: str) -> int`

Given any polynomial expression string in the same dialect, it must return the exact 64-bit integer signature the original system would have produced.

Expression dialect: variables are single lowercase letters `a`-`z`, coefficients are signed integers, operators are `+` `-` `*` `^`. `^` is exponentiation and is right-associative. Multiplication uses explicit `*` (write `2*x`, not `2x`). Operator precedence: `^` highest, then `*`, then `+` and `-` (lowest). Parentheses `()` may be used for grouping. Unary minus is supported: `-x`, `-(a+b)`. Whitespace is not significant.

Your `fingerprint()` must reproduce all 20 sample signatures exactly. It will also be tested against held-out expressions from the same archive, which you do not have access to.

`/app/fingerprint.py` must use only the Python standard library, be no larger than 50 KB, contain no base64-encoded data, embedded binary objects, or precomputed lookup tables keyed on specific expression strings. Compute every signature algorithmically from the expression string alone. Do not read any files or access the network.
