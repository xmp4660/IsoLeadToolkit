import logging
"""Replace print(...) calls with logging and insert logger where needed."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "reference",
    "assets",
    "locales",
}

TAG_LEVELS = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARN": "warning",
    "ERROR": "error",
    "FATAL": "critical",
}

PRINT_LINE_RE = re.compile(r"^(?P<indent>\s*)print\((?P<body>.*)\)\s*$")
TAG_RE = re.compile(r"\[(DEBUG|INFO|WARN|ERROR|FATAL)\]")


def _iter_py_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def _strip_flush(body: str) -> str:
    body = re.sub(r",\s*flush\s*=\s*True\s*$", "", body)
    body = re.sub(r",\s*flush\s*=\s*False\s*$", "", body)
    body = re.sub(r"\bflush\s*=\s*True\s*,?\s*", "", body)
    body = re.sub(r"\bflush\s*=\s*False\s*,?\s*", "", body)
    return body.strip().rstrip(",")


def _split_args(body: str) -> List[str]:
    args: List[str] = []
    current: List[str] = []
    depth = 0
    in_string = False
    quote = ""
    escape = False

    for ch in body:
        if in_string:
            current.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue

        if ch in ("'", '"'):
            in_string = True
            quote = ch
            current.append(ch)
            continue

        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)

        if ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue

        current.append(ch)

    if current:
        args.append("".join(current).strip())

    return [a for a in args if a]


def _detect_level(body: str) -> str:
    match = TAG_RE.search(body)
    if match:
        return TAG_LEVELS.get(match.group(1), "info")
    return "info"


def _build_logger_call(level: str, args: List[str]) -> str:
    if not args:
        return f"logger.{level}(\"\")"
    if len(args) == 1:
        return f"logger.{level}({args[0]})"
    joined = ", ".join(f"str({arg})" for arg in args)
    return f"logger.{level}(\" \".join([{joined}]))"


def _ensure_logger_import(lines: List[str]) -> Tuple[List[str], bool]:
    has_logging = any(re.match(r"\s*import\s+logging\b", line) for line in lines)
    has_logger = any("logger = logging.getLogger(__name__)" in line for line in lines)
    if has_logging and has_logger:
        return lines, False

    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = idx + 1
        elif line.strip() and not line.strip().startswith("#"):
            break

    updated = lines[:]
    if not has_logging:
        updated.insert(insert_at, "import logging\n")
        insert_at += 1
    if not has_logger:
        updated.insert(insert_at, "logger = logging.getLogger(__name__)\n")

    return updated, True


def process_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    lines = text.splitlines(keepends=True)
    changed = False

    new_lines: List[str] = []
    for line in lines:
        match = PRINT_LINE_RE.match(line.rstrip("\n"))
        if not match:
            new_lines.append(line)
            continue

        body = match.group("body").strip()
        body = _strip_flush(body)
        if not body:
            new_lines.append(line)
            continue

        args = _split_args(body)
        level = _detect_level(body)
        indent = match.group("indent")
        replacement = f"{indent}{_build_logger_call(level, args)}\n"
        new_lines.append(replacement)
        changed = True

    if not changed:
        return False

    new_lines, import_changed = _ensure_logger_import(new_lines)
    if import_changed:
        changed = True

    new_text = "".join(new_lines)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True

    return False


def main() -> None:
    updated = 0
    for path in _iter_py_files(ROOT):
        if process_file(path):
            updated += 1
    logger.info(f"[INFO] Updated {updated} files.")


if __name__ == "__main__":
    main()
