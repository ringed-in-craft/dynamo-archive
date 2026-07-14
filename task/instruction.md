The file `/app/xform` is a stripped 64-bit ELF binary. It reads stdin, applies a transformation,
and writes the result to stdout. The output length equals the input length with no framing.
The original source code is lost.

Three sample input/output pairs are provided:

- `/app/data/sample1.in` → `/app/data/sample1.out`
- `/app/data/sample2.in` → `/app/data/sample2.out`
- `/app/data/sample3.in` → `/app/data/sample3.out`

Run the binary directly to test hypotheses: `/app/xform < /app/data/sample1.in | xxd`

Write `/app/output/solution.py` exposing `transform(data: bytes) -> bytes` that produces the
exact same output as `/app/xform` for any input. Pure Python 3 standard library only — must not
invoke `/app/xform` or any external process. `transform(b"")` must match the binary's output
on empty stdin.

The binary will NOT be present when your solution is graded. Use it now to reverse-engineer
the transformation algorithm for all possible inputs.
