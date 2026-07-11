The file `/app/data/reconstruct.py` is a Python 3 script that reads a pcap capture at `/app/data/sample.pcap` and writes an extracted HTTP response body to `/app/output/payload.bin`. The script has defects that cause incorrect output on captures with multiple connections or protocol edge cases.

Fix `/app/data/reconstruct.py` to extract the HTTP response body for the resource `/exports/quarterly-report.pdf` from any valid pcap. The verifier will check the SHA-256 hash of `/app/output/payload.bin` against a golden reference.

The held-out capture may contain multiple TCP connections to the same server with different HTTP requests. Only extract the response body for the connection requesting `/exports/quarterly-report.pdf`. Ignore all other connections.

The target connection may involve complex protocol behavior. Use only the Python 3 standard library.

Copy your fixed script to `/app/output/reconstruct.py`. Produce `/app/output/payload.bin` by running your fixed script on the sample file.
