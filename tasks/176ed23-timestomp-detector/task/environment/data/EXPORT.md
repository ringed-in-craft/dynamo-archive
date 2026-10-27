# Forensic Export Documentation

## MFT Export (`mft.csv`)

A listing of every live file on the volume at acquisition time.

Columns:
- `record_number`: the MFT record number (integer)
- `sequence_number`: the MFT sequence number (integer)
- `path`: the absolute path on the volume (string)
- `birth_time`: the birth (creation) timestamp recorded in $STANDARD_INFORMATION (Unix epoch, integer seconds)

## USN Journal Export (`usn_journal.csv`)

The NTFS change journal (USN journal), exported as CSV. The journal is append-only:
records are written at increasing byte offsets, so higher USN values are strictly later
in time.

Columns:
- `usn`: byte offset in the journal (integer, monotonically increasing)
- `timestamp`: when the record was written (Unix epoch, integer seconds)
- `record_number`: MFT record number this change applies to (integer)
- `sequence_number`: MFT sequence number this change applies to (integer)
- `reason`: the reason code for this change. Possible values include `FILE_CREATE`, `DATA_OVERWRITE`, `RENAME_OLD_NAME`, and `CLOSE`.

The journal is bounded: the oldest records are periodically purged, so the export
begins at the oldest surviving record. Records predating the oldest survivor are
not recoverable.
