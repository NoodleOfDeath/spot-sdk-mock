"""Estop service tests."""
from __future__ import annotations

from bosdyn.api import estop_pb2
from bosdyn.client.estop import EstopClient


def _make_endpoint(name="mock-endpoint", role="PDB_rooted", timeout_sec=5):
    ep = estop_pb2.EstopEndpoint()
    ep.role = role
    ep.name = name
    ep.timeout.seconds = timeout_sec
    return ep


def test_register_endpoint_and_check_in(make_client, vlog):
    vlog("TEST: EstopService — register an endpoint and perform a successful check-in")
    client = make_client(EstopClient)

    vlog("ACTION: GetEstopConfig to obtain the active config id")
    config = client.get_config()
    vlog("ACTION: building EstopEndpoint and calling RegisterEstopEndpoint")
    ep = _make_endpoint()
    registered = client.register(config.unique_id, ep)
    vlog("ASSERT: registered.unique_id is non-empty (server assigned an id)")
    assert registered.unique_id  # server assigned an id

    vlog("ACTION: EstopCheckIn with stop_level=ESTOP_LEVEL_NONE, challenge=0, response=0")
    challenge = client.check_in(
        estop_pb2.ESTOP_LEVEL_NONE, registered, 0, 0, suppress_incorrect=True
    )
    vlog("ASSERT: server-issued challenge != 0")
    assert challenge != 0
    vlog("PASS: endpoint registered and EstopCheckIn produced a new challenge")


def test_system_status_includes_endpoint(make_client, vlog):
    vlog("TEST: EstopService — GetEstopSystemStatus reports registered endpoints")
    client = make_client(EstopClient)
    vlog("ACTION: get_config + register a new endpoint")
    config = client.get_config()
    ep = _make_endpoint(name="status-endpoint")
    client.register(config.unique_id, ep)

    vlog("ACTION: calling EstopClient.get_status()")
    status = client.get_status()
    vlog("ASSERT: len(status.endpoints) >= 1 (the endpoint we just registered)")
    assert len(status.endpoints) >= 1
    vlog("ASSERT: status.stop_level == ESTOP_LEVEL_NONE (no estop asserted)")
    assert status.stop_level == estop_pb2.ESTOP_LEVEL_NONE
    vlog("PASS: GetEstopSystemStatus reports the registered endpoint with NONE stop level")


def test_deregister_endpoint(make_client, vlog):
    vlog("TEST: EstopService — DeregisterEstopEndpoint removes the endpoint from status")
    client = make_client(EstopClient)
    vlog("ACTION: register an endpoint, then immediately deregister it")
    config = client.get_config()
    ep = _make_endpoint(name="dereg-endpoint")
    registered = client.register(config.unique_id, ep)
    client.deregister(config.unique_id, registered)
    status = client.get_status()
    names = {e.endpoint.unique_id for e in status.endpoints}
    vlog(f"ASSERT: registered.unique_id ({registered.unique_id!r}) is not in status.endpoints")
    assert registered.unique_id not in names
    vlog("PASS: endpoint deregistered and no longer appears in EstopSystemStatus")
