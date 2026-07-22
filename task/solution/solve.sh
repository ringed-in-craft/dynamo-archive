#!/bin/bash
# Oracle: reads /app/data/queries.jsonl, produces /app/output/fingerprints.jsonl
mkdir -p /app/output
python3 /solution/solve.py /app/data/queries.jsonl /app/output/fingerprints.jsonl
