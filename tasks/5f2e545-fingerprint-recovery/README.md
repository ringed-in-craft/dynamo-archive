# dynamo/fingerprint-recovery

**Category:** Mathematics and Formal Reasoning — Number theory and exact arithmetic · **Objective:** implement, analyze · **Artifact:** single_script_or_program, generated_output_artifact

## The problem

A proprietary data-integrity tool from a financial settlement system survives only as 20 archived input/output pairs: short text strings and their 16-character lowercase hex digests.

## What makes it hard

The digest is not a standard hash. It has to be reverse-engineered from I/O behaviour alone, and then verified against inputs the samples never cover.

## How it's verified

Exact string equality against held-out inputs.

## Calibration

6 commits. Instruction stripped of structural hints (separability, constant count) that originally gave the form away.

## Commit history

6 commits in this task's repository.

- Fix rubric: strip structural hints (separable, 4 constants) from instruction
- Fix rubric: remove TB3 timeout line and vestigial fingerprint.py requirement
- Task submission: fingerprint algorithm recovery from I/O pairs
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
