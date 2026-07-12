#!/usr/bin/env python3
"""Generate test vectors for the xform binary and build task files.

Produces:
  - environment/data/sample1.in / sample1.out (4-byte-aligned ASCII)
  - environment/data/sample2.in / sample2.out
  - environment/data/sample3.in / sample3.out
  - tests/expected/ vectors for held-out inputs
  - tests/expected/golden.json (all held-out expected outputs)
"""
import subprocess, os, hashlib, json, random

BINARY = "./xform"
OUT_ENV = "task/environment/data"
OUT_TESTS = "task/tests/expected"

os.makedirs(OUT_ENV, exist_ok=True)
os.makedirs(OUT_TESTS, exist_ok=True)

def xform(data: bytes) -> bytes:
    p = subprocess.run([BINARY], input=data, capture_output=True)
    assert p.returncode == 0, f"Binary failed: {p.stderr}"
    return p.stdout

# --- Sample vectors: 4-byte-aligned ASCII (never triggers tail path) ---
samples = [
    ("sample1.in", b"The quick brown fox jumps over the lazy dog."),       # 44 bytes
    ("sample2.in", b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv"),  # 48 bytes
    ("sample3.in", b"Hello, World! This is a test of the xform utils."),   # 48 bytes
]

for fname, data in samples:
    out = xform(data)
    with open(os.path.join(OUT_ENV, fname), "wb") as f:
        f.write(data)
    with open(os.path.join(OUT_ENV, fname.replace(".in", ".out")), "wb") as f:
        f.write(out)
    print(f"Sample {fname}: {len(data)} bytes -> {len(out)} bytes")

# --- Held-out vectors: covering the trap surface ---
random.seed(0xDEAD)

held_out = {
    # Alignment stress (tail path — lengths 1,2,3,5,6,7,9,15)
    "len1": bytes([0x41]),
    "len2": bytes([0x41, 0x42]),
    "len3": bytes([0x41, 0x42, 0x43]),
    "len5": b"ABCDE",
    "len6": b"ABCDEF",
    "len7": b"ABCDEFG",
    "len9": b"ABCDEFGHI",
    "len15": b"ABCDEFGHIJKLMNO",
    # Byte-value stress
    "nulls": b"\x00" * 16,
    "high": b"\xFF" * 16,
    "alternating": bytes([0x00, 0xFF] * 8),
    "binary": bytes(range(256))[:64],  # 0x00..0x3F
    # Length stress (state evolution)
    "1k": bytes([i & 0xFF for i in range(1024)]),
    "4k": bytes([(i * 37 + 13) & 0xFF for i in range(4096)]),
    # Empty input
    "empty": b"",
    # Random deterministic
    "rand16": random.getrandbits(128).to_bytes(16, 'little'),
    "rand32": random.getrandbits(256).to_bytes(32, 'little'),
    "rand73": random.getrandbits(584).to_bytes(73, 'little'),
}

golden = {}
for name, data in held_out.items():
    out = xform(data)
    golden[name] = {"input_hex": data.hex(), "output_hex": out.hex()}
    print(f"Held-out {name}: {len(data)} bytes -> {len(out)} bytes")

with open(os.path.join(OUT_TESTS, "golden.json"), "w") as f:
    json.dump(golden, f, indent=2)

print(f"\nGenerated {len(samples)} sample pairs + {len(held_out)} held-out test vectors")
print(f"Held-out golden: {OUT_TESTS}/golden.json")
print(f"Sample 1 output: {xform(b'The quick brown fox jumps over the lazy dog.').hex()}")
