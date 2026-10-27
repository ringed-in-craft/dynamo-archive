# dynamo/timestomp-detector

**Category:** Security — Digital Forensics · **Objective:** implement, analyze · **Artifact:** single_script_or_program

## The problem

Given a forensic export from a compromised Windows host — an MFT CSV and a USN change journal — implement detection for timestomping by correlating the two artifact sources.

## What makes it hard

Neither artifact is conclusive alone. Detection requires understanding how `$STANDARD_INFORMATION` timestamps can be rewritten while USN journal entries preserve the real creation and change sequence.

## How it's verified

The agent's detector is run against held-out case directories and its findings compared against known ground truth.

## Calibration

4 commits. Cleanest submission-to-acceptance path in the archive.

## Commit history

4 commits in this task's repository.

- Task submission: MFT timestomp detection via USN journal correlation
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
