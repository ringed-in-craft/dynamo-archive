#!/usr/bin/env python3
"""
Hidden fixture generator for the reproducible tarball verifier.

Creates hidden test fixtures that exercise specific reproducibility traps:
  A - Locale-dependent filename sorting
  B - Future mtimes requiring clamp-mtime
  C - Exclusion patterns (.git, .DS_Store, *.swp, node_modules)
  D - Permission normalization (0600, 0777, non-exec .sh)
  E - CRLF line endings + template substitution
  F - Long paths > 100 chars
  G - Extended attributes to be stripped

Each fixture directory is populated with files and a pre-computed expected
SHA-256 of the reference tarball (computed at test-authoring time).
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


# ── Integrity marker (must match /app/marker and reference solution) ─────────

def integrity_marker(data: bytes) -> int:
    a = 0x9E3779B9
    b = 0x7F4A7C15
    for byte in data:
        a = (a + byte) & 0xFFFFFFFF
        a = (a ^ (a >> 13)) & 0xFFFFFFFF
        a = (a * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        b = (b ^ byte) & 0xFFFFFFFF
        b = ((b << 7) | (b >> 25)) & 0xFFFFFFFF
        b = (b + a) & 0xFFFFFFFF
    return (a ^ b ^ 0xA5A5A5A5) & 0xFFFFFFFF


# ── Reference build function ─────────────────────────────────────────────────

import fnmatch

EXCLUDE_PATTERNS = [
    ".git", ".gitignore", ".gitattributes", "node_modules",
    "*.swp", "*~", ".DS_Store", "._*", "__pycache__", ".venv",
    "*.pyc", "Thumbs.db", ".idea", ".vscode", "MANIFEST.sig",
]

CRLF_EXTENSIONS = {
    ".txt", ".md", ".cfg", ".ini", ".sh", ".py", ".toml",
    ".yaml", ".yml", ".json", ".xml", ".html", ".css", ".js",
    ".c", ".h",
}
CRLF_NAMES = {"Makefile", "version.txt.in"}


def is_excluded(rel_path):
    parts = rel_path.split(os.sep)
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(rel_path, pat):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return True
    return False


def is_text_file(filepath):
    name = os.path.basename(filepath)
    if name in CRLF_NAMES:
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in CRLF_EXTENSIONS:
        return True
    try:
        with open(filepath, "rb") as f:
            head = f.read(1024)
        return b"\x00" not in head
    except OSError:
        return False


def build_reference_tarball(source_dir, output_path, epoch):
    """Build a reproducible tarball using the reference algorithm directly."""
    staging = tempfile.mkdtemp()
    try:
        # Copy with exclusions
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [
                d for d in dirs
                if not is_excluded(os.path.relpath(os.path.join(root, d), source_dir))
            ]
            rel_root = os.path.relpath(root, source_dir)
            dest_root = os.path.join(staging, rel_root) if rel_root != "." else staging
            os.makedirs(dest_root, exist_ok=True)
            for fname in files:
                rel = os.path.relpath(os.path.join(root, fname), source_dir)
                if is_excluded(rel):
                    continue
                src_file = os.path.join(root, fname)
                dst_file = os.path.join(dest_root, fname)
                shutil.copy2(src_file, dst_file)

        # 1. CRLF normalization (FIRST)
        for root, dirs, files in os.walk(staging):
            for fname in files:
                fpath = os.path.join(root, fname)
                if is_text_file(fpath):
                    with open(fpath, "rb") as f:
                        data = f.read()
                    data = data.replace(b"\r\n", b"\n")
                    with open(fpath, "wb") as f:
                        f.write(data)

        # 2. Template substitution
        tmpl_path = os.path.join(staging, "version.txt.in")
        if os.path.exists(tmpl_path):
            with open(tmpl_path) as f:
                content = f.read()
            content = content.replace("@EPOCH@", str(epoch))
            with open(tmpl_path, "w") as f:
                f.write(content)

        # 3. Permission normalization
        for root, dirs, files in os.walk(staging):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)
            for fname in files:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, staging)
                parts = rel.split(os.sep)
                is_bin = "bin" in parts
                is_sh = fname.endswith(".sh") or fname.endswith(".bash")
                if is_bin or is_sh:
                    os.chmod(fpath, 0o755)
                else:
                    os.chmod(fpath, 0o644)

        # 4. Generate MANIFEST.sig
        entries = []
        for root, dirs, files in os.walk(staging):
            dirs.sort()
            for fname in sorted(files):
                if fname == "MANIFEST.sig":
                    continue
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, staging)
                with open(fpath, "rb") as f:
                    data = f.read()
                marker = integrity_marker(data)
                archive_path = "./" + rel
                entries.append((archive_path, marker))
        entries.sort(key=lambda x: x[0].encode("utf-8"))
        manifest_path = os.path.join(staging, "MANIFEST.sig")
        with open(manifest_path, "w") as f:
            for path, marker in entries:
                f.write(f"{marker:08X} {path}\n")

        # 5. Create tarball
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        tar_cmd = [
            "tar", "--sort=name", f"--mtime=@{epoch}", "--clamp-mtime",
            "--owner=0", "--group=0", "--numeric-owner",
            "--format=gnu", "--no-xattrs", "--no-acls", "--no-selinux",
            "-cf", "-", ".",
        ]
        with open(output_path, "wb") as outfile:
            tar_proc = subprocess.Popen(
                tar_cmd, stdout=subprocess.PIPE, cwd=staging, env=env
            )
            assert tar_proc.stdout is not None
            gzip_proc = subprocess.Popen(
                ["gzip", "-n", "-9"], stdin=tar_proc.stdout, stdout=outfile
            )
            tar_proc.stdout.close()
            gzip_proc.communicate()
            tar_proc.wait()

        # Compute SHA-256
        with open(output_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    finally:
        shutil.rmtree(staging, ignore_errors=True)


# ── Fixture generators ────────────────────────────────────────────────────────

def make_fixture_A(tmpdir, epoch):
    """Locale-dependent sort: Readme.md vs README.md vs readme.txt."""
    d = os.path.join(tmpdir, "fixture_a")
    os.makedirs(d, exist_ok=True)
    files = {
        "Readme.md": "# Project Readme\n",
        "README.md": "# PROJECT README\n",
        "readme.txt": "readme text file\n",
        "src/main.py": "print('hello')\n",
    }
    for name, content in files.items():
        with open(os.path.join(d, name), "w") as f:
            f.write(content)
    return build_reference_tarball(d, os.path.join(tmpdir, "a.tar.gz"), epoch)


def make_fixture_B(tmpdir, epoch):
    """Future mtimes: files with mtime in 2035 (tests --clamp-mtime)."""
    d = os.path.join(tmpdir, "fixture_b")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "future.txt"), "w") as f:
        f.write("This file was supposedly created in the future.\n")
    with open(os.path.join(d, "normal.txt"), "w") as f:
        f.write("Normal file.\n")
    # Set mtime to 2035-06-15
    future_ts = 2065872000  # 2035-06-15T00:00:00Z
    os.utime(os.path.join(d, "future.txt"), (future_ts, future_ts))
    os.utime(os.path.join(d, "normal.txt"), (future_ts, future_ts))
    return build_reference_tarball(d, os.path.join(tmpdir, "b.tar.gz"), epoch)


def make_fixture_C(tmpdir, epoch):
    """Exclusion patterns: .git, .DS_Store, *.swp, node_modules."""
    d = os.path.join(tmpdir, "fixture_c")
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, ".git"), exist_ok=True)
    with open(os.path.join(d, ".git", "HEAD"), "w") as f:
        f.write("ref: refs/heads/main\n")
    with open(os.path.join(d, ".DS_Store"), "wb") as f:
        f.write(b"\x00\x00\x00\x01Bud1\x00\x00\x00\x00")
    with open(os.path.join(d, "foo.swp"), "w") as f:
        f.write("vim swap file\n")
    os.makedirs(os.path.join(d, "node_modules", "lib"), exist_ok=True)
    with open(os.path.join(d, "node_modules", "lib", "index.js"), "w") as f:
        f.write("module.exports = {};\n")
    with open(os.path.join(d, "keep_me.txt"), "w") as f:
        f.write("This file should be included.\n")
    return build_reference_tarball(d, os.path.join(tmpdir, "c.tar.gz"), epoch)


def make_fixture_D(tmpdir, epoch):
    """Permission normalization: 0600, 0777, non-exec .sh."""
    d = os.path.join(tmpdir, "fixture_d")
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "bin"), exist_ok=True)
    with open(os.path.join(d, "secret.key"), "w") as f:
        f.write("secret-api-key-12345\n")
    os.chmod(os.path.join(d, "secret.key"), 0o600)
    with open(os.path.join(d, "public.txt"), "w") as f:
        f.write("public data\n")
    os.chmod(os.path.join(d, "public.txt"), 0o777)
    with open(os.path.join(d, "bin", "run.sh"), "w") as f:
        f.write("#!/bin/sh\necho running\n")
    os.chmod(os.path.join(d, "bin", "run.sh"), 0o644)
    return build_reference_tarball(d, os.path.join(tmpdir, "d.tar.gz"), epoch)


def make_fixture_E(tmpdir, epoch):
    """CRLF + template substitution."""
    d = os.path.join(tmpdir, "fixture_e")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "README.md"), "wb") as f:
        f.write(b"# Readme\r\n\r\nLine 2\r\nLine 3\r\n")
    with open(os.path.join(d, "version.txt.in"), "w") as f:
        f.write("Build: @EPOCH@\n")
    return build_reference_tarball(d, os.path.join(tmpdir, "e.tar.gz"), epoch)


def make_fixture_F(tmpdir, epoch):
    """Long paths > 100 chars."""
    d = os.path.join(tmpdir, "fixture_f")
    deep = os.path.join(d, "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
                        "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
                        "u", "v", "w", "x", "y", "z")
    os.makedirs(deep, exist_ok=True)
    with open(os.path.join(deep, "deep_file.txt"), "w") as f:
        f.write("This is in a deeply nested directory.\n")
    with open(os.path.join(d, "root.txt"), "w") as f:
        f.write("Root level file.\n")
    return build_reference_tarball(d, os.path.join(tmpdir, "f.tar.gz"), epoch)


def make_fixture_G(tmpdir, epoch):
    """Extended attributes to be stripped."""
    d = os.path.join(tmpdir, "fixture_g")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "attributed.txt"), "w") as f:
        f.write("File with xattrs.\n")
    # Try to set xattr; skip if not supported
    try:
        os.setxattr(os.path.join(d, "attributed.txt"), "user.test", b"some_value")
    except (OSError, AttributeError):
        pass
    return build_reference_tarball(d, os.path.join(tmpdir, "g.tar.gz"), epoch)


# ── Main: compute all expected hashes ────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    tmpdir = tempfile.mkdtemp()
    epoch = 1700000000

    try:
        results = {}
        fixtures = {
            "A": make_fixture_A, "B": make_fixture_B, "C": make_fixture_C,
            "D": make_fixture_D, "E": make_fixture_E, "F": make_fixture_F,
            "G": make_fixture_G,
        }

        for name, fn in fixtures.items():
            sha = fn(tmpdir, epoch)
            results[f"fixture_{name.lower()}"] = sha
            print(f"fixture_{name.lower()}: {sha}")

        # Also compute visible fixtures from /app/data
        # These are already pre-built; just run reference on them
        for vis_name in ["example", "example_dirty"]:
            src = f"/app/data/{vis_name}"
            if os.path.isdir(src):
                sha = build_reference_tarball(src, os.path.join(tmpdir, f"{vis_name}.tar.gz"), epoch)
                results[vis_name] = sha
                print(f"{vis_name}: {sha}")

        # Write expected hashes for the test to read
        expected_path = os.path.join(tmpdir, "expected.json")
        with open(expected_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nExpected hashes written to {expected_path}")
        print(json.dumps(results, indent=2))

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
