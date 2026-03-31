"""Check direct app_state attribute assignments in Python source files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERN = re.compile(r"app_state\.[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)")
EXCLUDED_PARTS = {".venv", "reference", ".git"}


def should_scan(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    return not any(part in EXCLUDED_PARTS for part in path.parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-hits", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    counts: dict[str, int] = {}

    for file_path in root.rglob("*.py"):
        if not should_scan(file_path):
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
