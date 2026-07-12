"""Reference implementation of the xform stream cipher transform.

Derived from reverse-engineering /app/xform:
  - 128-bit state (4 x 32-bit words), initialized via key mixing
  - Non-linear mixing round: custom xorshift-like with shift triples (9,14,6)
    plus an additive constant 0x9E3779B9
  - INPUT-DEPENDENT: each 4-byte input word feeds back into state via XOR
  - 4-byte chunked processing with state-dependent tail handling
"""
import struct

_S0 = 0x3702a9e6
_S1 = 0x9341ca26
_S2 = 0x0a4e2902
_S3 = 0x49445473


def _step(s, input_word):
    """Advance state, mix in input_word, return the keystream word."""
    s0, s1, s2, s3 = s
    t = s0
    t ^= (t << 9) & 0xFFFFFFFF
    t ^= (t >> 14)
    n0, n1, n2 = s1, s2, s3
    w = s3
    w ^= (w >> 6)
    w ^= t
    w = (w + 0x9E3779B9) & 0xFFFFFFFF
    result = w
    n3 = w ^ input_word
    s[0] = n0
    s[1] = n1
    s[2] = n2
    s[3] = n3
    return result


def transform(data: bytes) -> bytes:
    """Apply the xform stream cipher to data, returning transformed bytes."""
    s = [_S0, _S1, _S2, _S3]
    out = bytearray()
    pos = 0

    while pos + 4 <= len(data):
        word = (data[pos]
              | (data[pos + 1] << 8)
              | (data[pos + 2] << 16)
              | (data[pos + 3] << 24))
        w = _step(s, word)
        out.append(data[pos] ^ ((w >> 0) & 0xFF))
        out.append(data[pos + 1] ^ ((w >> 8) & 0xFF))
        out.append(data[pos + 2] ^ ((w >> 16) & 0xFF))
        out.append(data[pos + 3] ^ ((w >> 24) & 0xFF))
        pos += 4

    if pos < len(data):
        word = 0
        r = 0
        while pos + r < len(data):
            word |= (data[pos + r] << (r * 8))
            r += 1
        w = _step(s, word)
        while pos < len(data):
            out.append(data[pos] ^ (w & 0xFF))
            w >>= 8
            pos += 1

    return bytes(out)
