#!/bin/bash
mkdir -p /app/output
python3 /solution/solve.py /app/data/queries.jsonl /app/output/transforms.jsonl
