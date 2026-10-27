# dynamo/expr-fingerprint-recovery

**Category:** Mathematics and Formal Reasoning — Symbolic computation · **Objective:** implement, analyze · **Artifact:** single_script_or_program

## The problem

A computational algebra group's in-house CAS produced 64-bit integer signatures for polynomial expressions. Twenty archived expression/signature pairs survive; the agent must recover the signature function.

## What makes it hard

The signature is separable — a linear component combined with XOR — and all four constants are derivable by algebra from the samples, but only if the agent recognises the separability. Treating it as an opaque hash leads nowhere.

## How it's verified

Exact integer equality against held-out expressions, including terms absent from the sample set.

## Calibration

15 commits. Full redesign to a separable linear+XOR algorithm with samples extended to cover `x^0+y`, `(x+1)^2`, and `-x` so the form is discoverable but not stated.

## Commit history

15 commits in this task's repository.

- Fix: add x^0+y,(x+1)^2,-x to samples; rewrite task.toml explanations to match actual algorithm
- Complete redesign: separable linear+XOR algorithm, all 4 constants derived from samples via algebra; oracle 1.0 nop 0.0
- retrigger CI 4
- retrigger CI 3
- retrigger CI 2
- retrigger CI
- Fix solution_quality: solve.py now derives linear constants from samples via modular arithmetic; non-linear recovery strategy documented
- Fix: wide spike range (2^24-2^40), add expansion sample, fix metadata accuracy
- Fix unambiguous + solution_quality: add x^0 sample, extract fingerprint template to separate file
- Fix unambiguous: 6 large-coeff samples with 2 exercising all 3 rotation slots; fix explanation counts
- Fix rubric: include large-coeff samples so non-linear path is observable; remove TB3 timeout line; add backticks; update explanations
- Task submission: expression fingerprint recovery — reconstruct lost canonicalization + non-linear accumulator from 20 I/O pairs
- …and 3 more

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
