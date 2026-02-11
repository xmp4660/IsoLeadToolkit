import logging
logger = logging.getLogger(__name__)
"""
Collect debug output points from the codebase.

Finds print statements and logger calls that contain tags like
[DEBUG], [INFO], [WARN], [ERROR], and [FATAL].
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "reference",
    "assets",
    "locales",
}

TAG_PATTERN = re.compile(r"\[(DEBUG|INFO|WARN|ERROR|FATAL)\]")
PRINT_PATTERN = re.compile(r"\bprint\s*\(")
LOG_PATTERN = re.compile(r"\blogger\.(debug|info|warning|error|critical)\b")


def _iter_py_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def _collect_points(path: Path) -> List[Tuple[int, str, str]]:
    points: List[Tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return points

    for idx, line in enumerate(text.splitlines(), start=1):
        tag_match = TAG_PATTERN.search(line)
        if tag_match and PRINT_PATTERN.search(line):
            points.append((idx, tag_match.group(1), line.strip()))
        elif LOG_PATTERN.search(line):
            points.append((idx, "LOG", line.strip()))
    return points


def main() -> None:
    all_points: Dict[str, List[Tuple[Path, int, str]]] = {}
    for py_file in _iter_py_files(ROOT):
        for lineno, tag, line in _collect_points(py_file):
            all_points.setdefault(tag, []).append((py_file, lineno, line))

    total = sum(len(items) for items in all_points.values())
    logger.info(f"[INFO] Found {total} debug output points.")

    for tag in sorted(all_points.keys()):
        logger.info(f"\n[{tag}] {len(all_points[tag])} entries")
        for path, lineno, line in all_points[tag]:
            rel = path.relative_to(ROOT)
            logger.info(f"  - {rel}:{lineno} {line}")


if __name__ == "__main__":
    main()
