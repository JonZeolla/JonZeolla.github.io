#!/usr/bin/env python3
"""Offline link check for the built site: every root-relative href/src in dist/*.html must resolve to a
file in dist/. Run after `task build`. Lab pages (Sphinx) are included too. External links are covered
by lychee in pre-commit, not here.

  python3 -I scripts/check_links.py [dist]
"""
import pathlib
import re
import sys
import urllib.parse

dist = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
missing: dict[str, set[str]] = {}
checked = 0
for html in dist.rglob("*.html"):
    text = html.read_text(errors="ignore")
    for m in re.finditer(r'(?:href|src)="(/[^"#?]*)', text):
        checked += 1
        path = urllib.parse.unquote(m.group(1))
        target = dist / path.lstrip("/")
        if path.endswith("/"):
            target = target / "index.html"
        if not (target.exists() or target.with_suffix(".html").exists()):
            missing.setdefault(path, set()).add(str(html.relative_to(dist)))
print(f"checked {checked} internal references in {dist}/")
for path, pages in sorted(missing.items()):
    print(f"MISSING {path}  (from {', '.join(sorted(pages)[:3])})")
sys.exit(1 if missing else 0)
