The file /app/data/sensorlog is a Python 3 script that reads a binary sensor log file at /app/data/sample.slog and writes decoded output to /app/output/decoded.json. The script runs without errors and produces output that looks correct — but its timestamps are computed incorrectly.

The .slog binary format:

- 4-byte magic: "SLOG"
- 2-byte block size (unsigned 16-bit little-endian, always 256)
- Then one or more blocks. Each block:
  - 4-byte base timestamp (unsigned 32-bit little-endian, Unix seconds)
  - Exactly block_size records. Each record: 1-byte relative offset (unsigned 8-bit) + 1-byte sensor ID (unsigned 8-bit) + 4-byte value (32-bit float, little-endian)

The absolute timestamp of a record is: block_base_timestamp + relative_offset.

The sample file /app/data/sample.slog contains 4 blocks (1,024 records) with contiguous, monotonic timestamps. The script produces correct timestamps on this file. The verifier will run your submitted script against a different .slog file where blocks are not contiguous and not monotonic.

Fix /app/data/sensorlog so that it correctly decodes any valid .slog file. Copy your fixed version to /app/output/sensorlog. The verifier will run this copy against a held-out file to verify your fix is general. Run your fixed script to produce /app/output/decoded.json — both files are graded.

Do not modify the .slog files. Do not create new Python scripts or data files; work within the existing script.
