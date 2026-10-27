# dynamo/tcp-stream-reconstruct

**Category:** Security — Network Forensics · **Objective:** fix, analyze, implement · **Artifact:** single_script_or_program, generated_output_artifact

## The problem

A script reads a pcap and writes an extracted HTTP response body, but produces wrong output on captures with multiple TCP streams and retransmissions.

## What makes it hard

The sample capture has a single clean stream, so a naive implementation passes. Correctness requires per-stream reassembly, sequence-number ordering, and retransmission handling.

## How it's verified

Exact byte comparison of the extracted payload against held-out captures.

## Calibration

8 commits. Instruction revised to name the target resource path explicitly without revealing the reassembly approach.

## Commit history

8 commits in this task's repository.

- Bump agent timeout to 1800s — agent was still making progress at 900s
- Fix: explicitly name target resource path in instruction
- Fix: add backticks, extract solution to separate file
- Set allow_internet=true — required by benchmark
- Task submission: TCP stream reconstructor
- Seed task.toml metadata from upload CSV
- Stamp task repo name into README
- Initial commit

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
