#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_mental_model_links.py — verify markdown link integrity for mental_model
authoritative docs.

Scans target .md files for inline links `[text](path)` (and `![alt](path)`),
resolves each relative path against the .md file's directory, and reports any
that do not exist on disk.

Skipped: http/https/mailto/tel links, pure `#anchor` links, empty targets.
For `path#anchor` style links, only the path part is verified (anchor ignored).

Exit code: 0 if all links resolve, 1 otherwise. CI-friendly.

Default scan targets:
    - CLAUDE.local.md
    - doc/SkillAI/mental_model/
    - .claude/

Override with --paths.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable

# Match inline markdown links: [text](target) and ![alt](target).
# Greedy-safe: target stops at first unescaped ')' or whitespace.
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "ftp://", "ftps://")


def find_md_files(targets: Iterable[Path], repo_root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for t in targets:
        p = (repo_root / t).resolve() if not Path(t).is_absolute() else Path(t).resolve()
        if not p.exists():
            print(f"[warn] target not found, skipping: {t}", file=sys.stderr)
            continue
        if p.is_file() and p.suffix.lower() == ".md":
            if p not in seen:
                files.append(p)
                seen.add(p)
        elif p.is_dir():
            for md in p.rglob("*.md"):
                if md not in seen:
                    files.append(md)
                    seen.add(md)
    return sorted(files)


def should_skip(target: str) -> bool:
    if not target:
        return True
    if target.startswith("#"):
        return True
    low = target.lower()
    for s in SKIP_SCHEMES:
        if low.startswith(s):
            return True
    return False


def strip_anchor(target: str) -> str:
    # path#anchor → path. Note: the FIRST '#' separates path from anchor in markdown.
    idx = target.find("#")
    if idx >= 0:
        return target[:idx]
    return target


def url_unquote(s: str) -> str:
    # Minimal unquote for common cases (%20, %23, etc.) — avoid pulling urllib for clarity.
    try:
        from urllib.parse import unquote
        return unquote(s)
    except Exception:
        return s


def check_file(md_file: Path) -> tuple[int, list[tuple[int, str, str]]]:
    """Return (total_links_checked, list of (line_no, target, raw_match)) broken."""
    base_dir = md_file.parent
    broken: list[tuple[int, str, str]] = []
    total = 0
    try:
        text = md_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = md_file.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            raw_target = m.group(1).strip()
            if should_skip(raw_target):
                continue
            total += 1
            path_part = strip_anchor(raw_target)
            path_part = url_unquote(path_part)
            if not path_part:
                # Pure anchor (already filtered) or odd case → skip silently.
                continue
            # Resolve relative to the .md file's directory.
            candidate = (base_dir / path_part).resolve()
            if not candidate.exists():
                broken.append((lineno, raw_target, m.group(0)))
    return total, broken


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check markdown link integrity for SkillAI mental_model docs."
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="Files or directories to scan (relative to --repo-root). "
             "Default: CLAUDE.local.md doc/SkillAI/mental_model/ .claude/",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root. Defaults to two levels above this script "
             "(doc/SkillAI/tools/ → repo root).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print broken links and final summary.",
    )
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    # repo_root = .../DreamRivakes2_U3DProj (script lives at doc/SkillAI/tools/)
    default_root = script_path.parent.parent.parent.parent
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_root

    if args.paths:
        targets = [Path(p) for p in args.paths]
    else:
        targets = [
            Path("CLAUDE.local.md"),
            Path("doc/SkillAI/mental_model"),
            Path(".claude"),
        ]

    md_files = find_md_files(targets, repo_root)
    if not args.quiet:
        print(f"[info] repo_root: {repo_root}")
        print(f"[info] scanning {len(md_files)} markdown file(s)")

    grand_total = 0
    grand_broken: list[tuple[Path, int, str]] = []

    for md in md_files:
        total, broken = check_file(md)
        grand_total += total
        for lineno, target, _raw in broken:
            grand_broken.append((md, lineno, target))

    # Print broken first (file:line:link), then summary.
    for md, lineno, target in grand_broken:
        try:
            rel = md.relative_to(repo_root)
        except ValueError:
            rel = md
        print(f"BROKEN  {rel}:{lineno}:{target}")

    print(f"[summary] scanned {grand_total} link(s) across {len(md_files)} file(s); "
          f"broken {len(grand_broken)}")

    return 0 if not grand_broken else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
