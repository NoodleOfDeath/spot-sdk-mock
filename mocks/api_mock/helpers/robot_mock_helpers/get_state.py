"""Fetch RobotState + MissionState from robot_mock and emit JSON on stdout."""
from __future__ import annotations

import json
import os
import sys

import grpc
from bosdyn.api import (
    robot_state_pb2,
    robot_state_service_pb2_grpc,
)
from bosdyn.api.mission import (
    mission_pb2,
    mission_service_pb2_grpc,
)


def main() -> int:
    host = os.environ.get("ROBOT_MOCK_HOST", "robot_mock")
    port = int(os.environ.get("ROBOT_MOCK_PORT", "44444"))
    addr = f"{host}:{port}"
    channel = grpc.insecure_channel(addr)

    rs_stub = robot_state_service_pb2_grpc.RobotStateServiceStub(channel)
    rs = rs_stub.GetRobotState(
        robot_state_pb2.RobotStateRequest(), timeout=4.0
    ).robot_state

    motor_power = rs.power_state.motor_power_state
    motor_name = robot_state_pb2.PowerState.MotorPowerState.Name(motor_power)
    estop_cut = any(
        s.state == s.STATE_ESTOPPED for s in rs.estop_states
    )
    battery_pct = 0.0
    if rs.battery_states:
        battery_pct = round(rs.battery_states[0].charge_percentage.value, 1)
    stand_state = "unknown"
    if motor_name == "MOTOR_POWER_STATE_ON":
        stand_state = "standing"
    elif motor_name == "MOTOR_POWER_STATE_OFF":
        stand_state = "sitting"

    mission_state = "IDLE"
    try:
        ms_stub = mission_service_pb2_grpc.MissionServiceStub(channel)
        ms = ms_stub.GetState(
            mission_pb2.GetStateRequest(), timeout=4.0
        ).state
        if ms.status == mission_pb2.State.STATUS_RUNNING:
            mission_state = "PLAYING"
        elif ms.status == mission_pb2.State.STATUS_PAUSED:
            mission_state = "PAUSED"
    except grpc.RpcError:
        pass

    out = {
        "power_state": motor_name.replace("MOTOR_POWER_STATE_", ""),
        "estop_cut": bool(estop_cut),
        "stand_state": stand_state,
        "battery_pct": battery_pct,
        "mission_state": mission_state,
    }
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
