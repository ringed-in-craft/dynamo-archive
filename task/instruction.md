The file `/app/data/reconstruct.py` is a Python 3 script that reads a pcap capture at `/app/data/sample.pcap` and writes an extracted HTTP response body to `/app/output/payload.bin`. The script has defects that cause incorrect output on captures with multiple connections or protocol edge cases.

Fix `/app/data/reconstruct.py` to correctly extract the HTTP response body from any valid pcap. The verifier will check the SHA-256 hash of `/app/output/payload.bin` against a golden reference.

The held-out capture contains multiple TCP connections. The script must identify and extract only the correct connection's data.

The capture may include connections with complex protocol behavior. Use only the Python 3 standard library — no external network analysis tools are needed or available.

Copy your fixed script to `/app/output/reconstruct.py`. Produce `/app/output/payload.bin` by running your fixed script on the sample file.
