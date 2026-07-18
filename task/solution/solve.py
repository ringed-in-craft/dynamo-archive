#!/usr/bin/env python3
"""Reference solution: reproducible release tarball builder.

Usage: python3 /solution/solve.py  (called from solve.sh)
solve.sh passes --source /app/data/example --output /app/output/release.tar.gz --epoch 1700000000

This produces a deterministic tarball with MANIFEST.sig using the custom
integrity marker algorithm, matching what /app/marker produces.
"""

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ── Integrity marker algorithm (must match /app/marker exactly) ──────────────

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


# ── Exclusion patterns ───────────────────────────────────────────────────────

EXCLUDE_PATTERNS = [
    ".git", ".gitignore", ".gitattributes", "node_modules",
    "*.swp", "*~", ".DS_Store", "._*", "__pycache__", ".venv",
    "*.pyc", "Thumbs.db", ".idea", ".vscode", "MANIFEST.sig",
]


def is_excluded(rel_path: str) -> bool:
    parts = rel_path.split(os.sep)
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(rel_path, pat):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return True
    return False


# ── CRLF detection ────────────────────────────────────────────────────────────

CRLF_EXTENSIONS = {
    ".txt", ".md", ".cfg", ".ini", ".sh", ".py", ".toml",
    ".yaml", ".yml", ".json", ".xml", ".html", ".css", ".js",
    ".c", ".h",
}

CRLF_NAMES = {"Makefile", "version.txt.in"}


def is_text_file(filepath: str) -> bool:
    """Determine if a file should have CRLF normalized."""
    name = os.path.basename(filepath)
    if name in CRLF_NAMES:
        return True
    _, ext = os.path.splitext(name)
    return ext.lower() in CRLF_EXTENSIONS


def normalize_crlf(filepath: str) -> None:
    """Convert CRLF to LF in-place."""
    with open(filepath, "rb") as f:
        data = f.read()
    data = data.replace(b"\r\n", b"\n")
    with open(filepath, "wb") as f:
        f.write(data)


# ── Permission normalization ─────────────────────────────────────────────────

def normalize_permissions(staging_dir: str) -> None:
    """Set canonical permissions: 0644 files, 0755 dirs and bin/*.sh."""
    for root, dirs, files in os.walk(staging_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, staging_dir)
            parts = rel.split(os.sep)
            is_bin = "bin" in parts
            is_sh = fname.endswith(".sh") or fname.endswith(".bash")
            if is_bin or is_sh:
                os.chmod(fpath, 0o755)
            else:
                os.chmod(fpath, 0o644)
    # Also normalize the staging root itself
    os.chmod(staging_dir, 0o755)


# ── Template substitution ────────────────────────────────────────────────────

def fill_template(staging_dir: str, epoch: str) -> None:
    """Replace @EPOCH@ in version.txt.in with the epoch integer, then rename to version.txt."""
    tmpl_path = os.path.join(staging_dir, "version.txt.in")
    if not os.path.exists(tmpl_path):
        return
    with open(tmpl_path, "r") as f:
        content = f.read()
    content = content.replace("@EPOCH@", epoch)
    new_path = os.path.join(staging_dir, "version.txt")
    with open(new_path, "w") as f:
        f.write(content)
    os.unlink(tmpl_path)


# ── Generate MANIFEST.sig ────────────────────────────────────────────────────

def generate_manifest(staging_dir: str, manifest_path: str) -> None:
    """Generate MANIFEST.sig for the staging directory in C-locale sorted order."""
    entries = []
    for root, dirs, files in os.walk(staging_dir):
        dirs.sort()
        for fname in sorted(files):
            if fname == "MANIFEST.sig":
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, staging_dir)
            with open(fpath, "rb") as f:
                data = f.read()
            marker = integrity_marker(data)
            archive_path = "./" + rel
            entries.append((archive_path, marker))

    # Sort in C locale (byte order)
    entries.sort(key=lambda x: x[0].encode("utf-8"))

    with open(manifest_path, "w") as f:
        for path, marker in entries:
            f.write(f"{marker:08X} {path}\n")


# ── Copy source to staging with exclusions ───────────────────────────────────

def copy_source(src_dir: str, staging_dir: str) -> None:
    """Copy source tree to staging, excluding forbidden files."""
    for root, dirs, files in os.walk(src_dir):
        # Filter directories
        dirs[:] = [
            d for d in dirs
            if not is_excluded(os.path.relpath(os.path.join(root, d), src_dir))
        ]
        # Compute relative root for the staging destination
        rel_root = os.path.relpath(root, src_dir)
        dest_root = os.path.join(staging_dir, rel_root) if rel_root != "." else staging_dir
        os.makedirs(dest_root, exist_ok=True)

        for fname in files:
            rel = os.path.relpath(os.path.join(root, fname), src_dir)
            if is_excluded(rel):
                continue
            src_file = os.path.join(root, fname)
            dst_file = os.path.join(dest_root, fname)
            shutil.copy2(src_file, dst_file)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--epoch", required=True)
    args = parser.parse_args()

    staging = tempfile.mkdtemp()

    try:
        # 1. Copy with exclusions
        copy_source(args.source, staging)

        # 2. CRLF → LF normalization (must run FIRST)
        for root, dirs, files in os.walk(staging):
            for fname in files:
                fpath = os.path.join(root, fname)
                if is_text_file(fpath):
                    normalize_crlf(fpath)

        # 3. Template substitution (after CRLF)
        fill_template(staging, args.epoch)

        # 4. Permission normalization (after template)
        normalize_permissions(staging)

        # 5. Generate MANIFEST.sig
        manifest_path = os.path.join(staging, "MANIFEST.sig")
        generate_manifest(staging, manifest_path)

        # 6. Create tarball with deterministic flags
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        tar_cmd = [
            "tar",
            "--sort=name",
            f"--mtime=@{args.epoch}",
            "--clamp-mtime",
            "--owner=0", "--group=0", "--numeric-owner",
            "--format=gnu",
            "--no-xattrs", "--no-acls", "--no-selinux",
            "-cf", "-", ".",
        ]
        gzip_cmd = ["gzip", "-n", "-9"]

        with open(args.output, "wb") as outfile:
            tar_proc = subprocess.Popen(
                tar_cmd, stdout=subprocess.PIPE, cwd=staging, env=env
            )
            assert tar_proc.stdout is not None
            gzip_proc = subprocess.Popen(
                gzip_cmd, stdin=tar_proc.stdout, stdout=outfile
            )
            tar_proc.stdout.close()
            gzip_proc.communicate()
            if tar_proc.wait() != 0:
                sys.exit(1)
            if gzip_proc.returncode != 0:
                sys.exit(1)

    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    main()
