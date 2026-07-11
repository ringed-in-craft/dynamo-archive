#!/usr/bin/env python3
"""Generate sample + held-out CHNK archives for the recovery task.

Archive format: CHNK v1
- Header: magic(4) + version(2) + file_count(2) + reserved(8)
- Per file: name_len(2) + name(varies) + chunk_count(2)
- Per chunk: chunk_index(2) + data_size(4) + stored_cksum(4) + copy_a(varies) + copy_b(varies)

Custom checksum: prime-weighted sum with seed + rotation
"""
import struct, os, hashlib, random

MAGIC = b"CHNK"
VERSION = 1
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19]


def custom_checksum(data: bytes) -> int:
    """Prime-weighted rolling sum with seed. NOT any standard algorithm."""
    result = 0x9E3779B9
    for i, b in enumerate(data):
        result = (result + b * PRIMES[i % 8]) & 0xFFFFFFFF
    return result


def build_archive(files: list[tuple[str, bytes]], flip_map: dict[tuple[str, int], str],
                  output_path: str):
    """Build a CHNK archive.

    files: list of (filename, content) tuples.
    flip_map: (filename, chunk_index) -> "A" or "B" indicating which copy gets a bit flip.
              If not present, copy A is correct. Exactly one copy gets a flip.
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

        # Split into chunks of 64-256 bytes
        chunks = []
        pos = 0
        while pos < len(content):
            chunk_size = min(random.randint(64, 256), len(content) - pos)
            chunks.append(content[pos:pos + chunk_size])
            pos += chunk_size
        if not chunks:
            chunks = [b""]

        buf += struct.pack("<H", len(chunks))

        for ci, chunk_data in enumerate(chunks):
            cksum = custom_checksum(chunk_data)

            # Determine which copy gets corrupted
            flip_target = flip_map.get((fname, ci), "B")  # default: corrupt B
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
            buf += struct.pack("<I", cksum)
            buf += copy_a
            buf += copy_b

    with open(output_path, "wb") as f:
        f.write(buf)


def main():
    random.seed(42)

    os.makedirs("task/environment/data", exist_ok=True)
    os.makedirs("task/tests/expected", exist_ok=True)

    # --- Sample files ---
    readme = b"CHNK Archive Recovery Tool v1.0\n\nThis archive uses a custom prime-weighted checksum.\n"
    notes = b"Meeting notes:\n- Deploy recovery pipeline by Friday\n- All chunks use redundant storage\n- Checksum algorithm is documented in FORMAT.md\n"
    data_csv = b"id,name,value\n1,alpha,100\n2,beta,200\n3,gamma,300\n4,delta,400\n5,epsilon,500\n"

    # --- Held-out files ---
    report = (b"QUARTERLY REPORT - CONFIDENTIAL\n\nRevenue: $1.2M (up 15% YoY)\n"
              b"Expenses: $0.9M (flat)\nProfit: $0.3M\n\n"
              b"Key metrics:\n- Customer churn: 2.1%\n- New signups: 1,450\n- Avg deal size: $8,200\n")
    image_desc = b"IMAGE_001: Product photo - SKU 88421\nDimensions: 1200x800\nFormat: RAW\n"
    log_data = b"2024-01-15 08:23:11 INFO Server start\n2024-01-15 08:23:12 INFO Listening on :8080\n"

    # Sample: all copy_A correct, buggy fallback (pick A) works
    build_archive(
        [("readme.txt", readme), ("notes.txt", notes), ("data.csv", data_csv)],
        {},  # default flip target = B for all
        "task/environment/data/archive.bin",
    )

    # Held-out: some chunks have copy_A corrupted (flip A instead of B)
    # Buggy fallback that picks A will fail on these
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

    # Sample file SHAs (for verify - expected output from sample)
    with open("task/tests/expected/sample_hashes.txt", "w") as f:
        for name, content in [("readme.txt", readme), ("notes.txt", notes),
                               ("data.csv", data_csv)]:
            h = hashlib.sha256(content).hexdigest()
            f.write(f"{name} {h}\n")

    print("Done. Sample: copy_A always correct. Held-out: mixed A/B flips.")
    print(f"Sample archive: task/environment/data/archive.bin")
    print(f"Held-out archive: task/tests/expected/heldout.bin")
    print(f"Golden hashes: task/tests/expected/golden_hashes.txt")


if __name__ == "__main__":
    main()
