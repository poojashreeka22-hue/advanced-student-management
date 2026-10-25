"""
Safe CSV Export utility with CSV injection prevention.
"""

import csv
import io
from typing import List, Dict, Any


def sanitize_csv_cell(value: Any) -> str:
    """
    Sanitize text against Formula Injection (CSV injection).
    If a string starts with =, +, -, @, \t, or \r, prefix it with a single quote.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def generate_safe_csv(fieldnames: List[str], rows: List[Dict[str, Any]]) -> str:
    """
    Generate RFC 4180 compliant CSV string with sanitized cells.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()

    for row in rows:
        sanitized_row = {k: sanitize_csv_cell(row.get(k, "")) for k in fieldnames}
        writer.writerow(sanitized_row)

    return output.getvalue()
