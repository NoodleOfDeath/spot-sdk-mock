"""RobotCommand service tests."""
from __future__ import annotations

import time

from bosdyn.api import power_pb2
from bosdyn.client.lease import LeaseClient
from bosdyn.client.power import PowerClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient


def _power_on(make_client):
    lease_client = make_client(LeaseClient)
    lease = lease_client.acquire("body")
    power_client = make_client(PowerClient)
    resp = power_client.power_command(
        power_pb2.PowerCommandRequest.REQUEST_ON_MOTORS, lease=lease.lease_proto
    )
    deadline = time.time() + 5.0
    while time.time() < deadline:
        s = power_client.power_command_feedback(resp.power_command_id)
        if s == power_pb2.STATUS_SUCCESS:
            break
        time.sleep(0.05)
    return lease


def test_stand_command(make_client, vlog):
    vlog("TEST: RobotCommandService — synchro_stand_command issues a stand and returns feedback")
    vlog("ACTION: powering on motors so that stand is accepted")
    lease = _power_on(make_client)
    cmd_client = make_client(RobotCommandClient)
    vlog("ACTION: sending RobotCommandBuilder.synchro_stand_command()")
    command = RobotCommandBuilder.synchro_stand_command()
    cmd_id = cmd_client.robot_command(command, lease=lease.lease_proto)
    vlog("ASSERT: cmd_id != 0 (server allocated a robot_command_id)")
    assert cmd_id != 0

    vlog("ACTION: fetching RobotCommandFeedback for the stand command")
    fb = cmd_client.robot_command_feedback(cmd_id)
    vlog("ASSERT: feedback.HasField('synchronized_feedback') (mobility feedback present)")
    assert fb.feedback.HasField("synchronized_feedback")
    vlog("PASS: stand command accepted and feedback includes synchronized_feedback")


def test_sit_command(make_client, vlog):
    vlog("TEST: RobotCommandService — synchro_sit_command issues a sit")
    vlog("ACTION: powering on motors so that sit is accepted")
    lease = _power_on(make_client)
    cmd_client = make_client(RobotCommandClient)
    vlog("ACTION: sending RobotCommandBuilder.synchro_sit_command()")
    cmd_id = cmd_client.robot_command(
        RobotCommandBuilder.synchro_sit_command(), lease=lease.lease_proto
    )
    vlog("ASSERT: cmd_id != 0 (sit command accepted)")
    assert cmd_id != 0
    vlog("PASS: sit command accepted with a non-zero command id")


def test_velocity_command(make_client, vlog):
    vlog("TEST: RobotCommandService — synchro_velocity_command (SE2VelocityCommand)")
    vlog("ACTION: powering on motors")
    lease = _power_on(make_client)
    cmd_client = make_client(RobotCommandClient)
    vlog("ACTION: sending velocity command v_x=0.1, v_y=0.0, v_rot=0.0 with 1s end_time")
    command = RobotCommandBuilder.synchro_velocity_command(v_x=0.1, v_y=0.0, v_rot=0.0)
    cmd_id = cmd_client.robot_command(
        command, end_time_secs=time.time() + 1.0, lease=lease.lease_proto
    )
    vlog("ASSERT: cmd_id != 0 (velocity command accepted)")
    assert cmd_id != 0
    vlog("PASS: SE2VelocityCommand accepted with a non-zero command id")


def test_selfright_command(make_client, vlog):
    vlog("TEST: RobotCommandService — selfright_command (full-body command)")
    vlog("ACTION: powering on motors")
    lease = _power_on(make_client)
    cmd_client = make_client(RobotCommandClient)
    vlog("ACTION: sending RobotCommandBuilder.selfright_command()")
    cmd_id = cmd_client.robot_command(
        RobotCommandBuilder.selfright_command(), lease=lease.lease_proto
    )
    vlog("ASSERT: cmd_id != 0 (selfright command accepted)")
    assert cmd_id != 0
    vlog("PASS: selfright command accepted with a non-zero command id")


def test_stop_command(make_client, vlog):
    vlog("TEST: RobotCommandService — stop_command (full-body command)")
    vlog("ACTION: powering on motors")
    lease = _power_on(make_client)
    cmd_client = make_client(RobotCommandClient)
    vlog("ACTION: sending RobotCommandBuilder.stop_command()")
    cmd_id = cmd_client.robot_command(
        RobotCommandBuilder.stop_command(), lease=lease.lease_proto
    )
    vlog("ASSERT: cmd_id != 0 (stop command accepted)")
    assert cmd_id != 0
    vlog("PASS: stop command accepted with a non-zero command id")


def test_safe_power_off(make_client, vlog):
    vlog("TEST: RobotCommandService — safe_power_off_command (full-body command)")
    vlog("ACTION: powering on motors before safe-power-off")
    lease = _power_on(make_client)
    cmd_client = make_client(RobotCommandClient)
    vlog("ACTION: sending RobotCommandBuilder.safe_power_off_command()")
    cmd_id = cmd_client.robot_command(
        RobotCommandBuilder.safe_power_off_command(), lease=lease.lease_proto
    )
    vlog("ASSERT: cmd_id != 0 (safe-power-off command accepted)")
    assert cmd_id != 0
    vlog("PASS: safe_power_off command accepted with a non-zero command id")
