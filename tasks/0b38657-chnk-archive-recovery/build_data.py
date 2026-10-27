#!/usr/bin/env python3
"""Generate sample + held-out CHNK archives for the recovery task.

Archive format: CHNK v1
- Header: magic(4) + version(2) + file_count(2) + reserved(8)
- Per file: name_len(2) + name(varies) + chunk_count(2)
- Per chunk: chunk_index(2) + data_size(4) + stored_marker(4) + copy_a(varies) + copy_b(varies)

Custom integrity marker: non-linear mixing function with two interacting accumulators.
NOT any standard algorithm — not CRC32, Adler-32, FNV, MurmurHash, xxHash, or SipHash.
"""
import struct, os, hashlib, random

MAGIC = b"CHNK"
VERSION = 1


def integrity_marker(data: bytes) -> int:
    """Non-linear mixing function with feedback between two accumulators.

    This is a custom algorithm — not CRC32, Adler-32, FNV, or any standard checksum.
    Models cannot brute-force it because the search space of possible non-linear
    mixing functions is astronomical.
    """
    a = 0x9E3779B9
    b = 0x7F4A7C15
    for i, byte in enumerate(data):
        # Accumulator A: byte absorption + xorshift + LCG mix
        a = (a + byte) & 0xFFFFFFFF
        a = (a ^ (a >> 13)) & 0xFFFFFFFF
        a = (a * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        # Accumulator B: byte XOR + rotation + feedback from A
        b = (b ^ byte) & 0xFFFFFFFF
        b = ((b << 7) | (b >> 25)) & 0xFFFFFFFF
        b = (b + a) & 0xFFFFFFFF
    # Combine with position-influenced final mix
    result = (a ^ b ^ 0xA5A5A5A5) & 0xFFFFFFFF
    return result


def build_archive(files: list[tuple[str, bytes]], flip_map: dict[tuple[str, int], str],
                  output_path: str):
    """Build a CHNK archive.

    files: list of (filename, content) tuples.
    flip_map: (filename, chunk_index) -> "A" or "B" indicating which copy gets a bit flip.
    """
    buf = bytearray()
    buf += MAGIC
    buf += struct.pack("<H", VERSION)
    buf += struct.pack("<H", len(files))
    buf += b"\x00" * 8

    for fname, content in files:
        name_enc = fname.encode("ascii")
        buf += struct.pack("<H", len(name_enc))
        buf += name_enc

        chunks = []
        pos = 0
        while pos < len(content):
            remaining = len(content) - pos
            chunk_size = min(random.randint(80, 280), remaining)
            chunks.append(content[pos:pos + chunk_size])
            pos += chunk_size
        if not chunks:
            chunks = [b""]

        buf += struct.pack("<H", len(chunks))

        for ci, chunk_data in enumerate(chunks):
            marker = integrity_marker(chunk_data)

            flip_target = flip_map.get((fname, ci), "B")
            corrupted = bytearray(chunk_data)
            if len(corrupted) > 0:
                bit_pos = random.randint(0, len(corrupted) * 8 - 1)
                byte_idx = bit_pos // 8
                bit_idx = bit_pos % 8
                corrupted[byte_idx] ^= (1 << bit_idx)

            if flip_target == "A":
                copy_a = bytes(corrupted)
                copy_b = chunk_data
            else:
                copy_a = chunk_data
                copy_b = bytes(corrupted)

            buf += struct.pack("<H", ci)
            buf += struct.pack("<I", len(chunk_data))
            buf += struct.pack("<I", marker)
            buf += copy_a
            buf += copy_b

    with open(output_path, "wb") as f:
        f.write(buf)


def main():
    random.seed(42)

    os.makedirs("task/environment/data", exist_ok=True)
    os.makedirs("task/tests/expected", exist_ok=True)

    readme = b"CHNK Archive Recovery Tool v1.0\n\nThis archive uses a proprietary integrity marker.\n"
    notes = b"Meeting notes:\n- Deploy recovery pipeline by Friday\n- All chunks use redundant storage\n- Marker algorithm is referenced in FORMAT.md\n"
    data_csv = b"id,name,value\n1,alpha,100\n2,beta,200\n3,gamma,300\n4,delta,400\n5,epsilon,500\n"

    report = (b"QUARTERLY REPORT - CONFIDENTIAL\n\nRevenue: $1.2M (up 15% YoY)\n"
              b"Expenses: $0.9M (flat)\nProfit: $0.3M\n\n"
              b"Key metrics:\n- Customer churn: 2.1%\n- New signups: 1,450\n- Avg deal size: $8,200\n")
    image_desc = b"IMAGE_001: Product photo - SKU 88421\nDimensions: 1200x800\nFormat: RAW\n"
    log_data = b"2024-01-15 08:23:11 INFO Server start\n2024-01-15 08:23:12 INFO Listening on :8080\n"

    # Sample: all copy_A correct, buggy fallback (pick A) works
    build_archive(
        [("readme.txt", readme), ("notes.txt", notes), ("data.csv", data_csv)],
        {},
        "task/environment/data/archive.bin",
    )

    # Held-out: some chunks have copy_A corrupted
    heldout_flips = {
        ("report.txt", 0): "A",
        ("image.log", 1): "A",
        ("server.log", 2): "A",
    }
    build_archive(
        [("report.txt", report), ("image.log", image_desc), ("server.log", log_data)],
        heldout_flips,
        "task/tests/expected/heldout.bin",
    )

    # Golden hashes for held-out files
    with open("task/tests/expected/golden_hashes.txt", "w") as f:
        for name, content in [("report.txt", report), ("image.log", image_desc),
                               ("server.log", log_data)]:
            h = hashlib.sha256(content).hexdigest()
            f.write(f"{name} {h}\n")

    print("Done. Non-linear integrity marker — not brute-forceable.")
    print(f"Sample: task/environment/data/archive.bin")
    print(f"Held-out: task/tests/expected/heldout.bin")


if __name__ == "__main__":
    main()
