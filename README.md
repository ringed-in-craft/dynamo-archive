# Reporting Pipeline Fix

A Terminal-Bench 2 task: fix a broken monthly financial reporting pipeline that produces silently incorrect output due to multiple SQL grain bugs and a query-plan anti-pattern.

## Overview

The agent inherits a Python script that queries a SQLite database and writes a quarterly revenue report. The script runs without errors but produces wrong numbers due to:

1. A JOIN fan-out inflating per-order discount totals
2. Shipping costs summed at the wrong aggregation grain
3. Cancelled and refunded orders incorrectly included in revenue
4. A missing composite index causing a full table scan

## Approach

The agent must iteratively diagnose each bug by running the pipeline, writing exploratory SQL, fixing queries, and re-verifying after each change. Each fix brings the output closer to correct but never all the way — the agent must actively re-check rather than stopping at "close enough."

## Environment

Python 3.13 with SQLite3. The task image is built from the pre-approved Python slim-bookworm base. Pytest and pytest-json-ctrf are baked in for verification.

## Verification

The verifier runs the agent's fixed script against a held-out database (same schema, different seed with different data distributions) and checks:

- The report CSV matches the golden reference exactly (2 decimal places)
- EXPLAIN QUERY PLAN shows USING INDEX with no SCAN orders
- Edge cases: NULL foreign keys, zero-item orders, cancelled/refunded orders
