"""Verify the basic SDK connection flow: robot-id, auth, directory, time-sync."""
from __future__ import annotations

import time

from bosdyn.client.auth import AuthClient
from bosdyn.client.directory import DirectoryClient
from bosdyn.client.robot_id import RobotIdClient
from bosdyn.client.time_sync import TimeSyncClient, TimeSyncEndpoint


def test_robot_id(make_client, vlog):
    vlog("TEST: RobotIdService — returns the hardcoded mock identity")
    vlog("ACTION: building RobotIdClient and calling get_id()")
    client = make_client(RobotIdClient)
    rid = client.get_id()
    vlog("ASSERT: rid.serial_number == 'MOCK-0001'")
    assert rid.serial_number == "MOCK-0001"
    vlog("ASSERT: rid.species == 'spot'")
    assert rid.species == "spot"
    vlog("ASSERT: rid.nickname == 'mock-spot'")
    assert rid.nickname == "mock-spot"
    vlog("ASSERT: rid.software_release.version.major_version == 5")
    assert rid.software_release.version.major_version == 5
    vlog("ASSERT: rid.software_release.version.minor_version == 1")
    assert rid.software_release.version.minor_version == 1
    vlog("ASSERT: rid.software_release.version.patch_level == 4")
    assert rid.software_release.version.patch_level == 4
    vlog("PASS: RobotId proto matches the mock's static identity (SDK 5.1.4)")


def test_auth_returns_token(make_client, vlog):
    vlog("TEST: AuthService — returns a JWT-shaped token for any credentials")
    client = make_client(AuthClient)
    vlog("ACTION: calling AuthClient.auth('anyuser', 'anypassword')")
    token = client.auth("anyuser", "anypassword")
    vlog("ASSERT: token is a str with exactly 2 dots (header.payload.signature)")
    assert isinstance(token, str) and token.count(".") == 2
    vlog("PASS: AuthService issued a JWT-shaped token")


def test_auth_refresh(make_client, vlog):
    vlog("TEST: AuthService — token refresh via auth_with_token")
    client = make_client(AuthClient)
    vlog("ACTION: initial auth() to obtain a token")
    token = client.auth("u1", "p1")
    vlog("ACTION: calling auth_with_token() to refresh")
    refreshed = client.auth_with_token(token)
    vlog("ASSERT: refreshed token has exactly 2 dots (header.payload.signature)")
    assert refreshed.count(".") == 2
    vlog("PASS: AuthService accepted the token and returned a refreshed JWT")


def test_directory_lists_services(make_client, vlog):
    vlog("TEST: DirectoryService — ListServiceEntries advertises every required service")
    client = make_client(DirectoryClient)
    vlog("ACTION: calling DirectoryClient.list()")
    entries = client.list()
    names = {e.name for e in entries}
    expected = {
        "robot-id",
        "auth",
        "directory",
        "directory-registration",
        "time-sync",
        "estop",
        "lease",
        "power",
        "robot-command",
        "robot-state",
        "image",
    }
    vlog(f"ASSERT: directory contains all required service names {sorted(expected)}")
    assert expected.issubset(names)
    vlog("PASS: every required service is registered with DirectoryService")


def test_directory_get_specific(make_client, vlog):
    vlog("TEST: DirectoryService — GetServiceEntry returns the requested entry")
    client = make_client(DirectoryClient)
    vlog("ACTION: calling DirectoryClient.get_entry('robot-state')")
    entry = client.get_entry("robot-state")
    vlog("ASSERT: entry.name == 'robot-state'")
    assert entry.name == "robot-state"
    vlog("ASSERT: entry.type == 'bosdyn.api.RobotStateService'")
    assert entry.type == "bosdyn.api.RobotStateService"
    vlog("PASS: DirectoryService returned the expected ServiceEntry")


def test_time_sync_converges_in_few_rounds(make_client, vlog):
    vlog("TEST: TimeSyncService — TimeSyncThread converges in <=3 rounds")
    client = make_client(TimeSyncClient)
    endpoint = TimeSyncEndpoint(client)
    vlog("ACTION: endpoint.establish_timesync(max_samples=3, break_on_success=True)")
    converged = endpoint.establish_timesync(max_samples=3, break_on_success=True)
    vlog("ASSERT: establish_timesync returned True (converged)")
    assert converged
    vlog("ASSERT: endpoint.has_established_time_sync is True")
    assert endpoint.has_established_time_sync
    vlog("PASS: TimeSyncService reaches STATUS_OK within 3 samples")
