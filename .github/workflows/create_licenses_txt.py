#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a single licenses_py.txt containing name / version / full license text
for installed distributions (using importlib.metadata).

Usage:
    python create_licenses_txt.py [--output LICENSES_FILE] [--skip names]

Default output: licenses_py.txt (UTF-8)

This tries multiple strategies to find full license text:
 - METADATA "License-File:" header
 - common filenames next to the distribution (LICENSE*, COPYING*, etc.)
 - recursive search (first match)
 - fall back to METADATA "License:" or classifiers

Designed to run on Python 3.8+ (we use `from importlib import metadata`).
"""

from importlib import metadata
import pathlib
import argparse
import sys
import re
from typing import Optional, Iterable

COMMON_LICENSE_NAMES = (
    "license",
    "license.txt",
    "license.md",
    "copying",
    "copying.txt",
    "licence",
    "license.rst",
    "license.markdown",
)

def read_metadata_text(dist) -> Optional[str]:
    """Return the raw METADATA text if available, otherwise None."""
    try:
        return dist.read_text("METADATA")
    except Exception:
        # Some distribution objects may not implement read_text or file absent
        return None


def extract_license_file_from_metadata(meta_text: str) -> Optional[str]:
    """Look for a 'License-File:' header in METADATA and return filename if present."""
    if not meta_text:
        return None
    m = re.search(r'^License-File:\s*(.+)$', meta_text, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def find_license_path_near(dist) -> Optional[pathlib.Path]:
    """Try several heuristics to find a license-like file for the distribution.

    Returns first matching Path or None.
    """
    try:
        base = pathlib.Path(dist.locate_file("")).resolve()
    except Exception:
        return None

    # candidate directories to check (base and its parent)
    candidates_dirs = [base]
    if base.parent != base:
        candidates_dirs.append(base.parent)

    # 1) direct filename matches in candidate directories
    for d in candidates_dirs:
        if not d.exists():
            continue
        try:
            for p in d.iterdir():
                if not p.is_file():
                    continue
                name = p.name.lower()
                if name in COMMON_LICENSE_NAMES or name.startswith("license") or name.startswith("copying") or name.startswith("licence"):
                    return p
        except PermissionError:
            pass

    # 2) look for common files in dist-info / .egg-info directories
    try:
        # dist.locate_file("") might point to the package root or to the dist-info directory;
        # check siblings and children too
        search_roots = set(candidates_dirs)
        for r in list(search_roots):
            if r.parent != r:
                search_roots.add(r.parent)
    except Exception:
        search_roots = candidates_dirs

    # 3) limited recursive search (first hit) to avoid excessive work
    for root in search_roots:
        if not root.exists():
            continue
        try:
            # limit depth by stopping after some number of checked files
            checked = 0
            max_checks = 1000
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                checked += 1
                name = p.name.lower()
                if name.startswith("license") or name.startswith("copying") or name.startswith("licence"):
                    return p
                if checked >= max_checks:
                    break
        except PermissionError:
            pass

    return None


def get_license_text_for_dist(dist, fallback: Optional[str] = None) -> str:
    """Return the best-effort full license text for a distribution.

    If no text is found, return a short fallback string (from METADATA License or fallback).
    """
    # 1) Try METADATA -> License-File
    meta_text = read_metadata_text(dist)
    if meta_text:
        lf = extract_license_file_from_metadata(meta_text)
        if lf:
            try:
                p = pathlib.Path(dist.locate_file(lf))
                if p.exists():
                    return p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                # ignore and continue
                pass

    # 2) Try to find LICENSE/COPYING files near the distribution
    p = find_license_path_near(dist)
    if p is not None:
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # 3) If no file found, try METADATA License: field
    if meta_text:
        m = re.search(r'^License:\s*(.+)$', meta_text, flags=re.MULTILINE | re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # 4) Try classifiers for license
    try:
        classifiers = dist.metadata.get_all("Classifier") if hasattr(dist.metadata, "get_all") else None
        if classifiers:
            license_cls = [c for c in classifiers if c.startswith("License ::")]
            if license_cls:
                return "; ".join(license_cls)
    except Exception:
        pass

    # 5) fallback to provided fallback value (e.g. license_dict) or unknown
    return fallback or dist.metadata.get("License") or "License file not found"


def get_python_license_text() -> str:
    """Attempt to read the interpreter's LICENSE file (best-effort).

    Tries several likely locations (sys.base_prefix, sys.exec_prefix, sys.prefix).
    If no file is found, returns a short fallback string containing sys.version.
    """
    candidates = []
    try:
        bp = pathlib.Path(sys.base_prefix)
        candidates.extend([
            bp / 'LICENSE.txt',
            bp / 'LICENSE',
            bp / 'LICENSE.rst',
            bp / 'LICENSE.md',
        ])
    except Exception:
        pass
    try:
        ep = pathlib.Path(sys.exec_prefix)
        candidates.extend([
            ep / 'LICENSE.txt',
            ep / 'LICENSE',
        ])
    except Exception:
        pass
    try:
        pp = pathlib.Path(sys.prefix)
        candidates.extend([
            pp / 'LICENSE.txt',
            pp / 'LICENSE',
        ])
    except Exception:
        pass

    # unique while preserving order
    seen = set()
    uniq_candidates = []
    for p in candidates:
        try:
            sp = p.resolve()
        except Exception:
            sp = p
        if str(sp) in seen:
            continue
        seen.add(str(sp))
        uniq_candidates.append(p)

    for p in uniq_candidates:
        try:
            if p.exists():
                return p.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

    # as a last resort, check executable parent
    try:
        exe_parent = pathlib.Path(sys.executable).parent
        for name in ('LICENSE.txt', 'LICENSE', 'LICENSE.rst', 'LICENSE.md'):
            p = exe_parent / name
            if p.exists():
                try:
                    return p.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    pass
    except Exception:
        pass

    # fallback: return Python version info
    return f"Python {sys.version.splitlines()[0]}\\n(No LICENSE file found in expected locations)"


def iter_dists_sorted(skip_names: Iterable[str] = ()):  # -> generator of dist
    """Yield distributions sorted by name (case-insensitive), skipping any in skip_names."""
    skip = {s.lower() for s in skip_names}
    dists = list(metadata.distributions())
    # try to get a safe name for sorting
    def get_name(d):
        try:
            n = d.metadata.get("Name") or d.metadata.get("Summary") or getattr(d, "name", None) or ""
        except Exception:
            n = ""
        return n

    dists_sorted = sorted(dists, key=lambda d: (get_name(d) or "").lower())
    for d in dists_sorted:
        name = (d.metadata.get("Name") or "").strip()
        if not name:
            # skip unnamed distributions
            continue
        if name.lower() in skip:
            continue
        yield d


def create_licenses_file(output_path: pathlib.Path, skip_names: Iterable[str] = ()): 
    output_lines = []
    
    try:
        py_license = get_python_license_text()
    except Exception as e:
        py_license = f"(failed to read Python license: {e})"

    py_block = []
    py_block.append("=" * 80)
    py_block.append(f"Python Interpreter  ({sys.version.splitlines()[0]})")
    py_block.append("-" * 80)
    py_block.append(py_license.rstrip())
    py_block.append("")
    output_lines.append("\n".join(py_block))

    for dist in iter_dists_sorted(skip_names):
        name = dist.metadata.get("Name") or ""
        version = getattr(dist, "version", "")
        try:
            license_text = get_license_text_for_dist(dist)
        except Exception as e:
            license_text = f"(failed to read license: {e})"

        block = []
        block.append("=" * 80)
        block.append(f"{name}  {version}")
        block.append("-" * 80)
        block.append(license_text.rstrip())
        block.append("")
        output_lines.append("\n".join(block))

    # write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", errors="replace") as f:
        f.write("\n".join(output_lines))


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Create a licenses_py.txt containing full license texts of installed packages.")
    p.add_argument("--output", "-o", default="licenses_py.txt", help="output filename (default: licenses_py.txt)")
    p.add_argument("--skip", "-s", default="", help="comma-separated package names to skip (e.g. pip,setuptools)")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    skip = [s.strip() for s in args.skip.split(",") if s.strip()]
    out_path = pathlib.Path(args.output)
    print(f"Scanning installed distributions...", file=sys.stderr)
    try:
        create_licenses_file(out_path, skip_names=skip)
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)
        raise
    print(f"Wrote licenses to: {out_path.resolve()}", file=sys.stderr)
