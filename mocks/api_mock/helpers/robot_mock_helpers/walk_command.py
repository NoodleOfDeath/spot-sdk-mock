"""Send an SE2TrajectoryCommand to robot_mock — straight walk along +X."""
from __future__ import annotations

import json
import os
import sys
import time

import grpc
from bosdyn.api import (
    geometry_pb2,
    robot_command_pb2,
    robot_command_service_pb2_grpc,
    robot_state_pb2,
    robot_state_service_pb2_grpc,
    trajectory_pb2,
)
from bosdyn.api.basic_command_pb2 import SE2TrajectoryCommand
from bosdyn.client.frame_helpers import BODY_FRAME_NAME, ODOM_FRAME_NAME, get_a_tform_b
from google.protobuf import duration_pb2, timestamp_pb2


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: walk_command.py <distance_m> [heading_rad]", file=sys.stderr)
        return 1
    distance_m = float(sys.argv[1])
    heading_rad = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0

    host = os.environ.get("ROBOT_MOCK_HOST", "robot_mock")
    port = int(os.environ.get("ROBOT_MOCK_PORT", "44444"))
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = robot_command_service_pb2_grpc.RobotCommandServiceStub(channel)

    # ``distance_m`` is a *delta* from the current body pose so successive
    # walks accumulate. Look up the current body pose in odom and add the
    # delta to compute the absolute goal.
    rs_stub = robot_state_service_pb2_grpc.RobotStateServiceStub(channel)
    rs = rs_stub.GetRobotState(
        robot_state_pb2.RobotStateRequest(), timeout=4.0
    ).robot_state
    body_in_odom = get_a_tform_b(
        rs.kinematic_state.transforms_snapshot,
        ODOM_FRAME_NAME,
        BODY_FRAME_NAME,
    )
    cur_x = body_in_odom.x if body_in_odom is not None else 0.0
    cur_y = body_in_odom.y if body_in_odom is not None else 0.0

    req = robot_command_pb2.RobotCommandRequest()
    req.header.client_name = "api_mock-walk_command"
    req.header.request_timestamp.GetCurrentTime()

    traj = req.command.synchronized_command.mobility_command.se2_trajectory_request
    traj.se2_frame_name = "odom"
    point = traj.trajectory.points.add()
    point.pose.position.x = cur_x + distance_m
    point.pose.position.y = cur_y
    point.pose.angle = heading_rad
    # Time-since-reference: 0 for the trajectory's start point.
    point.time_since_reference.CopyFrom(duration_pb2.Duration(seconds=0))
    traj.trajectory.reference_time.GetCurrentTime()

    resp = stub.RobotCommand(req, timeout=4.0)
    out = {
        "command_id": int(resp.robot_command_id),
        "status": robot_command_pb2.RobotCommandResponse.Status.Name(resp.status),
    }
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
