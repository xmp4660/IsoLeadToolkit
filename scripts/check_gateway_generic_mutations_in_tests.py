"""Check generic state gateway mutation calls in tests against an allowlist."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERN = re.compile(r"\bstate_gateway\.set_attrs?\s*\(")
EXCLUDED_PARTS = {".venv", "reference", ".git", "__pycache__"}
ALLOWED = {
    "tests/test_gateway_set_attr_compatibility.py",
}


def should_scan(path: Path, repo_root: Path) -> bool:
    if path.suffix != ".py":
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False

    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return False

    return rel.parts and rel.parts[0] == "tests"


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
        if hits <= 0:
            continue

        rel = file_path.relative_to(root).as_posix()
        if rel in ALLOWED:
            continue
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
