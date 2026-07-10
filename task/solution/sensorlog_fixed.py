#!/usr/bin/env python3
"""Sensor log decoder — reads .slog binary files and outputs JSON. FIXED."""

import struct, json, os

INPUT_PATH = "/app/data/sample.slog"
OUTPUT_DIR = "/app/output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "decoded.json")


def decode_slog(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b"SLOG":
            raise ValueError("Invalid magic bytes")
        block_size = struct.unpack("<H", f.read(2))[0]
        records = []
        while True:
            header = f.read(4)
            if not header:
                break
            base_timestamp = struct.unpack("<I", header)[0]
            for _ in range(block_size):
                rec = f.read(6)
                if not rec or len(rec) < 6:
                    break
                offset, sensor_id, value = struct.unpack("<BBf", rec)
                records.append({
                    "timestamp": base_timestamp + offset,
                    "sensor_id": sensor_id,
                    "value": round(value, 6),
                })
        return records


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    records = decode_slog(INPUT_PATH)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Decoded {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
