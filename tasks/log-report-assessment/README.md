# dynamo/log-report

**Category:** data_processing_and_etl — text_processing · **Objective:** transform, generate · **Artifact:** text_or_log_file, generated_output_artifact

## The problem

Repair a deliberately broken Terminal-Bench 2 (Harbor) task whose only job is to parse an Apache-style access log into a small JSON summary. The domain is trivial on purpose — the exercise is diagnosing bad task authoring.

## What makes it hard

Ten candidate defects were presented and only six were real. The four decoys were plausible red herrings — a supposedly corrupted input file, an unnecessary network requirement, a broken oracle solution, and an unrealistic memory limit — so pattern-matching on 'what sounds broken' produces wrong ticks.

## How it's verified

Each of the four stated success criteria maps to exactly one pytest test, and every test carries a docstring naming the criterion it verifies. The verifier compares parsed values against known ground truth, so a stub writing `{}` fails.

## Calibration

Oracle 1.0, no-op agent 0.0, stub writing `{}` 0.0. Six real defects repaired: `artifacts` as string instead of array, unpinned base image, reference solution leaked into the agent image, gameable existence-only verifier, reward written to the wrong path with no `ctrf.json`, and an ambiguous instruction inconsistent with the verifier. This was the entry assessment.

## Commit history

3 commits in this task's repository.

- Final sweep: restructure instruction.md, add README.md
- Fix: set -e footgun in test.sh, move data to environment/data/, remove tie-break clause
- Fixed broken Terminal-Bench 2 Harbor task: log-report

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
