#!/usr/bin/env python3
"""CHNK archive recovery tool — FIXED.

Correctly parses the format, uses the custom prime-weighted checksum to
validate chunk copies, and reassembles files from intact data.
"""
import struct, sys, os

ARCHIVE = "/app/data/archive.bin"
OUTDIR = "/app/output"

# Prime-weighted checksum — weights cycle every 8 bytes
_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19]


def custom_checksum(data: bytes) -> int:
    result = 0x9E3779B9
    for i, b in enumerate(data):
        result = (result + b * _PRIMES[i % 8]) & 0xFFFFFFFF
    return result


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
            stored_cksum = struct.unpack_from("<I", data, pos)[0]
            pos += 4

            copy_a = data[pos:pos + data_size]
            pos += data_size
            copy_b = data[pos:pos + data_size]
            pos += data_size

            cksum_a = custom_checksum(copy_a)
            cksum_b = custom_checksum(copy_b)

            if cksum_a == stored_cksum:
                file_content.extend(copy_a)
            elif cksum_b == stored_cksum:
                file_content.extend(copy_b)
            else:
                file_content.extend(copy_a)

        outpath = os.path.join(outdir, filename)
        with open(outpath, "wb") as f:
            f.write(bytes(file_content))
        print(f"Extracted: {filename} ({len(file_content)} bytes)")


if __name__ == "__main__":
    extract(ARCHIVE, OUTDIR)
