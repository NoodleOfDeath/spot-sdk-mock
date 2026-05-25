"""Fetch a RobotState from robot_mock and emit a JSON summary on stdout."""
from __future__ import annotations

import json
import os
import sys

import grpc
from bosdyn.api import (
    robot_state_pb2,
    robot_state_service_pb2_grpc,
    power_pb2,
)


def main() -> int:
    host = os.environ.get("ROBOT_MOCK_HOST", "robot_mock")
    port = int(os.environ.get("ROBOT_MOCK_PORT", "44444"))
    addr = f"{host}:{port}"
    channel = grpc.insecure_channel(addr)
    stub = robot_state_service_pb2_grpc.RobotStateServiceStub(channel)
    req = robot_state_pb2.RobotStateRequest()
    resp = stub.GetRobotState(req, timeout=4.0)
    rs = resp.robot_state

    motor_power = rs.power_state.motor_power_state
    motor_name = power_pb2.PowerCommandStatus.Name(motor_power) if False else \
        robot_state_pb2.PowerState.MotorPowerState.Name(motor_power)
    estop_cut = any(s.state.value == s.state.STATE_ESTOPPED for s in rs.estop_states)
    battery_pct = 0.0
    if rs.battery_states:
        battery_pct = round(rs.battery_states[0].charge_percentage.value, 1)
    stand_state = "unknown"
    for k in ("foot_state", "behavior_fault_state"):
        # No direct stand-state field; infer crudely from power
        pass
    if motor_name == "MOTOR_POWER_STATE_ON":
        stand_state = "standing"
    elif motor_name == "MOTOR_POWER_STATE_OFF":
        stand_state = "sitting"

    out = {
        "power_state": motor_name.replace("MOTOR_POWER_STATE_", ""),
        "estop_cut": bool(estop_cut),
        "stand_state": stand_state,
        "battery_pct": battery_pct,
    }
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
