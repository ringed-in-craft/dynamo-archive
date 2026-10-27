# dynamo/sparse-transform-recovery

**Category:** Mathematics and Formal Reasoning — Computational Linear algebra · **Objective:** implement, analyze · **Artifact:** single_script_or_program, generated_output_artifact

## The problem

A spectral element solver's custom sparse-matrix transform — a banded linear operator followed by a numerical stability encoding — survives only as 20 archived input/output pairs.

## What makes it hard

Two composed stages must both be recovered, and the stability encoding can mask small errors in the linear stage, so a near-miss looks correct on the sample.

## How it's verified

Exact comparison on held-out vectors that exercise the band edges.

## Calibration

4 commits. The direct predecessor to the v2 non-linear variant.

## Commit history

4 commits in this task's repository.

- Task submission: sparse tridiagonal transform recovery
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
