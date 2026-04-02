"""Shared scanner helpers for generic gateway mutation guard scripts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_PATTERN = re.compile(r"\bstate_gateway\.set_attrs?\s*\(")


def scan_generic_gateway_calls(
    root: Path,
    *,
    include_file: Callable[[Path, Path], bool],
    allowlist: set[str] | None = None,
) -> dict[str, int]:
    """Scan Python files and count generic gateway mutation usages.

    Args:
        root: Repository root directory.
        include_file: Predicate deciding whether a file should be scanned.
        allowlist: Relative POSIX paths to skip even if hits are found.

    Returns:
        Mapping of relative POSIX file path to hit count.
    """
    allow = allowlist or set()
    counts: dict[str, int] = {}

    for file_path in root.rglob("*.py"):
        if not include_file(file_path, root):
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        hits = len(_PATTERN.findall(text))
        if hits <= 0:
            continue

        rel = file_path.relative_to(root).as_posix()
        if rel in allow:
            continue
        counts[rel] = hits

    return counts


def print_scan_result(counts: dict[str, int]) -> None:
    """Print scanner output in stable, CI-friendly format."""
    total = sum(counts.values())
    print(f"TOTAL={total}")

    if total <= 0:
        return

    for rel, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        print(f"{count}\t{rel}")
