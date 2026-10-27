A forensic export from a compromised Windows host contains two artifacts in `/app/data/sample_case/`: an MFT export (`mft.csv`) listing every live file with its record number, sequence number, path, and birth timestamp, and a USN change journal export (`usn_journal.csv`) listing journal records with USN offset, timestamp, record number, sequence number, and reason flags. `/app/data/EXPORT.md` documents the columns and three facts: the journal is append-only with higher USN values strictly later in time, and the journal is bounded so the oldest records are purged and the export begins at the oldest survivor.

The host's filesystem has been tampered with — several files carry forged birth timestamps planted by an intruder to make a dropper blend into a system directory. Your task is to write an analyzer at `/app/audit.py` that detects which files have forged birth timestamps.

`/app/audit.py` must be runnable as `python3 /app/audit.py <case_dir> <output_json_path>` and must write a JSON object to `<output_json_path>` with exactly one key `"tampered"` whose value is a JSON array of absolute paths of every file with a forged birth timestamp, sorted lexicographically by Unicode code point.

The verifier runs your analyzer against `/app/data/sample_case/` and against held-out case directories with the same schema but different data, located under `/app/data/`. The sample case lets you validate your approach against a known case — the held-out cases determine your score.

Your implementation must be pure Python standard library. Do not invoke external processes or use network access.

The verifier checks the output JSON for exact set equality against the reference — same paths, same order. Every input case has exactly one correct answer. Any deviation fails.
