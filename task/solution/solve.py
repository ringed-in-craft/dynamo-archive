#!/usr/bin/env python3
"""Oracle solution — copies the fixed script and runs it."""

import os, shutil, subprocess

SOLUTION_DIR = "/solution"
OUTPUT_DIR = "/app/output"
FIXED_SRC = os.path.join(SOLUTION_DIR, "sensorlog_fixed.py")
FIXED_DST = "/app/output/sensorlog"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    shutil.copy2(FIXED_SRC, FIXED_DST)
    os.chmod(FIXED_DST, 0o755)
    result = subprocess.run(["python3", FIXED_DST], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error:", result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)


if __name__ == "__main__":
    main()
