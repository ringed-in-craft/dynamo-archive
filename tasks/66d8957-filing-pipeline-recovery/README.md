# dynamo/filing-pipeline-recovery

**Category:** File and Media Operations — Text editing and manipulation · **Objective:** implement, analyze · **Artifact:** single_script_or_program, generated_output_artifact

## The problem

A document services firm lost the code for its filing-preparation pipeline, which reads raw client submissions and emits cleaned, template-filled court-filing documents. Only surviving input/output artifacts remain.

## What makes it hard

The full pipeline specification originally appeared in the instruction, which reduced it to transcription. It now requires inference from samples: normalisation order, placeholder semantics, and escaping rules all interact.

## How it's verified

Produced documents compared against golden output for held-out submissions.

## Calibration

5 commits, the main one removing the spec from the instruction and requiring inference from samples.

## Commit history

5 commits in this task's repository.

- Fix rubric: remove full pipeline spec from instruction, require inference from samples
- Task submission: document filing pipeline recovery
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
