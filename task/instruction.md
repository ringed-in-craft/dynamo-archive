The file `/app/xform` is a stripped 64-bit ELF binary. It reads all of stdin, applies a
proprietary stream cipher transformation, and writes the result to stdout. The output has the
same length as the input and contains no framing — it is the raw transformed bytes. The original
source code is lost.

Three sample input/output pairs are provided:

- `/app/data/sample1.in` → `/app/data/sample1.out`
- `/app/data/sample2.in` → `/app/data/sample2.out`
- `/app/data/sample3.in` → `/app/data/sample3.out`

You can run the binary directly to test hypotheses: `/app/xform < /app/data/sample1.in | xxd`

Write `/app/output/solution.py` exposing a function `transform(data: bytes) -> bytes` that
produces the exact same output as `/app/xform` for any input. The function must be a pure
Python 3 implementation using only the standard library — it must not invoke `/app/xform` or
any external process. `transform(b"")` must produce the binary's output on empty stdin.

The binary will NOT be present when your solution is graded. Use it now to reverse-engineer
the transformation algorithm.
