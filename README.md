# Dynamo Task Archive

**14 Terminal-Bench 2 (Harbor) task repositories** authored end-to-end between **July 7–27, 2026** as a contributor to Project Dynamo — a fellowship programme building the second-generation benchmark for evaluating coding agents in real terminal environments.

Each repository was written from a blank scaffold to a submitted pull request: proposal under a rubric gate, `instruction.md`, a pinned reproducible Docker environment, a reference solution (`solution/solve.sh` → helper), and a pytest verifier designed so that no-op and stub submissions score 0.0 while the golden solution scores 1.0. Every task was then calibrated against live model trials (`pass@2` / `pass@5`) and iterated until frontier models failed on valid, non-timeout runs.

**14 tasks · 145 commits · zero surviving upstream repos.** The original `handshake-project-dynamo` organisation repos and the personal forks were deleted upstream; this archive is restored from working copies with full commit history preserved as git subtrees.

---

## Index

| # | Task | Category | Commits | Trap |
|---|------|----------|---------|------|
| 1 | [log-report-assessment](tasks/log-report-assessment) | Data Processing / ETL | 3 | Repair a deliberately broken Harbor task |
| 2 | [cfde464-sensorlog-decoder-fix](tasks/cfde464-sensorlog-decoder-fix) | Security — Reverse Engineering | 25 | Per-block base timestamps in a binary log format |
| 3 | [a652298-telemetry-codec-recovery](tasks/a652298-telemetry-codec-recovery) | Security — Reverse Engineering | 16 | Reconstruct a compression codec from 12 I/O pairs |
| 4 | [9e02db9-reproducible-release-tarball](tasks/9e02db9-reproducible-release-tarball) | Build & Release Management | 18 | Bit-exact release markers from 17 I/O pairs |
| 5 | [7d6c88d-reporting-pipeline-fix](tasks/7d6c88d-reporting-pipeline-fix) | Data Querying / Databases | 10 | Hidden SQL bugs that only fail on held-out data |
| 6 | [4d0b80a-mesh-score-recovery](tasks/4d0b80a-mesh-score-recovery) | Mathematics — Computational Geometry | 16 | Recover a 64-bit mesh-quality scorer |
| 7 | [e1d23a3-expr-fingerprint-recovery](tasks/e1d23a3-expr-fingerprint-recovery) | Mathematics — Symbolic Computation | 15 | Recover a 64-bit CAS expression signature |
| 8 | [0b38657-chnk-archive-recovery](tasks/0b38657-chnk-archive-recovery) | File & Media Operations | 9 | Fix chunk parsing + non-linear checksum validation |
| 9 | [4926bc6-tcp-stream-reconstruct](tasks/4926bc6-tcp-stream-reconstruct) | Security — Network Forensics | 8 | Reassemble HTTP payloads across TCP segments |
| 10 | [5f2e545-fingerprint-recovery](tasks/5f2e545-fingerprint-recovery) | Mathematics — Number Theory | 6 | 16-hex-char integrity digests from 20 I/O pairs |
| 11 | [66d8957-filing-pipeline-recovery](tasks/66d8957-filing-pipeline-recovery) | File & Media Operations | 5 | Infer a document templating pipeline from samples |
| 12 | [e35a8e7-sparse-transform-v2](tasks/e35a8e7-sparse-transform-v2) | Mathematics — Linear Algebra | 6 | Non-linear encoded sparse transform |
| 13 | [371c6d7-sparse-transform-recovery](tasks/371c6d7-sparse-transform-recovery) | Mathematics — Linear Algebra | 4 | Banded operator + numerical stability encoding |
| 14 | [176ed23-timestomp-detector](tasks/176ed23-timestomp-detector) | Security — Digital Forensics | 4 | Detect timestomping via MFT/USN journal correlation |

---

## Design principles applied

Every task in this archive follows the same authoring discipline:

- **Instruction states the goal, not the procedure.** No tool listings, no recipe, absolute paths in backticks. The agent must reason its way to an approach.
- **The sample hides the crux; the held-out data exposes it.** Pattern that consistently produced 0/5 pass@5: ship a homogeneous sample that makes a naive assumption look correct, then hold out data where that assumption breaks.
- **Verification grades outcomes, not strings.** The verifier executes the agent's artifact and compares computed values against pre-computed golden output. No keyword matching, no existence-only checks.
- **Anti-cheat by construction.** Golden answers live only in `tests/`, never inside the agent image. Reference solutions are never reachable at verify time.
- **Deterministic and reproducible.** Base images pinned by `@sha256` digest, pytest and plugins pinned, no live services, no network dependency at verify time.
- **One test per stated success criterion,** each carrying a docstring naming the criterion it verifies — no missing and no extra checks.
- **Calibrated, not assumed.** Oracle must score 1.0, a no-op agent must score 0.0, and a stub writing `{}` must score 0.0 before submission.

## The flagship result

`cfde464-sensorlog-decoder-fix` — a binary sensor-log decoder that computed timestamps from a running counter instead of each block's base timestamp. After ten hours of failures, the pass@2 analysis showed every agent had hardcoded `block_size=256` read from the header comment rather than parsed from the file. The held-out fixture was rebuilt with `block_size=128`.

Result: **0/5 passed. Five valid failures, zero timeouts, zero verifier errors** — the strongest difficulty signal the benchmark permits, with the oracle still scoring 1.0.

## Archive notes

- **Per-task READMEs** describe each task's problem, the specific trap that made it hard, how the verifier resists gaming, and the calibration result, followed by that task's real commit log.
- **Pointer CI workflows were removed.** Each task originally carried `.github/workflows/` files that delegated to a reusable workflow hosted under the (now defunct) upstream organisation, using `pull_request_target` with `secrets: inherit`. Republishing that pattern on a public repository is a supply-chain footgun if the organisation name is ever released and re-registered, so the files were stripped. They were centrally-maintained scaffolding, not authored work.
- **Two tasks share names** (`sparse-transform`, and the `fingerprint` pair) because the second was an independent rebuild of the same problem with a harder encoding. They are distinguished by their short IDs.
- **Program reference docs removed.** Each task originally carried a `references/` folder holding the programme's internal grading rubric and diversity taxonomy — material issued to contributors for consultation, not authored here and not mine to redistribute. Those folders were stripped before publication and archived locally. The tasks run without them; they were authoring aids.
- **Not recovered:** the pass@5 trial tables and human reviewer verdicts lived in pull-request comments inside the deleted organisation, so they are lost. The commit history, the reasoning behind each design decision, and the calibration outcomes recorded above survive.

## Note on scope

These are benchmark-authoring artifacts, not exploits or client work. They exist to measure where frontier coding agents break. 25 commits on the flagship task is not 25 features — a large share are CI retriggers against an evaluator that intermittently failed to post results.
