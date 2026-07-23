#!/bin/bash
# Oracle: produce the expected output file
mkdir -p /app/output
python3 /solution/solve.py /app/data/queries.jsonl /app/output/scores.jsonl
