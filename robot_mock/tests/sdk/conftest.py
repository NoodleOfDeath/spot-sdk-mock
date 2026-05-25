"""SDK-suite conftest.

Registers the ``--mock`` flag at the ``sdk/`` level so it's available to
both ``sdk/client/`` (upstream bosdyn-client tests) and ``sdk/mission/``
(upstream bosdyn-mission tests). Per-suite fixtures live in each
subdirectory's own ``conftest.py``.
"""
from __future__ import annotations


def pytest_addoption(parser):
    if not any(opt.dest == "mock" for opt in parser._anonymous.options):  # type: ignore[attr-defined]
        try:
            parser.addoption(
                "--mock",
                action="store_true",
                default=False,
                help="Route SDK client channels to the local mock server",
            )
        except ValueError:
            pass
