"""
Verifier for reproducible release tarball task.

Tests the agent's /app/build.sh against visible examples and hidden fixtures
that exercise distinct reproducibility traps. Also runs structural probes
on tarball internals (mtimes, sort order, uid/gid, gzip header).

The expected SHA-256 values are computed at test time by a reference
implementation embedded in this file, then compared against what the
agent's build.sh produces.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# Reference integrity marker (must match /app/marker exactly)
# ═══════════════════════════════════════════════════════════════════════════════

def _integrity_marker(data: bytes) -> int:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Reference tarball builder (produces expected SHA-256 values)
# ═══════════════════════════════════════════════════════════════════════════════

import fnmatch

_EXCLUDE = [
    ".git", ".gitignore", ".gitattributes", "node_modules",
    "*.swp", "*~", ".DS_Store", "._*", "__pycache__", ".venv",
    "*.pyc", "Thumbs.db", ".idea", ".vscode", "MANIFEST.sig",
]

_CRLF_EXTS = {
    ".txt", ".md", ".cfg", ".ini", ".sh", ".py", ".toml",
    ".yaml", ".yml", ".json", ".xml", ".html", ".css", ".js", ".c", ".h",
}
_CRLF_NAMES = {"Makefile", "version.txt.in"}


def _is_excluded(rel_path: str) -> bool:
    parts = rel_path.split(os.sep)
    for pat in _EXCLUDE:
        if fnmatch.fnmatch(rel_path, pat):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return True
    return False


def _is_text(filepath: str) -> bool:
    name = os.path.basename(filepath)
    if name in _CRLF_NAMES:
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in _CRLF_EXTS:
        return True
    try:
        with open(filepath, "rb") as f:
            return b"\x00" not in f.read(1024)
    except OSError:
        return False


def _ref_build(source_dir: str, output_path: str, epoch: int) -> str:
    """Build reproducible tarball using reference algorithm. Returns SHA-256 hex."""
    staging = tempfile.mkdtemp()
    try:
        # Copy with exclusions
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [
                d for d in dirs
                if not _is_excluded(os.path.relpath(os.path.join(root, d), source_dir))
            ]
            rel_root = os.path.relpath(root, source_dir)
            dest_root = os.path.join(staging, rel_root) if rel_root != "." else staging
            os.makedirs(dest_root, exist_ok=True)
            for fname in files:
                rel = os.path.relpath(os.path.join(root, fname), source_dir)
                if _is_excluded(rel):
                    continue
                shutil.copy2(os.path.join(root, fname), os.path.join(dest_root, fname))

        # CRLF → LF (FIRST)
        for root, dirs, files in os.walk(staging):
            for fname in files:
                fpath = os.path.join(root, fname)
                if _is_text(fpath):
                    with open(fpath, "rb") as f:
                        data = f.read()
                    data = data.replace(b"\r\n", b"\n")
                    with open(fpath, "wb") as f:
                        f.write(data)

        # Template substitution
        tmpl = os.path.join(staging, "version.txt.in")
        if os.path.exists(tmpl):
            with open(tmpl) as f:
                c = f.read()
            with open(tmpl, "w") as f:
                f.write(c.replace("@EPOCH@", str(epoch)))

        # Permission normalization
        for root, dirs, files in os.walk(staging):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)
            for fname in files:
                fpath = os.path.join(root, fname)
                parts = os.path.relpath(fpath, staging).split(os.sep)
                if "bin" in parts or fname.endswith((".sh", ".bash")):
                    os.chmod(fpath, 0o755)
                else:
                    os.chmod(fpath, 0o644)

        # MANIFEST.sig
        entries = []
        for root, dirs, files in os.walk(staging):
            dirs.sort()
            for fname in sorted(files):
                if fname == "MANIFEST.sig":
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "rb") as f:
                    marker = _integrity_marker(f.read())
                archive_path = "./" + os.path.relpath(fpath, staging)
                entries.append((archive_path, marker))
        entries.sort(key=lambda x: x[0].encode("utf-8"))
        with open(os.path.join(staging, "MANIFEST.sig"), "w") as f:
            for path, marker in entries:
                f.write(f"{marker:08X} {path}\n")

        # Tarball
        env = {**os.environ, "LC_ALL": "C"}
        with open(output_path, "wb") as out:
            tp = subprocess.Popen(
                ["tar", "--sort=name", f"--mtime=@{epoch}", "--clamp-mtime",
                 "--owner=0", "--group=0", "--numeric-owner",
                 "--format=gnu", "--no-xattrs", "--no-acls", "--no-selinux",
                 "-cf", "-", "."],
                stdout=subprocess.PIPE, cwd=staging, env=env)
            assert tp.stdout is not None
            gp = subprocess.Popen(["gzip", "-n", "-9"], stdin=tp.stdout, stdout=out)
            tp.stdout.close()
            gp.communicate()
            tp.wait()

        with open(output_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _run_agent_build(build_script: str, source_dir: str, epoch: int) -> str:
    """Run the agent's build.sh and return SHA-256 of output."""
    output = tempfile.mktemp(suffix=".tar.gz")
    try:
        # Detect interpreter: check first line for shebang
        with open(build_script, "r") as f:
            first_line = f.readline()
        if first_line.startswith("#!"):
            cmd = [build_script]
        else:
            cmd = ["bash", build_script]
        cmd += ["--source", source_dir, "--output", output, "--epoch", str(epoch)]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"build.sh failed (exit {result.returncode}): {result.stderr[-500:]}")
        with open(output, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    finally:
        if os.path.exists(output):
            os.unlink(output)


# ═══════════════════════════════════════════════════════════════════════════════
# Hidden fixture generators
# ═══════════════════════════════════════════════════════════════════════════════

def _make_fixture_a(tmpdir):
    """Locale sort: Readme.md, README.md, readme.txt."""
    d = os.path.join(tmpdir, "a")
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    for name, content in [("Readme.md", "# Project\n"), ("README.md", "# PROJECT\n"),
                           ("readme.txt", "text\n"), ("src/main.py", "print('hi')\n")]:
        with open(os.path.join(d, name), "w") as f:
            f.write(content)
    return d

def _make_fixture_b(tmpdir):
    """Future mtimes (2035)."""
    d = os.path.join(tmpdir, "b")
    os.makedirs(d)
    with open(os.path.join(d, "data.txt"), "w") as f:
        f.write("future mtime test\n")
    os.utime(os.path.join(d, "data.txt"), (2065872000, 2065872000))
    return d

def _make_fixture_c(tmpdir):
    """Exclusion patterns."""
    d = os.path.join(tmpdir, "c")
    os.makedirs(os.path.join(d, ".git"))
    with open(os.path.join(d, ".git", "HEAD"), "w") as f:
        f.write("ref: refs/heads/main\n")
    with open(os.path.join(d, ".DS_Store"), "wb") as f:
        f.write(b"\x00" * 32)
    os.makedirs(os.path.join(d, "node_modules", "pkg"))
    with open(os.path.join(d, "node_modules", "pkg", "index.js"), "w") as f:
        f.write("// module\n")
    with open(os.path.join(d, "keep.txt"), "w") as f:
        f.write("keep me\n")
    return d

def _make_fixture_d(tmpdir):
    """Permission normalization."""
    d = os.path.join(tmpdir, "d")
    os.makedirs(os.path.join(d, "bin"))
    with open(os.path.join(d, "secret.key"), "w") as f:
        f.write("key\n")
    os.chmod(os.path.join(d, "secret.key"), 0o600)
    with open(os.path.join(d, "open.txt"), "w") as f:
        f.write("open\n")
    os.chmod(os.path.join(d, "open.txt"), 0o777)
    with open(os.path.join(d, "bin", "run.sh"), "w") as f:
        f.write("#!/bin/sh\necho ok\n")
    os.chmod(os.path.join(d, "bin", "run.sh"), 0o644)
    return d

def _make_fixture_e(tmpdir):
    """CRLF + template."""
    d = os.path.join(tmpdir, "e")
    os.makedirs(d)
    with open(os.path.join(d, "README.md"), "wb") as f:
        f.write(b"# Title\r\n\r\nBody\r\n")
    with open(os.path.join(d, "version.txt.in"), "w") as f:
        f.write("epoch=@EPOCH@\n")
    return d

def _make_fixture_f(tmpdir):
    """Long paths."""
    d = os.path.join(tmpdir, "f")
    deep = os.path.join(d, *["sub"] * 40)
    os.makedirs(deep)
    with open(os.path.join(deep, "deep.txt"), "w") as f:
        f.write("deep\n")
    return d

def _make_fixture_g(tmpdir):
    """xattr stripping."""
    d = os.path.join(tmpdir, "g")
    os.makedirs(d)
    with open(os.path.join(d, "xattr.txt"), "w") as f:
        f.write("xattr test\n")
    try:
        os.setxattr(os.path.join(d, "xattr.txt"), "user.test", b"val")
    except (OSError, AttributeError):
        pass
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# Test cases
# ═══════════════════════════════════════════════════════════════════════════════

BUILD_SCRIPT = "/app/build.sh"
EPOCH = 1700000000


def test_build_script_exists():
    """The agent must produce /app/build.sh as an executable script."""
    assert os.path.exists(BUILD_SCRIPT), "/app/build.sh does not exist"
    assert os.access(BUILD_SCRIPT, os.X_OK), "/app/build.sh is not executable"


def test_example_fixture():
    """build.sh on the shipped clean example must match the reference SHA-256."""
    agent_sha = _run_agent_build(BUILD_SCRIPT, "/app/data/example", EPOCH)
    ref_sha = _ref_build("/app/data/example",
                         os.path.join(tempfile.gettempdir(), "ref_example.tar.gz"),
                         EPOCH)
    assert agent_sha == ref_sha, (
        f"example SHA-256 mismatch:\n  agent: {agent_sha}\n  ref:   {ref_sha}"
    )


def test_example_dirty_fixture():
    """build.sh on the shipped dirty example must match the reference SHA-256."""
    agent_sha = _run_agent_build(BUILD_SCRIPT, "/app/data/example_dirty", EPOCH)
    ref_sha = _ref_build("/app/data/example_dirty",
                         os.path.join(tempfile.gettempdir(), "ref_dirty.tar.gz"),
                         EPOCH)
    assert agent_sha == ref_sha, (
        f"example_dirty SHA-256 mismatch:\n  agent: {agent_sha}\n  ref:   {ref_sha}"
    )


def test_hidden_fixtures():
    """All seven hidden fixtures must produce byte-identical tarballs."""
    fixtures = [
        ("a", _make_fixture_a, "locale-dependent filename sort"),
        ("b", _make_fixture_b, "future mtimes requiring clamp-mtime"),
        ("c", _make_fixture_c, "exclusion patterns"),
        ("d", _make_fixture_d, "permission normalization"),
        ("e", _make_fixture_e, "CRLF + template substitution"),
        ("f", _make_fixture_f, "long paths > 100 chars"),
        ("g", _make_fixture_g, "extended attribute stripping"),
    ]
    tmpdir = tempfile.mkdtemp()
    try:
        for name, make_fn, description in fixtures:
            src = make_fn(tmpdir)
            agent_sha = _run_agent_build(BUILD_SCRIPT, src, EPOCH)
            ref_sha = _ref_build(src, os.path.join(tmpdir, f"ref_{name}.tar.gz"), EPOCH)
            assert agent_sha == ref_sha, (
                f"Fixture {name} ({description}) SHA-256 mismatch:\n"
                f"  agent: {agent_sha}\n  ref:   {ref_sha}"
            )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_structural_probes():
    """Verify tarball internal properties on the example output."""
    output = tempfile.mktemp(suffix=".tar.gz")
    try:
        # Detect interpreter
        with open(BUILD_SCRIPT, "r") as f:
            first_line = f.readline()
        if first_line.startswith("#!"):
            cmd = [BUILD_SCRIPT]
        else:
            cmd = ["bash", BUILD_SCRIPT]
        cmd += ["--source", "/app/data/example", "--output", output, "--epoch", str(EPOCH)]
        subprocess.run(
            cmd, capture_output=True, check=True, timeout=120,
        )

        # Decompress and list
        listing = subprocess.run(
            ["tar", "-tvf", output, "--numeric-owner"],
            capture_output=True, text=True,
        ).stdout

        lines = [l for l in listing.split("\n") if l.strip()]

        # Check all mtimes equal the epoch
        for line in lines:
            parts = line.split()
            if len(parts) >= 6 and parts[0].startswith("-"):
                mtime_str = " ".join(parts[3:5])
                assert str(EPOCH) in mtime_str or "1970" not in mtime_str, (
                    f"Unexpected mtime in entry: {line}"
                )

        # Check uid/gid are 0
        for line in lines:
            assert " root/root " in line or " 0/0 " in line, (
                f"Non-zero uid/gid in entry: {line}"
            )

        # Check entries are sorted (C locale)
        tar_list = subprocess.run(
            ["tar", "-tf", output], capture_output=True, text=True
        ).stdout.strip().split("\n")
        tar_list_sorted = sorted(tar_list, key=lambda x: x.encode("utf-8"))
        assert tar_list == tar_list_sorted, (
            f"Tar entries not sorted in C locale.\n"
            f"Got:      {tar_list[:5]}\n"
            f"Expected: {tar_list_sorted[:5]}"
        )

        # Check gzip header does not contain original filename or mtime
        with open(output, "rb") as f:
            header = f.read(10)
        # gzip magic: 0x1F 0x8B
        assert header[0:2] == b"\x1f\x8b", "Not a valid gzip file"
        # Byte 3: flags. If bit 3 (0x08) is set, FNAME is present — must be 0
        assert (header[3] & 0x08) == 0, (
            "gzip header has FNAME flag set (original filename embedded)"
        )
        # Bytes 4-7: mtime. Must be zero
        assert header[4:8] == b"\x00\x00\x00\x00", (
            "gzip header has non-zero mtime"
        )

        # Check no excluded paths present
        forbidden = [".git", ".DS_Store", "._", ".swp", "__pycache__",
                     "node_modules", ".idea", ".vscode"]
        for entry in tar_list:
            entry_lower = entry.lower()
            for fb in forbidden:
                assert fb not in entry_lower, (
                    f"Forbidden path found in tarball: {entry}"
                )

        # Check MANIFEST.sig exists
        manifest_entries = [e for e in tar_list if "MANIFEST.sig" in e]
        assert len(manifest_entries) == 1, (
            f"Expected exactly 1 MANIFEST.sig entry, got {len(manifest_entries)}"
        )

    finally:
        if os.path.exists(output):
            os.unlink(output)
