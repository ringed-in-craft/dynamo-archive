# CHNK Archive Format v1

## Header (16 bytes)

| Offset | Size | Type   | Description          |
|--------|------|--------|----------------------|
| 0      | 4    | bytes  | Magic: "CHNK"        |
| 4      | 2    | u16 LE | Version (always 1)   |
| 6      | 2    | u16 LE | File count           |
| 8      | 8    | bytes  | Reserved (zeros)     |

## File Entry (variable)

| Offset | Size        | Type   | Description           |
|--------|-------------|--------|-----------------------|
| 0      | 2           | u16 LE | Filename length       |
| 2      | name_len    | bytes  | Filename (ASCII)      |
| ...    | 2           | u16 LE | Chunk count           |

## Chunk Entry (per chunk, per file)

| Offset | Size        | Type   | Description                          |
|--------|-------------|--------|--------------------------------------|
| 0      | 2           | u16 LE | Chunk index (0-based within file)    |
| 2      | 4           | u32 LE | Data size (both copies same length)  |
| 6      | 4           | u32 LE | Integrity marker (of original data)  |
| 10     | data_size   | bytes  | Copy A                               |
| ...    | data_size   | bytes  | Copy B                               |

## Recovery Rules

- Each chunk stores TWO copies of the data: Copy A and Copy B.
- The integrity marker at offset 6 is computed from the ORIGINAL (correct) data using
  the archive's proprietary mixing algorithm.
- At least one copy in each chunk is intact (bit-for-bit identical to the original).
  The other copy may have a flipped bit introduced by the storage hardware.
- To recover: compute the integrity marker of each copy and compare to the stored value.
  Select the copy whose computed marker matches the stored marker.
- If both match, prefer Copy A.

## Integrity Marker

The marker is computed by a proprietary non-linear mixing function with feedback
between two internal accumulators. It is NOT CRC32, Adler-32, Fletcher, FNV,
MurmurHash, xxHash, SipHash, or any other standard checksum or hash algorithm.
The algorithm is deterministic and self-contained (no lookup tables, no external
data). The original implementation is lost; the marker values embedded in the
archive are the only surviving specification of the algorithm's behavior.
