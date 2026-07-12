"""Reference implementation of the xform stream cipher transform.

Derived from reverse-engineering /app/xform:
  - 128-bit state (4 x 32-bit words), initialized via key mixing
  - Non-linear mixing round: custom xorshift-like with shift triples (9,14,6)
    plus an additive constant 0x9E3779B9
  - 4-byte chunked processing with state-dependent tail handling
"""
import struct

# Initial state — extracted from the binary's init section.
# NOTE: the compiler's register allocation shuffles the order from what
# the C source produces. Correct ordering determined by matching output.
_S0 = 0x3702a9e6
_S1 = 0x9341ca26
_S2 = 0x0a4e2902
_S3 = 0x49445473


def _step(s):
    """Advance state by one round, return the 32-bit output word."""
    s0, s1, s2, s3 = s
    t = s0
    t ^= (t << 9) & 0xFFFFFFFF
    t ^= (t >> 14)
    n0 = s1
    n1 = s2
    n2 = s3
    w = s3
    w ^= (w >> 6)
    w ^= t
    w = (w + 0x9E3779B9) & 0xFFFFFFFF
    n3 = w
    s[0] = n0
    s[1] = n1
    s[2] = n2
    s[3] = n3
    return w


def transform(data: bytes) -> bytes:
    """Apply the xform stream cipher to data, returning transformed bytes."""
    s = [_S0, _S1, _S2, _S3]
    out = bytearray()
    pos = 0

    # Process full 4-byte chunks
    while pos + 4 <= len(data):
        w = _step(s)
        out.append(data[pos] ^ ((w >> 0) & 0xFF))
        out.append(data[pos + 1] ^ ((w >> 8) & 0xFF))
        out.append(data[pos + 2] ^ ((w >> 16) & 0xFF))
        out.append(data[pos + 3] ^ ((w >> 24) & 0xFF))
        pos += 4

    # Tail: 0-3 leftover bytes, one step produces 4 keystream bytes
    if pos < len(data):
        w = _step(s)
        while pos < len(data):
            out.append(data[pos] ^ (w & 0xFF))
            w >>= 8
            pos += 1

    return bytes(out)
