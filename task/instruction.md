The file `/app/data/sensorlog` is a Python 3 script that reads a binary sensor log file at `/app/data/sample.slog` and writes decoded output to `/app/output/decoded.json`. The script runs without errors but has a subtle defect that causes incorrect results on some valid input files.

On the provided sample file the script produces correct output. The verifier will run your submitted script against a different `.slog` file. Fix the script so it correctly decodes any valid file.

Examine the script and the binary format it parses. Do not rely on the sample output alone to verify correctness — the defect is not visible on the sample data.

Fix `/app/data/sensorlog`, then copy your fixed version to `/app/output/sensorlog`. The verifier will run this copy. Run your fixed script to produce `/app/output/decoded.json`. Both files are graded.

Do not modify the `.slog` files. Do not create new Python scripts or data files.
