#!/usr/bin/env python3
"""Tally SANS class rosters exported from Google Drive.

Input: the two zips Google Drive produces when you download the "SEC540 Classes" and
"SEC545 Classes" folders (Drive > folder > Download). Each class folder holds one or two
roster spreadsheets (In Person and/or Live Online) plus notes, eval calculators, expense
reports. Only the rosters are read; evals/expenses/feedback files are skipped by name.

Two subcommands:

  students   Count students per class (in person + live online) and print a JSON fragment
             for data/students.json, keyed by class date. Dates come from the class folder
             name (YYYY-MM) and must be matched by hand to the exact date in the
             "My Training Classes" table of docs/ref/jz-content.md (the script prints the
             folder name beside each count to make that easy).

  employers  Count distinct student employers across every roster (the "Company" /
             "Organization" column). Used once to pick logos for "Trusted by engineers at".
             Prints organization names and counts only, never student names.

Usage:
  python3 -I scripts/sans_rosters.py students  ~/Downloads/*SEC540*.zip ~/Downloads/*SEC545*.zip
  python3 -I scripts/sans_rosters.py employers ~/Downloads/*SEC540*.zip ~/Downloads/*SEC545*.zip

Roster layouts seen so far (both handled):
  * 2022-2025 exports: header row contains "Company"; one row per student.
  * 2025-2026 exports: a title block, then a header row at row 11 containing
    "Organization" / "Customer"; one row per student until a "Total Students" line.
Counting rule: rows after the header with at least two non-empty cells, stopping at
"Total Students" or the SANS confidentiality footer. Two hand-checks on 2026-10-11:
2025-06 Baltimore in person = 9, 2023-07 SANSFIRE in person = 19.

Run with `python3 -I` so nothing is imported from the download directory.
"""
import collections
import html
import re
import sys
import zipfile
from io import BytesIO

SKIP = ("Eval", "Expense", "Feedback")
HEADER = re.compile(r"^(company|organi[sz]ation|employer|first name|last name|customer|name)$", re.I)
ORG_COL = re.compile(r"company|organi[sz]ation|employer", re.I)
STOP = re.compile(r"Total Students|Confidential property", re.I)


def sheet_rows(xlsx_bytes):
    """Yield each worksheet of an .xlsx as a list of rows; each row is a list of cell strings."""
    zf = zipfile.ZipFile(BytesIO(xlsx_bytes))
    names = zf.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        ss = zf.read("xl/sharedStrings.xml").decode("utf8", "ignore")
        shared = [html.unescape("".join(re.findall(r"<t[^>]*>([^<]*)</t>", si))) for si in re.findall(r"<si>(.*?)</si>", ss, re.S)]
    for sheet in sorted(n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml", n)):
        xml = zf.read(sheet).decode("utf8", "ignore")
        rows = []
        for body in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
            cells = []
            for _ref, typ, c in re.findall(r'<c r="([A-Z]+)\d+"(?: [^>]*?t="(\w+)")?[^>]*>(.*?)</c>', body, re.S):
                v = re.search(r"<v>([^<]*)</v>", c)
                t = re.findall(r"<t[^>]*>([^<]*)</t>", c)
                if v:
                    cells.append(shared[int(v.group(1))] if typ == "s" else v.group(1))
                elif t:
                    cells.append(html.unescape("".join(t)))
            rows.append([s.strip() for s in cells if s.strip()])
        yield rows


def header_index(rows):
    return next((i for i, r in enumerate(rows) if any(HEADER.match(c) for c in r)), None)


def count_students(xlsx_bytes):
    best = 0
    for rows in sheet_rows(xlsx_bytes):
        h = header_index(rows)
        if h is None:
            continue
        n = 0
        for r in rows[h + 1:]:
            if STOP.search(" ".join(r)):
                break
            if len(r) >= 2:
                n += 1
        best = max(best, n)
    return best


def employers(xlsx_bytes):
    out = []
    for rows in sheet_rows(xlsx_bytes):
        h = header_index(rows)
        if h is None:
            continue
        hdr = rows[h]
        col = next((i for i, c in enumerate(hdr) if ORG_COL.search(c)), None)
        if col is None:
            continue
        for r in rows[h + 1:]:
            if STOP.search(" ".join(r)):
                break
            if len(r) > col and len(r) >= 2:
                out.append(r[col])
    return out


def rosters(zip_paths):
    """Yield (class_folder, roster_filename, bytes) for every roster in the zips."""
    for zp in zip_paths:
        zf = zipfile.ZipFile(zp)
        for n in zf.namelist():
            if not n.lower().endswith(".xlsx") or any(k in n for k in SKIP):
                continue
            parts = n.split("/")
            folder = parts[2] if "Prior Years" in n else parts[1]
            yield folder, parts[-1], zf.read(n)


def main(argv):
    if len(argv) < 3 or argv[1] not in ("students", "employers"):
        print(__doc__)
        return 2
    mode, zips = argv[1], argv[2:]
    if mode == "students":
        per_class = collections.OrderedDict()
        for folder, fname, data in rosters(zips):
            per_class.setdefault(folder, []).append((fname, count_students(data)))
        total = 0
        print("# per class (in person + live online); match each folder to its date in jz-content.md")
        for folder, lst in sorted(per_class.items()):
            s = sum(n for _, n in lst)
            total += s
            detail = ", ".join(f"{n} {fname}" for fname, n in lst)
            print(f"{s:4d}  {folder}    [{detail}]")
        print(f"\nTOTAL {total} students across {len(per_class)} classes")
        print('\n# students.json fragment (fill in the exact table dates):')
        for folder, lst in sorted(per_class.items()):
            print(f'  "{folder[:7]}-??": {{"students": {sum(n for _, n in lst)}, "source": "roster"}},  // {folder}')
    else:
        c = collections.Counter()
        n_students = 0
        for _folder, _fname, data in rosters(zips):
            orgs = employers(data)
            n_students += len(orgs)
            c.update(orgs)
        print(f"# {n_students} students, {len(c)} distinct employers")
        for org, k in c.most_common():
            print(f"{k:4d}  {org}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
