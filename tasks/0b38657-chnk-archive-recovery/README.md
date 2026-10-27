# dynamo/chnk-archive-recovery

**Category:** File and Media Operations — Recovery and repair · **Objective:** fix, recover_or_repair_artifact · **Artifact:** single_script_or_program, archive_or_compressed_artifact

## The problem

A Python recovery script extracts files from a corrupted chunked archive (CHNK format) and gets the chunk parsing and checksum validation wrong. A format spec ships alongside.

## What makes it hard

The first checksum was linear and therefore brute-forceable from the sample; it was replaced with a non-linear mixing function so the recovery cannot be shortcut.

## How it's verified

Byte-for-byte comparison of recovered files against the true contents, plus checksum validation on held-out chunks.

## Calibration

9 commits, including the v2 checksum hardening to close the brute-force path.

## Commit history

9 commits in this task's repository.

- Fix rubric: add data provenance, real-world audience, remove cross-task reference
- retry CI
- trigger CI rerun
- v2: Replace linear checksum with non-linear mixing function — un-brute-forceable
- Fix rubric: remove TB3 timeout line from instruction, trim artifacts to recover.py only
- CHNK archive recovery: fix broken chunk-parsing and checksum validation
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
