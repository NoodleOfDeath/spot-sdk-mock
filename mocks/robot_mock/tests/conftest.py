"""Shared pytest fixtures for robot_mock tests.

Spins up the mock gRPC server in a background thread on an ephemeral port and
yields an insecure channel for tests to use with the SDK client classes.
"""
from __future__ import annotations

import os
import socket
import time

import grpc
import pytest

from robot_mock.server import build_server
from robot_mock.state import ROBOT_STATE


def pytest_addoption(parser):
    parser.addoption("--verbose-mock", action="store_true", default=False)


@pytest.fixture
def vlog(request):
    flag = request.config.getoption("--verbose-mock")

    def _log(msg):
        if flag:
            print(f"\n  {msg}", flush=True)

    return _log


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server_port() -> int:
    port = int(os.environ.get("MOCK_ROBOT_PORT", _free_port()))
    return port


@pytest.fixture(scope="session")
def grpc_server(server_port):
    server, bound = build_server(port=server_port)
    server.start()
    # Brief moment for server to be ready.
    deadline = time.time() + 2.0
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", bound), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    yield bound
    server.stop(grace=1.0).wait()


@pytest.fixture()
def channel(grpc_server):
    ch = grpc.insecure_channel(f"127.0.0.1:{grpc_server}")
    yield ch
    ch.close()


class _MockServerHandle:
    def __init__(self, port: int):
        self.port = port


@pytest.fixture(scope="session")
def mock_server(grpc_server):
    """Session-scoped handle exposing the running mock server's port.

    Persists across the entire SDK test run so the gRPC server is bound
    once and reused.
    """
    return _MockServerHandle(port=grpc_server)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset shared mutable state between tests to keep them isolated."""
    with ROBOT_STATE.lock:
        if ROBOT_STATE._locomotion_stop is not None:
            ROBOT_STATE._locomotion_stop.set()
            ROBOT_STATE._locomotion_stop = None
        ROBOT_STATE.locomotion_target_m = None
        ROBOT_STATE.locomotion_start_time_ns = None
        ROBOT_STATE.gait_cycles = 0
        ROBOT_STATE.body_pose_se2.x = 0.0
        ROBOT_STATE.body_pose_se2.y = 0.0
        ROBOT_STATE.body_pose_se2.heading = 0.0
        ROBOT_STATE.motor_power_state = ROBOT_STATE.MOTOR_OFF
        ROBOT_STATE._power_transition_target = None
        ROBOT_STATE.estop_endpoints.clear()
        ROBOT_STATE.stand_state = "sit"
        ROBOT_STATE.body_height = 0.20
        ROBOT_STATE.commands.clear()
        ROBOT_STATE.power_commands.clear()
        for rec in ROBOT_STATE.leases.values():
            rec.sequence = [0]
            rec.client_names = []
            rec.owner_client_name = ""
            rec.owner_user_name = ""
    yield


def _bind_client(client_cls, channel):
    client = client_cls()
    client.channel = channel
    return client


@pytest.fixture()
def make_client(channel):
    """Create SDK clients bound to the mock server.

    For RobotCommandClient, an established TimeSyncEndpoint is also injected so
    that command timestamps can be converted from local to robot time without
    needing a full ``Robot`` connection flow.
    """
    from bosdyn.client.robot_command import RobotCommandClient
    from bosdyn.client.time_sync import TimeSyncClient, TimeSyncEndpoint

    timesync_endpoint = None

    def _ensure_timesync():
        nonlocal timesync_endpoint
        if timesync_endpoint is None:
            ts_client = _bind_client(TimeSyncClient, channel)
            timesync_endpoint = TimeSyncEndpoint(ts_client)
            timesync_endpoint.establish_timesync(max_samples=4, break_on_success=True)
        return timesync_endpoint

    def _factory(client_cls):
        client = _bind_client(client_cls, channel)
        if isinstance(client, RobotCommandClient):
            client._timesync_endpoint = _ensure_timesync()
        return client

    return _factory
