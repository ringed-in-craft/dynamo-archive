#!/usr/bin/env python3
"""Oracle solution — writes correct Python decoder and runs it."""

import os, shutil, subprocess

SOLUTION_DIR = "/solution"
OUTPUT_DIR = "/app/output"

DECODER_SRC = '''#!/usr/bin/env python3
"""Sensor log decoder — reverse-engineered from slogdec."""
import struct, json, sys, os

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/app/data/sample.slog"
OUTPUT = os.path.join("/app/output", "decoded.json")

with open(INPUT, "rb") as f:
    assert f.read(4) == b"SLOG"
    block_size = struct.unpack("<H", f.read(2))[0]
    records = []
    while True:
        hdr = f.read(4)
        if not hdr: break
        base = struct.unpack("<I", hdr)[0]
        for _ in range(block_size):
            rec = f.read(6)
            if not rec: break
            off, sid = rec[0], rec[1]
            val = struct.unpack("<f", rec[2:6])[0]
            records.append({"timestamp": base + off, "sensor_id": sid, "value": round(val, 6)})

os.makedirs("/app/output", exist_ok=True)
with open(OUTPUT, "w") as f:
    json.dump(records, f, indent=2)
'''

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dst = os.path.join(OUTPUT_DIR, "sensorlog")
    with open(dst, "w") as f:
        f.write(DECODER_SRC)
    os.chmod(dst, 0o755)
    result = subprocess.run(["python3", dst, "/app/data/sample.slog"],
                           capture_output=True, text=True)
    if result.returncode != 0:
        print("Error:", result.stderr)
        raise SystemExit(result.returncode)

if __name__ == "__main__":
    main()
