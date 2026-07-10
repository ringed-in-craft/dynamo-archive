The binary `/app/data/slogdec` correctly decodes `.slog` binary log files into JSON. Run it on the sample file at `/app/data/sample.slog` to see the expected output format.

Write a Python 3 script at `/app/sensorlog` that decodes any `.slog` file and produces output identical to `/app/data/slogdec`. Your script will be invoked as `python3 /app/sensorlog /app/data/sample.slog` and must write the decoded JSON array to `/app/output/decoded.json`.

The verifier will run your script against a held-out `.slog` file and compare the output byte-for-byte with the reference decoder's output.

Reverse-engineer how `/app/data/slogdec` parses the binary format by examining the binary and testing it against the sample file. Standard Linux tools (objdump, strings, strace, xxd, python3) are available.

Copy your script to `/app/output/sensorlog`. Produce `/app/output/decoded.json` by running your script on the sample file.
