The file `/app/data/sample.slog` is a binary sensor log. `/app/data/expected_sample.json` is the correct decoded output for that sample file — produced by the system that originally generated the log.

Write a Python 3 script at `/app/sensorlog` that decodes any `.slog` file and produces correct JSON output. Your script will be invoked as `python3 /app/sensorlog /app/data/sample.slog` and must write the decoded JSON array to `/app/output/decoded.json`.

The verifier will run your script against a held-out `.slog` file and compare the output field-by-field against the expected values.

Reverse-engineer the binary format by examining the sample file and its expected output. Copy your script to `/app/output/sensorlog`. Produce `/app/output/decoded.json` by running your script on the sample file.
