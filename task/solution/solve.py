#!/usr/bin/env python3
"""Oracle — writes solution.py and verifies against sample vectors."""
import os, shutil, subprocess

def main():
    os.makedirs("/app/output", exist_ok=True)
    src = "/solution/solution.py"
    dst = "/app/output/solution.py"
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)

    # Verify against sample vectors
    for i in range(1, 4):
        inpath = f"/app/data/sample{i}.in"
        expected = f"/app/data/sample{i}.out"
        result = subprocess.run(
            ["python3", "-c", f"import sys; sys.path.insert(0,'/app/output'); from solution import transform; import builtins; open('/dev/stdout','wb').write(transform(open('{inpath}','rb').read()))"],
            capture_output=True, text=False, timeout=10
        )
        actual = result.stdout
        expected_data = open(expected, "rb").read()
        if actual != expected_data:
            print(f"FAIL: sample{i} mismatch")
            print(f"  expected {len(expected_data)} bytes, got {len(actual)} bytes")
            raise SystemExit(1)
        print(f"PASS: sample{i}.in -> {len(actual)} bytes matches expected")

if __name__ == "__main__":
    main()
