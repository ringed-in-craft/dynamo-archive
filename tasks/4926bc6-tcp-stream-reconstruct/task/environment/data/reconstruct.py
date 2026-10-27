#!/usr/bin/env python3
"""HTTP file extractor — reads pcap, extracts response body to payload.bin.

Reads /app/data/sample.pcap and writes /app/output/payload.bin.
"""
import struct, os, socket

PCAP = "/app/data/sample.pcap"
OUTDIR = "/app/output"
OUTFILE = os.path.join(OUTDIR, "payload.bin")

# pcap global header
PCAP_GHDR = "<IHHiIII"
PCAP_PHDR = "<IIII"
ETH_HDR = 14
IP_HDR_MIN = 20

def parse_pcap(path):
    with open(path, "rb") as f:
        magic, ver_maj, ver_min, tz, sig, snaplen, linktype = \
            struct.unpack(PCAP_GHDR, f.read(24))
        assert magic in (0xa1b2c3d4, 0xd4c3b2a1), f"bad magic: {magic:#x}"
        le = (magic == 0xa1b2c3d4)
        end = "<" if le else ">"
        phdr_fmt = end + "IIII"

        payloads = []
        while True:
            hdr = f.read(16)
            if not hdr:
                break
            ts_sec, ts_usec, caplen, origlen = struct.unpack(phdr_fmt, hdr)
            pkt = f.read(caplen)
            # Skip Ethernet + IP headers
            ip_start = ETH_HDR
            if ip_start + IP_HDR_MIN > len(pkt):
                continue
            ihl = pkt[ip_start] & 0x0F
            ip_len = ihl * 4
            proto = pkt[ip_start + 9]
            if proto != 6:  # not TCP
                continue
            tcp_start = ip_start + ip_len
            data_offset = (pkt[tcp_start + 12] >> 4) * 4
            payload_start = tcp_start + data_offset
            payload = pkt[payload_start:]
            if payload:
                payloads.append(payload)

    return b"".join(payloads)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    body = parse_pcap(PCAP)
    # Strip HTTP headers — find \r\n\r\n
    idx = body.find(b"\r\n\r\n")
    if idx >= 0:
        body = body[idx + 4:]
    with open(OUTFILE, "wb") as f:
        f.write(body)
    print(f"Wrote {len(body)} bytes to {OUTFILE}")


if __name__ == "__main__":
    main()
