# Reproducible Release Tarball

A Project Dynamo task in the Build Dependency and Release Management / Release Artifacts category.

## Task

The agent must produce `/app/build.sh` — a self-contained script that builds byte-reproducible `.tar.gz` release artifacts from unclean source trees, including a generated `MANIFEST.sig` integrity manifest using a custom, undocumented marker algorithm that must be reverse-engineered from I/O pairs.

## Approach

The solution requires simultaneous control over seven independent sources of nondeterminism in tar/gzip archives (sort order, mtimes, ownership, PAX headers, gzip metadata, exclusions, permissions) and methodical reverse-engineering of a proprietary 32-bit non-linear integrity marker algorithm using the provided `/app/marker` oracle.

## Environment

Ubuntu 24.04 with GNU tar, gzip, Python 3, and a statically-compiled `/app/marker` binary implementing the custom checksum algorithm.

## Verification

The verifier runs the agent's `/app/build.sh` against two visible example directories and seven hidden fixtures exercising distinct reproducibility traps. All nine must produce byte-identical SHA-256 to the reference tarballs. Structural probes confirm mtime uniformity, C-locale sort order, zero uid/gid, clean gzip headers, and correct MANIFEST.sig content.
