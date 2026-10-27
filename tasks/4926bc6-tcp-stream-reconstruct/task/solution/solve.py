#!/usr/bin/env python3
"""Oracle solution — copies fixed reconstruct.py and runs it."""

import os, shutil, subprocess

SOLUTION_DIR = "/solution"
OUTPUT_DIR = "/app/output"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    src = os.path.join(SOLUTION_DIR, "reconstruct_fixed.py")
    dst = os.path.join(OUTPUT_DIR, "reconstruct.py")
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)
    result = subprocess.run(["python3", dst], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error:", result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)


if __name__ == "__main__":
    main()
