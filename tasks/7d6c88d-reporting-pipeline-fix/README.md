# dynamo/reporting-pipeline-fix

**Category:** Data Querying and Databases — Query optimization · **Objective:** fix · **Artifact:** single_script_or_program, generated_output_artifact

## The problem

A Python report generator attempts to implement an authoritative written spec against a SQLite database, and gets it wrong on cases the shipped sample never exercises.

## What makes it hard

Two bugs are visible and act as lures; two hidden requirements — a discount cap and a `LEFT JOIN` where the code uses `INNER JOIN`, plus a status filter — only fail on the held-out database. Fixing the visible bugs produces a confident, wrong submission.

## How it's verified

The verifier runs the agent's script against the held-out database and compares the produced report against golden output, so partial fixes score zero.

## Calibration

Redesigned mid-flight from visible-bug to spec-based hidden-requirements, after the original design was too easy to pass on the sample alone.

## Commit history

10 commits in this task's repository.

- Redesign: spec-based hidden requirements (discount cap + LEFT JOIN) — sample hides them, held-out exposes
- Add 2 hidden bugs (status filter + INNER JOIN) - visible bugs act as lure, hidden bugs only fail on held-out DB
- Fix golden: zero-item orders contribute 0 discount/shipping, use consistent %.2f formatting
- Drop index requirement - contradicts instruction and unstated in spec
- Fix: strip bug-revealing comments, remove timeout line, move fixed script to separate file, fix fixture dependency
- Add .dockerignore for build context
- Task submission: reporting pipeline fix
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
