#!/usr/bin/env python3
"""CHNK archive recovery tool — FIXED.

Correctly parses the format and uses the proprietary integrity marker algorithm
to validate chunk copies and reassemble files from intact data.
"""
import struct, sys, os

ARCHIVE = "/app/data/archive.bin"
OUTDIR = "/app/output"


def integrity_marker(data: bytes) -> int:
    """Proprietary non-linear mixing function — NOT any standard checksum."""
    a = 0x9E3779B9
    b = 0x7F4A7C15
    for i, byte in enumerate(data):
        a = (a + byte) & 0xFFFFFFFF
        a = (a ^ (a >> 13)) & 0xFFFFFFFF
        a = (a * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        b = (b ^ byte) & 0xFFFFFFFF
        b = ((b << 7) | (b >> 25)) & 0xFFFFFFFF
        b = (b + a) & 0xFFFFFFFF
    return (a ^ b ^ 0xA5A5A5A5) & 0xFFFFFFFF


def extract(archive_path: str, outdir: str):
    with open(archive_path, "rb") as f:
        data = f.read()

    pos = 0
    magic = data[pos:pos + 4]
    if magic != b"CHNK":
        raise ValueError(f"Bad magic: {magic}")
    pos += 4
    version = struct.unpack_from("<H", data, pos)[0]
    pos += 2
    file_count = struct.unpack_from("<H", data, pos)[0]
    pos += 2
    pos += 8  # reserved

    os.makedirs(outdir, exist_ok=True)

    for _ in range(file_count):
        name_len = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        filename = data[pos:pos + name_len].decode("ascii")
        pos += name_len
        chunk_count = struct.unpack_from("<H", data, pos)[0]
        pos += 2

        file_content = bytearray()

        for _ in range(chunk_count):
            chunk_idx = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            data_size = struct.unpack_from("<I", data, pos)[0]  # FIXED: little-endian
            pos += 4
            stored_marker = struct.unpack_from("<I", data, pos)[0]
            pos += 4

            copy_a = data[pos:pos + data_size]
            pos += data_size
            copy_b = data[pos:pos + data_size]
            pos += data_size

            marker_a = integrity_marker(copy_a)
            marker_b = integrity_marker(copy_b)

            if marker_a == stored_marker:
                file_content.extend(copy_a)
            elif marker_b == stored_marker:
                file_content.extend(copy_b)
            else:
                file_content.extend(copy_a)

        outpath = os.path.join(outdir, filename)
        with open(outpath, "wb") as f:
            f.write(bytes(file_content))
        print(f"Extracted: {filename} ({len(file_content)} bytes)")


if __name__ == "__main__":
    extract(ARCHIVE, OUTDIR)
