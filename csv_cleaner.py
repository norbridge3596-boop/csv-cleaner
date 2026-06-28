#!/usr/bin/env python3
"""csv-cleaner — Automated CSV cleaning and standardisation.

Usage:
    python3 csv-cleaner.py input.csv [output.csv]

If output is omitted, prints cleaned data to stdout.

Features:
    - Detect and standardise delimiters
    - Strip whitespace from headers and values
    - Normalise date formats
    - Handle missing values consistently
    - Remove duplicate rows
"""

import csv
import sys
import os
from pathlib import Path


def detect_delimiter(sample: str) -> str:
    """Detect the delimiter from a sample of the file."""
    counts = {',': 0, '	': 0, ';': 0, '|': 0}
    for line in sample.split('
')[:5]:
        for d in counts:
            counts[d] += line.count(d)
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ','


def normalise_date(val: str) -> str:
    """Attempt to normalise common date formats to YYYY-MM-DD."""
    val = val.strip().strip('"').strip("'")
    from datetime import datetime
    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d',
                '%d %b %Y', '%d %B %Y', '%b %d %Y', '%B %d %Y']:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return val


def clean_value(val: str) -> str:
    """Clean a single value."""
    val = val.strip()
    val = val.strip('"').strip("'")
    if val.lower() in ('', 'null', 'none', 'n/a', 'na', '-', '--'):
        return ''
    return val


def process(input_path: str, output_path: str = None):
    """Clean a CSV file and write to output."""
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        raw = f.read()

    delimiter = detect_delimiter(raw)
    reader = csv.DictReader(raw.split('
'), delimiter=delimiter)

    # Clean headers
    reader.fieldnames = [h.strip().strip('"').strip("'") for h in reader.fieldnames]

    seen = set()
    rows = []
    for row in reader:
        cleaned = {k: clean_value(v) for k, v in row.items()}
        # Skip empty rows and duplicates
        if all(v == '' for v in cleaned.values()):
            continue
        row_hash = tuple(cleaned.items())
        if row_hash in seen:
            continue
        seen.add(row_hash)
        rows.append(cleaned)

    if not rows:
        print("No data rows found.", file=sys.stderr)
        sys.exit(1)

    out = output_path or sys.stdout
    if output_path:
        out = open(output_path, 'w', newline='', encoding='utf-8')
    
    writer = csv.DictWriter(out, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    if output_path:
        out.close()
        print(f"Cleaned {len(rows)} rows to {output_path}", file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    process(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
