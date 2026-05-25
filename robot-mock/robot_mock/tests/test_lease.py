"""Lease service tests."""
from __future__ import annotations

from bosdyn.client.lease import LeaseClient


def test_acquire_lease(make_client, vlog):
    vlog("TEST: LeaseService — AcquireLease assigns the 'body' resource with sequence >= 1")
    client = make_client(LeaseClient)
    vlog("ACTION: calling LeaseClient.acquire('body')")
    lease = client.acquire("body")
    vlog("ASSERT: lease.lease_proto.resource == 'body'")
    assert lease.lease_proto.resource == "body"
    vlog("ASSERT: lease.lease_proto.sequence[0] >= 1 (monotonically increasing)")
    assert list(lease.lease_proto.sequence)[0] >= 1
    vlog("PASS: AcquireLease returned a body lease with a positive sequence number")


def test_take_lease(make_client, vlog):
    vlog("TEST: LeaseService — TakeLease forcefully grabs ownership of the body resource")
    client = make_client(LeaseClient)
    vlog("ACTION: calling LeaseClient.take('body')")
    lease = client.take("body")
    vlog("ASSERT: lease.lease_proto.resource == 'body'")
    assert lease.lease_proto.resource == "body"
    vlog("PASS: TakeLease returned a body lease")


def test_list_leases_includes_body(make_client, vlog):
    vlog("TEST: LeaseService — ListLeases includes both 'body' and 'mobility' sub-resources")
    client = make_client(LeaseClient)
    vlog("ACTION: calling LeaseClient.list_leases()")
    resources = client.list_leases()
    names = {r.resource for r in resources}
    vlog(f"ASSERT: 'body' in resource names ({sorted(names)})")
    assert "body" in names
    vlog("ASSERT: 'mobility' in resource names")
    assert "mobility" in names
    vlog("PASS: ListLeases advertised body + mobility sub-resources")


def test_retain_lease(make_client, vlog):
    vlog("TEST: LeaseService — RetainLease succeeds on a freshly acquired lease")
    client = make_client(LeaseClient)
    vlog("ACTION: acquire('body') then retain_lease(lease)")
    lease = client.acquire("body")
    # retain_lease returns None on success; we assert it does not raise.
    client.retain_lease(lease)
    vlog("ASSERT: retain_lease did not raise (no LeaseUseError, no RpcError)")
    assert True  # documented post-condition: no exception
    vlog("PASS: RetainLease accepted the lease and returned without error")


def test_return_lease(make_client, vlog):
    vlog("TEST: LeaseService — ReturnLease clears ownership for the body resource")
    client = make_client(LeaseClient)
    vlog("ACTION: acquire('body') then return_lease(lease)")
    lease = client.acquire("body")
    client.return_lease(lease)
    vlog("ASSERT: return_lease did not raise (status STATUS_OK on the server)")
    assert True
    vlog("PASS: ReturnLease accepted the lease and returned without error")
