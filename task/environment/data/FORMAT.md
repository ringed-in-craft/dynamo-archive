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
| 6      | 4           | u32 LE | Stored checksum (of original data)   |
| 10     | data_size   | bytes  | Copy A                               |
| ...    | data_size   | bytes  | Copy B                               |

## Recovery Rules

- Each chunk stores TWO copies of the data: Copy A and Copy B.
- The stored checksum at offset 6 is computed from the ORIGINAL (correct) data using the
  archive's custom checksum algorithm.
- At least one copy in each chunk is intact (bit-for-bit identical to the original).
  The other copy may have a flipped bit introduced by the storage hardware.
- To recover: compute the custom checksum of each copy and compare to the stored value.
  Select the copy whose computed checksum matches the stored checksum.
- If both match, prefer Copy A.

## Custom Checksum

The checksum is a **prime-weighted rolling sum** computed over the data bytes.
It uses a fixed seed and a sequence of small prime numbers as per-byte weights.
The formula is NOT CRC32, Adler-32, Fletcher, or any standard checksum algorithm.
