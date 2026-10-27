# dynamo/mesh-score-recovery

**Category:** Mathematics and Formal Reasoning — Computational Geometry · **Objective:** implement, analyze · **Artifact:** generated_output_artifact

## The problem

A computational geometry team lost the routine that turns a triangle's three 2D vertex pairs into a 64-bit quality score used to prioritise mesh refinement. Only archived input/output pairs survive.

## What makes it hard

The scoring function mixes geometric predicates with integer quantisation, so the recovery has to be exact rather than approximate — a close formula still produces different 64-bit outputs.

## How it's verified

Exact 64-bit equality against held-out triangles. No tolerance, no partial credit.

## Calibration

16 commits. Required stripping the solution recipe out of the instruction so the agent infers the form rather than transcribing it.

## Commit history

16 commits in this task's repository.

- retrigger: pass2 infra crash
- Fix artifact_type to generated_output_artifact (not single_script_or_program)
- Fix concision: strip recipe from instruction, keep only functional spec
- retrigger CI
- Fix: specify linear combination form in instruction (QC underdetermined)
- retrigger: QC eval passed, sticky comment stale
- retrigger: proposal now matches implementation
- Fix stale verification_explanation: no more audit.py subprocess
- retrigger CI
- retrigger CI: evaluator API failure
- retrigger CI
- Fix QC: grade static output file, don't re-execute agent code at verify time
- …and 4 more

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
