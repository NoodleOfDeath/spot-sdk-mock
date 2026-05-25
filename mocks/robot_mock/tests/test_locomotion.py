"""SE2TrajectoryCommand — assert the mock walks 5 metres along +X."""
from __future__ import annotations

import time

from bosdyn.api.basic_command_pb2 import SE2TrajectoryCommand
from bosdyn.client.frame_helpers import BODY_FRAME_NAME, ODOM_FRAME_NAME, get_a_tform_b
from bosdyn.client.lease import LeaseClient
from bosdyn.client.robot_command import (
    RobotCommandBuilder,
    RobotCommandClient,
)
from bosdyn.client.robot_state import RobotStateClient


def test_walk_5m(make_client, vlog):
    vlog("TEST: SE2TrajectoryCommand — walk 5m forward along +X")
    lease_client = make_client(LeaseClient)
    lease = lease_client.acquire("body")
    cmd_client = make_client(RobotCommandClient)
    rs_client = make_client(RobotStateClient)

    vlog("ACTION: sending SE2TrajectoryCommand goal x=5.0 frame=odom")
    cmd = RobotCommandBuilder.synchro_se2_trajectory_point_command(
        goal_x=5.0, goal_y=0.0, goal_heading=0.0, frame_name=ODOM_FRAME_NAME
    )
    cmd_id = cmd_client.robot_command(cmd, lease=lease.lease_proto)

    vlog("ACTION: polling feedback until STATUS_AT_GOAL (10s timeout)")
    deadline = time.time() + 10.0
    final_status = None
    while time.time() < deadline:
        fb = cmd_client.robot_command_feedback(cmd_id)
        sf = fb.feedback.synchronized_feedback.mobility_command_feedback
        final_status = sf.se2_trajectory_feedback.status
        if final_status == SE2TrajectoryCommand.Feedback.STATUS_AT_GOAL:
            break
        time.sleep(0.1)

    assert final_status == SE2TrajectoryCommand.Feedback.STATUS_AT_GOAL, (
        f"trajectory did not reach goal: status={final_status}"
    )

    vlog("ASSERT: body pose in odom is ≈ (5.0, 0.0) ±0.1")
    state = rs_client.get_robot_state()
    body_in_odom = get_a_tform_b(
        state.kinematic_state.transforms_snapshot,
        ODOM_FRAME_NAME,
        BODY_FRAME_NAME,
    )
    assert body_in_odom is not None
    assert abs(body_in_odom.x - 5.0) < 0.1, (
        f"body.x={body_in_odom.x:.3f} expected ≈ 5.0"
    )
    assert abs(body_in_odom.y) < 0.1
    vlog(f"PASS: walked to x={body_in_odom.x:.3f} (5.0m goal)")


def test_no_locomotion_when_idle(make_client, vlog):
    """Other tests must not leave locomotion in-flight."""
    vlog("TEST: with no SE2 trajectory issued, locomotion_target_m is None")
    rs_client = make_client(RobotStateClient)
    state = rs_client.get_robot_state()
    # Body is at the origin when no walk has been issued.
    body_in_odom = get_a_tform_b(
        state.kinematic_state.transforms_snapshot,
        ODOM_FRAME_NAME,
        BODY_FRAME_NAME,
    )
    assert body_in_odom is not None
    assert abs(body_in_odom.x) < 1e-3
    assert abs(body_in_odom.y) < 1e-3
    vlog("PASS: body at origin, no in-flight locomotion")
