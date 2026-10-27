#!/usr/bin/env python3
"""Oracle solution — copies the fixed script and runs it to produce artifacts."""

import os
import shutil
import subprocess

SOLUTION_DIR = "/solution"
OUTPUT_DIR = "/app/output"
FIXED_SRC = os.path.join(SOLUTION_DIR, "generate_report_fixed.py")
FIXED_DST = os.path.join(OUTPUT_DIR, "generate_report.py")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copy the fixed script as an artifact
    shutil.copy2(FIXED_SRC, FIXED_DST)
    os.chmod(FIXED_DST, 0o755)

    # Run the fixed script to produce the report
    result = subprocess.run(["python3", FIXED_DST], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running fixed script:", result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)


if __name__ == "__main__":
    main()
