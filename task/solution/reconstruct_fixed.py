#!/usr/bin/env python3
"""HTTP file extractor — FIXED: demux by 4-tuple, identify target connection,
handle seq wraparound, first-received-wins, and chunked transfer-encoding."""

import struct, os, socket, hashlib

PCAP = "/app/data/sample.pcap"
OUTDIR = "/app/output"
OUTFILE = os.path.join(OUTDIR, "payload.bin")
M32 = 0xFFFFFFFF

# pcap format
PCAP_GHDR_FMT = "<IHHiIII"
PCAP_PHDR_FMT = "<IIII"


def seq_lt(a, b):
    """Unsigned 32-bit less-than with wraparound awareness."""
    return ((a - b) & M32) > (M32 // 2)


def seq_after(a, b):
    """True if sequence a is after b (wraparound-aware)."""
    if a == b:
        return False
    return not seq_lt(a, b)


def dechunk(data):
    """Decode HTTP chunked transfer-encoding. Returns body bytes."""
    body = b""
    while True:
        crlf = data.find(b"\r\n")
        if crlf < 0:
            break
        size = int(data[:crlf], 16)
        if size == 0:
            return body
        body += data[crlf + 2:crlf + 2 + size]
        data = data[crlf + 2 + size + 2:]  # skip CRLF after chunk
    return body


def parse_pcap(path):
    with open(path, "rb") as f:
        magic, vmaj, vmin, tz, sig, snaplen, lt = struct.unpack(PCAP_GHDR_FMT, f.read(24))
        le = (magic == 0xa1b2c3d4)
        end = "<" if le else ">"

        # streams: key=(src_ip,src_port,dst_ip,dst_port) -> {buf, next_seq, http_req}
        streams = {}

        while True:
            hdr = f.read(16)
            if not hdr:
                break
            ts_sec, ts_usec, caplen, origlen = struct.unpack(end + "IIII", hdr)
            pkt = f.read(caplen)
            if len(pkt) < 34:
                continue
            proto = pkt[23]
            if proto != 6:
                continue
            src_ip = socket.inet_ntoa(pkt[26:30])
            dst_ip = socket.inet_ntoa(pkt[30:34])
            ihl = (pkt[14] & 0x0F) * 4
            tcp_off = 14 + ihl
            src_port = struct.unpack("!H", pkt[tcp_off:tcp_off+2])[0]
            dst_port = struct.unpack("!H", pkt[tcp_off+2:tcp_off+4])[0]
            seq = struct.unpack("!I", pkt[tcp_off+4:tcp_off+8])[0]
            doff = ((pkt[tcp_off+12] >> 4) * 4)
            payload = pkt[tcp_off+doff:]
            flags = pkt[tcp_off+13]

            # Determine direction for 4-tuple key
            if dst_port == 80:
                key = (src_ip, src_port, dst_ip, dst_port)
            else:
                key = (dst_ip, dst_port, src_ip, src_port)

            if key not in streams:
                streams[key] = {"buf": b"", "next_seq": None, "http_req": None}

            s = streams[key]
            if not payload:
                continue
            plen = len(payload)

            if s["next_seq"] is None:
                s["next_seq"] = (seq + plen) & M32
                s["buf"] += payload
                continue

            # Compute overlap
            seq_end = (seq + plen) & M32
            if seq_after(seq, s["next_seq"]):
                # Gap — still accept (store for now)
                s["buf"] += payload
                s["next_seq"] = seq_end
                continue

            # Overlap: only keep new data after next_seq
            overlap = 0
            if not seq_after(seq, s["next_seq"]) and seq_after(seq_end, s["next_seq"]):
                overlap = (s["next_seq"] - seq) & M32
            if overlap < plen:
                s["buf"] += payload[overlap:]
                s["next_seq"] = seq_end

    # Identify target connection
    target_body = None
    for key, s in streams.items():
        idx = s["buf"].find(b"GET ")
        if idx >= 0:
            end = s["buf"].find(b"\r\n", idx)
            if end >= 0:
                req_line = s["buf"][idx:end].decode(errors="ignore")
                if "/exports/quarterly-report.pdf" in req_line:
                    # Found target. Extract body after HTTP headers.
                    body_start = s["buf"].find(b"\r\n\r\n")
                    if body_start >= 0:
                        # Skip past both request AND response headers
                        # First CRLFCRLF = end of request, second = end of response headers
                        second = s["buf"].find(b"\r\n\r\n", body_start + 4)
                        if second >= 0:
                            raw = s["buf"][second + 4:]
                        # Check for chunked encoding in response headers
                        resp_hdrs = s["buf"][body_start + 4:second].decode(errors="ignore").lower()
                        target_body = dechunk(raw) if "chunked" in resp_hdrs else raw
                    break

    return target_body if target_body else b""


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    body = parse_pcap(PCAP)
    with open(OUTFILE, "wb") as f:
        f.write(body)
    print(f"Wrote {len(body)} bytes, SHA256: {hashlib.sha256(body).hexdigest()}")


if __name__ == "__main__":
    main()
