#!/usr/bin/env python3
"""Oracle solution — writes the correct transform module."""

import os

SOLUTION = r'''"""Telemetry codec — reconstructed from archived frame pairs."""

import struct


def transform(data: bytes) -> bytes:
    if len(data) <= 16:
        return _short(data)
    return _long(data)


def _short(data: bytes) -> bytes:
    s = 0xDEADBEEF
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ (s & 0xFF)
        s = ((s << 7) | (s >> 25)) + 0x9E3779B9
        s &= 0xFFFFFFFF
    return bytes(out)


def _long(data: bytes) -> bytes:
    k0 = 0x9E3779B97F4A7C15
    k1 = 0xBB67AE8584CAA73B
    k0 ^= (k0 >> 33)
    k0 = (k0 * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    k0 ^= (k0 >> 33)
    k1 ^= (k1 >> 33)
    k1 = (k1 * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    k1 ^= (k1 >> 33)
    s = [
        (k0 >> 0)  & 0xFFFFFFFF,
        (k0 >> 32) & 0xFFFFFFFF,
        (k1 >> 0)  & 0xFFFFFFFF,
        (k1 >> 32) & 0xFFFFFFFF,
    ]
    out = bytearray()
    pos = 0
    while pos + 4 <= len(data):
        word = struct.unpack("<I", data[pos:pos + 4])[0]
        t = s[0]
        t ^= (t << 9) & 0xFFFFFFFF
        t ^= (t >> 14)
        s[0] = s[1]
        s[1] = s[2]
        s[2] = s[3]
        w = s[3]
        w ^= (w >> 6)
        w ^= t
        w = (w + 0x9E3779B9) & 0xFFFFFFFF
        ks = w
        w ^= word
        s[3] = w
        out.extend(struct.pack("<I", word ^ ks))
        pos += 4
    if pos < len(data):
        tail_len = len(data) - pos
        word = int.from_bytes(data[pos:] + b'\x00' * (4 - tail_len), 'little')
        t = s[0]
        t ^= (t << 9) & 0xFFFFFFFF
        t ^= (t >> 14)
        s[0] = s[1]
        s[1] = s[2]
        s[2] = s[3]
        w = s[3]
        w ^= (w >> 6)
        w ^= t
        w = (w + 0x9E3779B9) & 0xFFFFFFFF
        ks = w
        out_ks = ks.to_bytes(4, 'little')
        for i in range(tail_len):
            out.append(data[pos + i] ^ out_ks[i])
    return bytes(out)
'''


def main():
    os.makedirs("/app/output", exist_ok=True)
    with open("/app/output/solution.py", "w") as f:
        f.write(SOLUTION)


if __name__ == "__main__":
    main()
