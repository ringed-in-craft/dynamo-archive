# dynamo/log-report

Parses an Apache-style access log into a small, deterministic JSON summary report.

## Overview

The agent is given `/app/access.log`, a fixed Apache Common Log Format file, and must
produce `/app/report.json` summarizing traffic: total request count, count of distinct
client IPs, and the most frequently requested path. The task is intentionally small in
scope — the difficulty for an agent is in correct log parsing (regex extraction of the
HTTP method/path from the quoted request field, handling the trailing HTTP version) and
producing an exact-match structured output, not in algorithmic complexity.

## Approach

`solution/solve.py` streams `/app/access.log` line by line:

- increments a running total per non-blank line,
- adds the first whitespace-delimited field (client IP) to a set for uniqueness,
- extracts the request path via `"(?:GET|POST|PUT|DELETE|HEAD|PATCH) (\S+) `,
  tallied in a `Counter`,
- writes `{"total_requests": ..., "unique_ips": ..., "top_path": ...}` to
  `/app/report.json`.

`top_path` is whichever path `Counter.most_common(1)` returns; ties are broken by
first-seen order, not alphabetically — the instruction and tests are written to match
this actual behavior rather than claim an untested guarantee.

## Environment

Single image, `environment/Dockerfile`:

- `public.ecr.aws/docker/library/python:3.13-slim-bookworm`, pinned by digest
- `pytest==8.4.1` and `pytest-json-ctrf==0.3.5` baked in (pinned) — no installs at
  verify time
- Input fixture lives at `environment/data/access.log`, copied to `/app/access.log`
  at build time
- No network access needed at runtime; `allow_internet = true` per task.toml default,
  but the answer isn't retrievable online — it's specific to the bundled fixture

## Verification

`tests/test.sh` runs `pytest` against `tests/test_outputs.py` and writes `1`/`0` to
`/logs/verifier/reward.txt`, plus `ctrf.json` to the same directory. The reward write
is guarded against `set -e` short-circuiting: the pytest call is the `if` condition
itself, so both the pass and fail branches always execute and the reward file is
always written.

Each test maps to one numbered criterion in `instruction.md`:

| Criterion (`instruction.md`) | Test |
|---|---|
| 1. `total_requests` key, correct value | `test_report_total_requests` |
| 2. `unique_ips` key, correct value | `test_report_unique_ips` |
| 3. `top_path` key, correct value | `test_report_top_path` |
| 4. `access.log` not modified | `test_access_log_unchanged` |
| (structural prerequisite) | `test_report_exists`, `test_report_valid_json`, `test_report_has_required_keys` |

Ground truth for the bundled fixture (6 lines, 3 distinct IPs, `/index.html` at 3
requests vs. `/about.html` at 2) is computed independently and hardcoded in the tests,
including a SHA-256 checksum of the untouched log to catch modification.

**Calibration:**
- `harbor run -p . --agent oracle` → reward `1.0`
- `harbor run -p . --agent nop` → reward `0`
- A stub that writes `{}` to `/app/report.json` (exists, non-empty, valid JSON, but
  no required keys) also scores `0` — confirms the verifier checks real values, not
  just file presence.

## What was fixed

This task was originally handed over broken in the following ways, since repaired:

- `task.toml`: `artifacts` was a bare string with a path that didn't match what the
  solution actually wrote; now a correctly-typed array pointing at the real output path
- `environment/Dockerfile`: unpinned `python:latest` → digest-pinned allowlisted base;
  a full reference solution (`solution_hint.py`) was copied straight into the agent
  image — removed entirely
- Input fixture moved into `environment/data/`, matching the required layout
- `tests/test_outputs.py`: verifier only checked file existence/non-emptiness (a
  trivial stub would have passed) → now asserts exact computed values plus an
  unmodified-input check
- `tests/test.sh`: reward was written to the wrong path with no `ctrf.json`, and a
  `set -e` bug meant the reward file silently never got written on a failing run →
  fixed to reliably write `/logs/verifier/reward.txt` and `ctrf.json` on every path
- `instruction.md`: had no absolute paths, no schema, no numbered criteria, and was
  missing the required timeout line entirely → rewritten with all four, kept under
  the 1500-token cap, and scoped to only claim behavior the solution actually
  guarantees
