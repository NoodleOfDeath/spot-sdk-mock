"""Mission-suite conftest.

Inherits the ``--mock`` flag from the parent ``tests/sdk/conftest.py``. The
upstream ``test_client.py`` stands up its own in-process gRPC server via
``helpers.start_server`` and points the ``MissionClient`` at it, so when
``--mock`` is active we still leave that wiring alone — there is no
network call back to the long-running mock server. The fixture below
records the mock-server endpoint on the client for any caller that wants
to talk to the live robot_mock instance.
"""
from __future__ import annotations

import pytest


def _mock_active(config) -> bool:
    try:
        return bool(config.getoption("--mock"))
    except (ValueError, KeyError):
        return False


@pytest.fixture(autouse=True)
def mission_mock_channel(request):
    if not _mock_active(request.config):
        yield
        return

    # Resolve the running mock-server endpoint and stamp it on every freshly
    # created MissionClient so downstream code that wants to bypass the
    # in-test server can reach the real one.
    server = request.getfixturevalue("mock_server")
    import bosdyn.mission.client as mc

    original_init = mc.MissionClient.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._mock_target = f"localhost:{server.port}"  # type: ignore[attr-defined]

    mc.MissionClient.__init__ = patched_init  # type: ignore[assignment]
    try:
        yield
    finally:
        mc.MissionClient.__init__ = original_init  # type: ignore[assignment]
