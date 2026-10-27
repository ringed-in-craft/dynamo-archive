# dynamo/sensorlog-decoder-fix

**Category:** Security — Reverse Engineering · **Objective:** implement, analyze · **Artifact:** single_script_or_program, generated_output_artifact

## The problem

A binary sensor log miscalculates timestamps because the shipped decoder uses a running counter instead of each block's base timestamp. The agent receives one sample `.slog` file and its correct decoded output, and must write a decoder that generalises.

## What makes it hard

The sample is four contiguous blocks at monotonically increasing timestamps, so a running-counter implementation looks correct. The held-out fixture has a 4,744-second jump, an out-of-order block, and a second gap — plus a different `block_size` (128 vs. the 256 stated in the header comment the sample conveniently reinforces).

## How it's verified

The agent's script is executed and its JSON output is compared field-by-field against a pre-computed golden file held only in `tests/`. Expected output is never reachable from the agent image, and the reference decoder is never run at verify time.

## Calibration

**0/5 passed** on live model trials — five valid failures, no timeouts, no verifier errors — while the oracle scored 1.0. This is the strongest difficulty signal the benchmark permits. Achieved after the pass@2 analysis revealed every agent had hardcoded `block_size` from the sample rather than parsing it.

## Commit history

25 commits in this task's repository.

- Retrigger CI
- Retrigger CI
- Retrigger CI
- Retrigger CI 2
- Retrigger CI
- Fix deep review items: float precision, invocation path, slogdec ghosts, block_size docs, test_output_exists dependency
- Make held-out use block_size=128 — agents that hardcode 256 will fail
- Fix solution_explanation and verification_explanation — no binary exists
- Eliminate binary — agent gets sample input+output only, must reconstruct format from examples
- Fix: remove binary before agent runs, update verification explanation to match
- Fix anti-cheat: pre-compute golden output, no binary execution at verify time
- Fix anti-cheat: remove reference binary before running agent script; add docstrings to all tests
- …and 13 more

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
