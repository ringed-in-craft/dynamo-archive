The file `/app/data/recover.py` is a Python 3 script that recovers files from a corrupted chunked
archive at `/app/data/archive.bin` using the CHNK format. The format specification is documented
in `/app/data/FORMAT.md` — read it in full. Each file is split into chunks; each chunk stores two
redundant copies. At least one copy per chunk is intact; the other may have a flipped bit. The
script validates copies against stored checksums to select the correct data and reassembles files.

The script has defects that cause incorrect file recovery on some archives. Fix
`/app/data/recover.py` to correctly recover **all files with their exact original content** from
any valid CHNK archive.

Copy your fixed script to `/app/output/recover.py`. Run it on the sample archive to produce the
extracted files under `/app/output/`.

Use only the Python 3 standard library. The custom checksum formula is NOT any standard algorithm
(not CRC32, Adler-32, Fletcher, or similar) and cannot be looked up online — it must be
reconstructed from the stored checksum values in the archive.

You have 900 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
