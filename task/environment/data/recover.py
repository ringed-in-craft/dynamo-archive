#!/usr/bin/env python3
"""CHNK archive recovery tool — recovers files from corrupted chunked archives.

Reads the CHNK format: each chunk stores two copies (A and B). At least one
copy is intact. The tool validates copies against stored checksums to select
the correct data and reassemble files.
"""
import struct, sys, os, zlib

ARCHIVE = "/app/data/archive.bin"
OUTDIR = "/app/output"


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
        chunks_ok = True

        for _ in range(chunk_count):
            chunk_idx = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            data_size = struct.unpack_from(">I", data, pos)[0]  # BUG: reads big-endian, spec says LE
            pos += 4
            stored_cksum = struct.unpack_from("<I", data, pos)[0]
            pos += 4

            copy_a = data[pos:pos + data_size]
            pos += data_size
            copy_b = data[pos:pos + data_size]
            pos += data_size

            # Select valid copy using checksum
            cksum_a = zlib.crc32(copy_a) & 0xFFFFFFFF
            cksum_b = zlib.crc32(copy_b) & 0xFFFFFFFF

            if cksum_a == stored_cksum:
                file_content.extend(copy_a)
            elif cksum_b == stored_cksum:
                file_content.extend(copy_b)
            else:
                # Fallback: neither matches, pick Copy A
                file_content.extend(copy_a)
                chunks_ok = False

        outpath = os.path.join(outdir, filename)
        with open(outpath, "wb") as f:
            f.write(bytes(file_content))
        status = "OK" if chunks_ok else "RECOVERED"
        print(f"Extracted: {filename} ({len(file_content)} bytes) [{status}]")


if __name__ == "__main__":
    extract(ARCHIVE, OUTDIR)
