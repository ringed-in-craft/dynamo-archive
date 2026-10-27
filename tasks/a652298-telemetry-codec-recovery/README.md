# dynamo/telemetry-codec-recovery

**Category:** Security — Reverse Engineering · **Objective:** implement, analyze · **Artifact:** single_script_or_program

## The problem

A decommissioned telemetry compression codec used by a satellite ground station survives only as 12 input/output frame pairs. The agent must reconstruct the codec and reproduce it in code.

## What makes it hard

No specification exists — the algorithm has to be derived from 12 examples through hex inspection and hypothesis testing. The original design shipped a reference binary, which is an anti-cheat violation; the task was rebuilt as data-only so no oracle is reachable at verify time.

## How it's verified

Outputs are compared against held-out frames the agent never sees, so a fitted lookup table cannot pass. A solution-purity scan blocks subprocess/ctypes tricks and ELF embedding.

## Calibration

Rebuilt from binary-based to data-only after the evaluator rejected the original structure. Oracle 1.0 and nop 0.0 confirmed on the data-only variant.

## Commit history

16 commits in this task's repository.

- retrigger CI
- Retrigger CI for data-only rebuild
- Pivot to data-only: remove xform binary, provide 12 I/O sample pairs, models reconstruct codec mathematically
- Add back minimal smuggling check: subprocess/ctypes import blocking per instruction
- Simplify purity check: only block ELF embedding, drop import scanning
- Fix anti-cheat: add solution purity scan (no subprocess/ctypes/ELF embedding)
- v3: Length-dependent transform — short path (≤16B) vs long path (>16B)
- Fix taxonomy: drop binary_executable_or_library from artifact_type
- Fix deep review: install RE tools (binutils/file/xxd), bump timeout to 2400s
- Fix solution_explanation: document CFB-style input feedback step
- v2: Input-dependent cipher (blocks keystream precomputation bypass)
- Fix static check: remove pre-committed job artifacts, update .gitignore
- …and 4 more

---

Part of the [Dynamo Task Archive](../..). Authored for Project Dynamo / Terminal-Bench 2 (Harbor).
