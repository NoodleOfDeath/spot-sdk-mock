"""Power service tests."""
from __future__ import annotations

import time

from bosdyn.api import power_pb2, robot_state_pb2
from bosdyn.client.lease import LeaseClient
from bosdyn.client.power import PowerClient
from bosdyn.client.robot_state import RobotStateClient


def test_power_on_reaches_motor_on(make_client, vlog):
    vlog("TEST: PowerService — REQUEST_ON_MOTORS drives the state machine to MOTOR_POWER_STATE_ON")
    vlog("ACTION: acquiring the 'body' lease required by PowerCommand")
    lease_client = make_client(LeaseClient)
    lease = lease_client.acquire("body")

    vlog("ACTION: sending PowerCommandRequest REQUEST_ON_MOTORS")
    power_client = make_client(PowerClient)
    response = power_client.power_command(
        power_pb2.PowerCommandRequest.REQUEST_ON_MOTORS, lease=lease.lease_proto
    )
    vlog(
        "ASSERT: response.status in {STATUS_IN_PROGRESS, STATUS_SUCCESS} "
        "(transition started or already on)"
    )
    assert response.status in (
        power_pb2.STATUS_IN_PROGRESS,
        power_pb2.STATUS_SUCCESS,
    )

    vlog("ACTION: polling PowerCommandFeedback until STATUS_SUCCESS or 5s deadline")
    deadline = time.time() + 5.0
    while time.time() < deadline:
        status = power_client.power_command_feedback(response.power_command_id)
        if status == power_pb2.STATUS_SUCCESS:
            break
        time.sleep(0.05)

    vlog("ACTION: GetRobotState to read the final motor_power_state")
    state_client = make_client(RobotStateClient)
    state = state_client.get_robot_state()
    vlog("ASSERT: state.power_state.motor_power_state == MOTOR_POWER_STATE_ON")
    assert state.power_state.motor_power_state == robot_state_pb2.PowerState.MOTOR_POWER_STATE_ON
    vlog("PASS: power-on transition reached MOTOR_POWER_STATE_ON")


def test_power_off(make_client, vlog):
    vlog("TEST: PowerService — REQUEST_OFF_MOTORS returns the state machine to MOTOR_POWER_STATE_OFF")
    vlog("ACTION: acquiring the 'body' lease")
    lease_client = make_client(LeaseClient)
    lease = lease_client.acquire("body")

    vlog("ACTION: first power-on so we have a non-trivial off transition to verify")
    power_client = make_client(PowerClient)
    on_response = power_client.power_command(
        power_pb2.PowerCommandRequest.REQUEST_ON_MOTORS, lease=lease.lease_proto
    )
    deadline = time.time() + 5.0
    while time.time() < deadline:
        s = power_client.power_command_feedback(on_response.power_command_id)
        if s == power_pb2.STATUS_SUCCESS:
            break
        time.sleep(0.05)

    vlog("ACTION: sending PowerCommandRequest REQUEST_OFF_MOTORS")
    off_response = power_client.power_command(
        power_pb2.PowerCommandRequest.REQUEST_OFF_MOTORS, lease=lease.lease_proto
    )
    vlog("ACTION: polling PowerCommandFeedback until STATUS_SUCCESS or 5s deadline")
    deadline = time.time() + 5.0
    while time.time() < deadline:
        s = power_client.power_command_feedback(off_response.power_command_id)
        if s == power_pb2.STATUS_SUCCESS:
            break
        time.sleep(0.05)

    vlog("ACTION: GetRobotState to read the final motor_power_state")
    state_client = make_client(RobotStateClient)
    state = state_client.get_robot_state()
    vlog("ASSERT: state.power_state.motor_power_state == MOTOR_POWER_STATE_OFF")
    assert state.power_state.motor_power_state == robot_state_pb2.PowerState.MOTOR_POWER_STATE_OFF
    vlog("PASS: power-off transition reached MOTOR_POWER_STATE_OFF")
