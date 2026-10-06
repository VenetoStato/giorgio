#!/usr/bin/env python3
"""Check that relative links and images in tracked Markdown files point to tracked files or directories.

Ignored: http(s)/mailto links, pure anchors, links into third_party/ and docs/fonti/ (fetched/kept locally,
git-ignored) and into generated output folders (out/, runs/). Broken links FAIL only in the files listed in
STRICT; elsewhere they are printed as warnings. Run from the repository root: python .github/scripts/check_links.py
"""
import os
import re
import subprocess
import sys
from pathlib import PurePosixPath

STRICT = {"README.md", "CONTRIBUTING.md", "docs/CUSTOMIZE.md"}
IGNORE_PREFIXES = ("third_party/", "docs/fonti/")
IGNORE_PARTS = {"out", "runs"}

LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
REF = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.M)
FENCE = re.compile(r"```.*?```", re.S)


def main() -> int:
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    tracked = set(files)
    dirs = {str(p) for f in files for p in PurePosixPath(f).parents}
    errors = warnings = 0
    for md in sorted(f for f in files if f.endswith(".md") and os.path.exists(f)):
        text = FENCE.sub("", open(md, encoding="utf-8", errors="replace").read())
        targets = LINK.findall(text) + HTML.findall(text) + REF.findall(text)
        base = PurePosixPath(md).parent
        for t in targets:
            if re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I) or t.startswith("#"):
                continue
            path = t.split("#", 1)[0].split("?", 1)[0]
            if not path:
                continue
            if path.startswith("/"):
                norm = path.lstrip("/")
            else:
                parts = []
                for p in (base / path).parts:
                    if p == "..":
                        if parts:
                            parts.pop()
                    elif p != ".":
                        parts.append(p)
                norm = "/".join(parts)
            norm = norm.rstrip("/") or "."
            if norm.startswith(IGNORE_PREFIXES) or IGNORE_PARTS & set(norm.split("/")):
                continue
            if norm in tracked or norm in dirs or norm == ".":
                continue
            if md in STRICT:
                print(f"ERROR {md}: broken link -> {t}")
                errors += 1
            else:
                print(f"warn  {md}: broken link -> {t}")
                warnings += 1
    print(f"link check: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
