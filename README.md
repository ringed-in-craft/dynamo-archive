# CHNK Archive Recovery

A Terminal-Bench 2 task: fix a broken CHNK archive recovery tool.

## Overview

A legacy backup system stored files as chunked archives (CHNK format) with redundant copies per chunk. The recovery tool has two defects: it reads data sizes in wrong endianness and uses CRC32 instead of the archive's custom prime-weighted checksum. The agent must fix both to correctly recover files from corrupted archives.

## Environment

- Python 3.13 on Debian Bookworm (slim)
- Sample CHNK archive with 3 files (all copy-A intact)
- Format specification (FORMAT.md)
- Broken recover.py script

## Verification

The verifier replaces the sample archive with a held-out archive where some chunks have copy-A corrupted and copy-B intact. The agent's fixed script must use the correct checksum to select the intact copy for each chunk. Output files are verified byte-for-byte via SHA-256 against a golden reference.
