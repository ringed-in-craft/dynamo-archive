"""
Reference solution: document filing pipeline reconstruction.

Pipeline stages (in order):
  1. Encoding detection: BOM -> null-byte -> UTF-8 validity -> Latin-1 fallback
  2. Template substitution: {KEY} replaced, {{/}} escaped to literal braces
  3. Whitespace normalization: tabs->4 spaces, strip trailing, collapse blanks

Ordering: template substitution runs on raw decoded text, whitespace runs after.
This is observable from visible samples where template values contain tabs.
"""

import json
import sys

TAB_WIDTH = 4


def detect_encoding(raw_bytes):
    if raw_bytes[:2] == b'\xff\xfe':
        return 'utf-16-le'
    if raw_bytes[:2] == b'\xfe\xff':
        return 'utf-16-be'
    null_count = sum(1 for b in raw_bytes if b == 0)
    if null_count > len(raw_bytes) * 0.3:
        return 'utf-16-le'
    try:
        raw_bytes.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        return 'iso-8859-1'


def decode_file(raw_bytes):
    return raw_bytes.decode(detect_encoding(raw_bytes))


def apply_template(text, data_dict):
    result = []
    i = 0
    while i < len(text):
        if text[i] == '{':
            if i + 1 < len(text) and text[i + 1] == '{':
                result.append('{')
                i += 2
                continue
            j = text.find('}', i + 1)
            if j == -1:
                result.append(text[i])
                i += 1
                continue
            key = text[i + 1:j]
            if key and all(c.isalnum() or c in '_-' for c in key):
                result.append(str(data_dict.get(key, f'{{{key}}}')))
                i = j + 1
            else:
                result.append(text[i])
                i += 1
        elif text[i] == '}':
            if i + 1 < len(text) and text[i + 1] == '}':
                result.append('}')
                i += 2
            else:
                result.append('}')
                i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def normalize_whitespace(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        expanded = ''
        for ch in line:
            if ch == '\t':
                expanded += ' ' * (TAB_WIDTH - (len(expanded) % TAB_WIDTH))
            else:
                expanded += ch
        expanded = expanded.rstrip()
        if expanded == '':
            if result and result[-1] == '':
                continue
        result.append(expanded)
    return '\n'.join(result)


def pipeline(raw_bytes, data_dict):
    text = decode_file(raw_bytes)
    text = apply_template(text, data_dict)
    text = normalize_whitespace(text)
    return text


def solve(in_path, out_path):
    with open(in_path) as f:
        queries = [json.loads(line) for line in f if line.strip()]

    results = []
    for q in queries:
        filename = q["input"]
        data_dict = q["data"]
        raw = open(f"/app/data/inputs/{filename}", "rb").read()
        out = pipeline(raw, data_dict)
        results.append({"input": filename, "output": out})

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <queries.jsonl> <output.jsonl>", file=sys.stderr)
        sys.exit(1)
    solve(sys.argv[1], sys.argv[2])
