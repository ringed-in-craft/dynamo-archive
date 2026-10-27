# dynamo/sparse-transform-recovery

**Category:** Mathematics and Formal Reasoning — Computational Linear algebra · **Objective:** implement, analyze · **Artifact:** generated_output_artifact

## The problem

A linear algebra team lost a sparse-matrix transform used in an iterative solver. Twenty-one archived input/output pairs survive; the routine takes a dense vector and emits an encoded output vector.

## What makes it hard

The encoding is non-linear on top of the banded operator, and the sample coverage initially only exercised leading positions — so an implementation could pass while ignoring the tail entirely.

## How it's verified

Exact numeric comparison against held-out vectors, with coverage deliberately extended to position 20.

## Calibration

6 commits. QC caught the coverage gap before submission; samples were extended and non-zero held-out positions added at 10+ and 15+.

## Commit history

6 commits in this task's repository.

- QC fix: extend coverage to position 20 — zero sample to 20, non-zero held-out at 15+
- QC fix: add non-zero position 10+ samples and held-out coverage
- Task submission: sparse tridiagonal transform with non-linear encoding
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
