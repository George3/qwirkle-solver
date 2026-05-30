#!/usr/bin/env python3
"""Check for drift between imported third-party modules and requirements.txt.

This script is intentionally lightweight (stdlib only) so it can run in any
Python environment without bootstrap dependencies.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_FILE = ROOT / "requirements.txt"

# App is launched with "python -m uvicorn app:app" even though uvicorn is not
# imported in source files; keep it as an explicit runtime dependency.
EXTRA_RUNTIME_DEPS = {"uvicorn"}

IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
}


def normalize_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIR_NAMES for part in path.parts)


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if should_skip(path):
            continue
        yield path


def get_local_modules(root: Path) -> set[str]:
    local_modules: set[str] = set()
    for path in iter_python_files(root):
        if path.name == "__init__.py":
            local_modules.add(path.parent.name)
        else:
            local_modules.add(path.stem)
    return local_modules


def imported_top_level_modules(path: Path) -> set[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return set()

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return set()

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".", 1)[0]
                if top:
                    modules.add(top)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module:
                continue
            top = node.module.split(".", 1)[0]
            if top:
                modules.add(top)
    return modules


def get_stdlib_modules() -> set[str]:
    modules = set(getattr(sys, "stdlib_module_names", set()))
    # Commonly imported names that can be absent depending on Python build.
    modules.update({"typing", "pathlib", "dataclasses"})
    return modules


def parse_requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    requirement_name = re.compile(r"^\s*([A-Za-z0-9_.-]+)")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("-r", "--requirement", "-e", "--editable")):
            continue

        match = requirement_name.match(stripped)
        if match:
            names.add(normalize_name(match.group(1)))

    return names


def main() -> int:
    if not REQUIREMENTS_FILE.exists():
        print(f"Missing requirements file: {REQUIREMENTS_FILE}")
        return 2

    stdlib_modules = get_stdlib_modules()
    local_modules = get_local_modules(ROOT)

    imported: set[str] = set()
    for py_file in iter_python_files(ROOT):
        imported.update(imported_top_level_modules(py_file))

    third_party = {
        normalize_name(mod)
        for mod in imported
        if mod not in stdlib_modules and mod not in local_modules
    }

    required = set(third_party)
    required.update(EXTRA_RUNTIME_DEPS)

    listed = parse_requirement_names(REQUIREMENTS_FILE)

    missing = sorted(required - listed)
    extra = sorted(listed - required)

    if not missing and not extra:
        print("requirements.txt is in sync with direct runtime imports.")
        return 0

    print("requirements.txt drift detected:")
    if missing:
        print("  Missing packages:")
        for name in missing:
            print(f"    - {name}")
    if extra:
        print("  Potentially unused packages:")
        for name in extra:
            print(f"    - {name}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
