"""Reference implementation of the binary transform.

Length-dependent: ≤16 bytes uses simple XOR rotate, >16 bytes uses full
non-linear stream cipher with CFB feedback and custom shift triples (9,14,6).
"""
import struct


def _short_xform(data: bytes) -> bytes:
    """Simple XOR with rotating state (inputs ≤ 16 bytes)."""
    s = 0xDEADBEEF
    out = bytearray()
    for b in data:
        out.append(b ^ (s & 0xFF))
        s = (((s << 7) | (s >> 25)) + 0x9E3779B9) & 0xFFFFFFFF
    return bytes(out)


# Long transform state
_S0 = 0x3702a9e6
_S1 = 0x9341ca26
_S2 = 0x0a4e2902
_S3 = 0x49445473


def _long_step(s, input_word):
    s0, s1, s2, s3 = s
    t = s0
    t ^= (t << 9) & 0xFFFFFFFF
    t ^= (t >> 14)
    w = s3
    w ^= (w >> 6)
    w ^= t
    w = (w + 0x9E3779B9) & 0xFFFFFFFF
    result = w
    n3 = w ^ input_word
    return [s1, s2, s3, n3], result


def _long_xform(data: bytes) -> bytes:
    """Full non-linear stream cipher (inputs > 16 bytes)."""
    s = [_S0, _S1, _S2, _S3]
    out = bytearray()
    pos = 0
    while pos + 4 <= len(data):
        word = (data[pos] | (data[pos+1] << 8)
              | (data[pos+2] << 16) | (data[pos+3] << 24))
        s, ks = _long_step(s, word)
        out.append(data[pos] ^ ((ks >> 0) & 0xFF))
        out.append(data[pos+1] ^ ((ks >> 8) & 0xFF))
        out.append(data[pos+2] ^ ((ks >> 16) & 0xFF))
        out.append(data[pos+3] ^ ((ks >> 24) & 0xFF))
        pos += 4
    if pos < len(data):
        word = 0
        r = 0
        while pos + r < len(data):
            word |= (data[pos+r] << (r*8))
            r += 1
        s, ks = _long_step(s, word)
        while pos < len(data):
            out.append(data[pos] ^ (ks & 0xFF))
            ks >>= 8
            pos += 1
    return bytes(out)


def transform(data: bytes) -> bytes:
    if len(data) <= 16:
        return _short_xform(data)
    return _long_xform(data)
