The file /app/data/reconstruct.py is a Python 3 script that reads a pcap capture at /app/data/sample.pcap and writes an extracted HTTP response body to /app/output/payload.bin. The script works correctly on the provided sample capture but fails on captures with multiple concurrent TCP connections.

Fix /app/data/reconstruct.py to correctly extract the HTTP response body from any pcap file. The verifier will run your fixed script against a held-out pcap and check the SHA-256 hash of /app/output/payload.bin against a golden reference.

The held-out capture contains multiple TCP connections. Only one connection carries the target file — the one whose HTTP request targets /exports/quarterly-report.pdf. The script must demultiplex connections by their TCP 4-tuple (source IP, source port, destination IP, destination port) and identify the correct connection by inspecting the HTTP request line. Other connections are decoys.

The target connection has three additional complexities:

1. TCP sequence numbers may wrap past the 32-bit boundary. Use unsigned 32-bit modular arithmetic for all sequence comparisons.

2. The HTTP response uses chunked transfer-encoding. The reassembled stream must be dechunked to produce the final payload.

3. Some packets are retransmissions that carry data different from the original. When a retransmitted segment overlaps a byte range already received, keep the first-received copy of those bytes.

Copy your fixed script to /app/output/reconstruct.py. Produce /app/output/payload.bin by running your fixed script on the sample file.
