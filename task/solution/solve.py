#!/usr/bin/env python3
"""Oracle — copies the fixed recover script and runs it."""
import os, shutil, subprocess

def main():
    os.makedirs("/app/output", exist_ok=True)
    src = "/solution/recover_fixed.py"
    dst = "/app/output/recover.py"
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)
    result = subprocess.run(["python3", dst], capture_output=True, text=True)
    if result.returncode != 0:
        print("stderr:", result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)

if __name__ == "__main__":
    main()
