"""Reference analyzer: detect forged MFT birth timestamps using USN journal."""

import csv, json, os, sys


def parse_mft(mft_path):
    mft = {}
    with open(mft_path) as f:
        for row in csv.DictReader(f):
            rec = int(row["record_number"])
            seq = int(row["sequence_number"])
            mft[(rec, seq)] = {
                "path": row["path"],
                "birth_time": int(row["birth_time"])
            }
    return mft


def parse_journal(journal_path):
    journal = []
    with open(journal_path) as f:
        for row in csv.DictReader(f):
            journal.append({
                "usn": int(row["usn"]),
                "timestamp": int(row["timestamp"]),
                "record_number": int(row["record_number"]),
                "sequence_number": int(row["sequence_number"]),
                "reason": row["reason"]
            })
    return journal


def analyze(case_dir):
    mft = parse_mft(os.path.join(case_dir, "mft.csv"))
    journal = parse_journal(os.path.join(case_dir, "usn_journal.csv"))

    if not journal:
        return []

    window_start = min(e["timestamp"] for e in journal)

    # Index by full file reference
    journal_by_ref = {}
    for e in journal:
        ref = (e["record_number"], e["sequence_number"])
        journal_by_ref.setdefault(ref, []).append(e)

    tampered = []
    for (rec, seq), finfo in mft.items():
        ref = (rec, seq)
        creates = [e for e in journal_by_ref.get(ref, []) if e["reason"] == "FILE_CREATE"]

        if creates:
            create_ts = min(e["timestamp"] for e in creates)
            if finfo["birth_time"] != create_ts:
                tampered.append(finfo["path"])
        else:
            if finfo["birth_time"] >= window_start:
                tampered.append(finfo["path"])

    return sorted(tampered)


def main():
    case_dir = sys.argv[1]
    output_path = sys.argv[2]
    tampered = analyze(case_dir)
    with open(output_path, "w") as f:
        json.dump({"tampered": tampered}, f)


if __name__ == "__main__":
    main()
