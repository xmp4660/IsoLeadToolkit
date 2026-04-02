"""Check generic state gateway mutation calls in production Python files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERN = re.compile(r"\bstate_gateway\.set_attrs?\s*\(")
EXCLUDED_PARTS = {".venv", "reference", ".git"}
TARGET_ROOTS = {"application", "core", "data", "ui", "visualization"}


def should_scan(path: Path, repo_root: Path) -> bool:
    if path.suffix != ".py":
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False

    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return False

    if not rel.parts:
        return False
    if rel.parts[0] not in TARGET_ROOTS:
        return False
    if rel.as_posix() == "core/state/gateway.py":
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-hits", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    counts: dict[str, int] = {}

    for file_path in root.rglob("*.py"):
        if not should_scan(file_path, root):
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        hits = len(PATTERN.findall(text))
        if hits > 0:
            rel = file_path.relative_to(root).as_posix()
            counts[rel] = hits

    total = sum(counts.values())
    print(f"TOTAL={total}")

    if total > 0:
        for rel, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
            print(f"{count}\t{rel}")

    if args.fail_on_hits and total > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
