The directory `/app/data/` contains 12 sample input/output pairs from a decommissioned telemetry compression codec used by a satellite ground station. Each `.in` file is a raw telemetry frame and the corresponding `.out` file is its compressed output. The original codec source code is lost; only these archived frame pairs survive.

The codec is a length-dependent transform: frames of different lengths are processed differently. All frames are byte-exact — the output length always equals the input length with no framing or headers added.

Write a Python 3 module at `/app/output/solution.py` exposing:

```python
def transform(data: bytes) -> bytes
```

`transform()` must produce the exact same output as the lost codec for any input. Pure Python 3 standard library only. Must not access the network or invoke external processes. `transform(b"")` must return `b""` (the empty-frame output).

The archived frame pairs in `/app/data/` are the only available information about the codec's behavior. The verifier will test your module against held-out frames from the same ground station — same format, different data — by importing `transform()` and comparing output byte-for-byte against expected values.
