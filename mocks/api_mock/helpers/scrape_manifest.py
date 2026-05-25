"""Scan upstream Spot SDK tests under ``vendor/spot-sdk/python/**/tests/`` and
write a manifest the API serves to the GUI.
"""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path


# Default search roots (mounted by docker-compose); can be overridden via env.
VENDOR_ROOTS = [
    "/app/vendor/spot-sdk/python/bosdyn-client/tests",
    "/app/vendor/spot-sdk/python/bosdyn-mission/tests",
]
LOCAL_ROOTS = [
    "/app/robot_mock/tests",
]


def _suite_for(rel_path: Path) -> str:
    """Infer a suite name from the path layout.

    ``bosdyn-client/tests/test_foo.py`` → ``client``
    ``bosdyn-mission/tests/test_foo.py`` → ``mission``
    Anything under a ``tests/<subdir>/`` falls back to that subdir name.
    """
    parts = rel_path.parts
    for i, p in enumerate(parts):
        if p == "tests":
            if i > 0:
                package = parts[i - 1]
                if package.startswith("bosdyn-"):
                    return package.removeprefix("bosdyn-")
            if i + 1 < len(parts) - 1:
                return parts[i + 1]
    return "client"


def collect(roots, default_suite: str = "client"):
    entries = []
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            print(f"skip (missing): {root_path}", file=sys.stderr)
            continue
        for py in sorted(root_path.rglob("test_*.py")):
            try:
                tree = ast.parse(py.read_text())
            except SyntaxError:
                continue
            abs_file = str(py)
            rel = py.relative_to(root_path)
            if "/app/vendor/spot-sdk" in abs_file:
                suite = _suite_for(py.relative_to(Path("/app/vendor/spot-sdk")))
            else:
                suite = default_suite
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    entries.append(
                        {
                            "id": f"{suite}/{rel.as_posix()}::{node.name}",
                            "file": abs_file,
                            "name": node.name,
                            "suite": suite,
                        }
                    )
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    for child in node.body:
                        if (
                            isinstance(child, ast.FunctionDef)
                            and child.name.startswith("test_")
                        ):
                            entries.append(
                                {
                                    "id": (
                                        f"{suite}/{rel.as_posix()}::"
                                        f"{node.name}::{child.name}"
                                    ),
                                    "file": abs_file,
                                    "name": f"{node.name}::{child.name}",
                                    "suite": suite,
                                }
                            )
    return entries


def main() -> int:
    roots_env = os.environ.get("SDK_TEST_ROOTS")
    if roots_env:
        vendor_roots = [r.strip() for r in roots_env.split(":") if r.strip()]
    else:
        vendor_roots = VENDOR_ROOTS
    local_roots_env = os.environ.get("LOCAL_TEST_ROOTS")
    if local_roots_env:
        local_roots = [r.strip() for r in local_roots_env.split(":") if r.strip()]
    else:
        local_roots = LOCAL_ROOTS
    out_path = Path(
        os.environ.get("MANIFEST_PATH", "/app/.test_manifest.json")
    )
    local = collect(local_roots, default_suite="local")
    vendor = collect(vendor_roots)
    manifest = {"local": local, "vendor": vendor}
    out_path.write_text(json.dumps(manifest, indent=2))
    print(
        f"wrote {len(local)} local + {len(vendor)} vendor entries to {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
