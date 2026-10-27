The file `/app/data/sample.slog` is a binary sensor log. `/app/data/expected_sample.json` is the correct decoded output for that sample file — produced by the system that originally generated the log.

Write a Python 3 script at `/app/sensorlog` that decodes any `.slog` file and produces correct JSON output. Copy your script to `/app/output/sensorlog`. The verifier will invoke it as `python3 /app/output/sensorlog /app/data/sample.slog` and it must write the decoded JSON array to `/app/output/decoded.json`.

The verifier will run your script against a held-out `.slog` file and compare the output field-by-field against the expected values. The `value` field is a float32 decoded from the binary; round it to 6 decimal places (e.g. `round(val, 6)`) to match the reference output exactly.

Reverse-engineer the binary format by examining the sample file and its expected output. Produce `/app/output/decoded.json` by running your script on the sample file.
