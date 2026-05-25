"""Scan robot_mock/tests/sdk/*.py for test functions and write a manifest."""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path


def collect(sdk_dir: Path):
    entries = []
    for py in sorted(sdk_dir.glob("test_*.py")):
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                entries.append(
                    {
                        "id": f"{py.name}::{node.name}",
                        "file": py.name,
                        "name": node.name,
                    }
                )
            elif isinstance(node, ast.ClassDef) and node.name.startswith(("Test",)):
                for child in node.body:
                    if (
                        isinstance(child, ast.FunctionDef)
                        and child.name.startswith("test_")
                    ):
                        entries.append(
                            {
                                "id": f"{py.name}::{node.name}::{child.name}",
                                "file": py.name,
                                "name": f"{node.name}::{child.name}",
                            }
                        )
    return entries


def main() -> int:
    sdk_dir = Path(
        os.environ.get("SDK_TESTS_DIR", "/app/robot_mock/tests/sdk")
    )
    if not sdk_dir.exists():
        print(f"sdk dir not found: {sdk_dir}", file=sys.stderr)
        return 1
    out_path = Path(
        os.environ.get("MANIFEST_PATH", "/app/.test_manifest.json")
    )
    entries = collect(sdk_dir)
    out_path.write_text(json.dumps(entries, indent=2))
    print(f"wrote {len(entries)} entries to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
