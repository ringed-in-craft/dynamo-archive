#!/bin/bash
# Reference solution: write /app/build.sh (the artifact the verifier tests).
# Harbor mounts solution/ at /solution/ and runs this script.
set -euo pipefail

# Copy the reference build script as the agent's deliverable
cp /solution/solve.py /app/build.sh
chmod +x /app/build.sh
