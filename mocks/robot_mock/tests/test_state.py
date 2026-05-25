"""RobotState service tests."""
from __future__ import annotations

from bosdyn.api import robot_state_pb2
from bosdyn.client.robot_state import RobotStateClient


def test_battery_at_eighty_percent(make_client, vlog):
    vlog("TEST: RobotStateService — BatteryState reports a plausible 80% charge")
    client = make_client(RobotStateClient)
    vlog("ACTION: calling RobotStateClient.get_robot_state()")
    state = client.get_robot_state()
    vlog("ASSERT: len(state.battery_states) >= 1")
    assert len(state.battery_states) >= 1
    vlog(
        "ASSERT: abs(state.battery_states[0].charge_percentage.value - 80.0) < 0.01"
    )
    assert abs(state.battery_states[0].charge_percentage.value - 80.0) < 0.01
    vlog("PASS: GetRobotState reports a single BatteryState at 80% charge")


def test_kinematic_state_has_body_in_tree(make_client, vlog):
    vlog("TEST: RobotStateService — KinematicState.transforms_snapshot contains body+odom")
    client = make_client(RobotStateClient)
    vlog("ACTION: get_robot_state() and inspect transforms_snapshot")
    state = client.get_robot_state()
    edges = state.kinematic_state.transforms_snapshot.child_to_parent_edge_map
    vlog("ASSERT: 'body' frame is in the transform tree")
    assert "body" in edges
    vlog("ASSERT: 'odom' frame is in the transform tree")
    assert "odom" in edges
    body_edge = edges["body"]
    vlog(
        f"ASSERT: body Z < 0.5 (sitting pose). actual Z = "
        f"{body_edge.parent_tform_child.position.z}"
    )
    assert body_edge.parent_tform_child.position.z < 0.5
    vlog("PASS: KinematicState publishes body+odom frames with a sitting body pose")


def test_metrics(make_client, vlog):
    vlog("TEST: RobotStateService — GetRobotMetrics includes a 'distance' metric")
    client = make_client(RobotStateClient)
    vlog("ACTION: calling RobotStateClient.get_robot_metrics()")
    metrics = client.get_robot_metrics()
    labels = {m.label for m in metrics.metrics}
    vlog(f"ASSERT: 'distance' in metric labels ({sorted(labels)})")
    assert "distance" in labels
    vlog("PASS: GetRobotMetrics returns the expected 'distance' metric")


def test_hardware_configuration(make_client, vlog):
    vlog("TEST: RobotStateService — GetRobotHardwareConfiguration reports off-robot capability")
    client = make_client(RobotStateClient)
    vlog("ACTION: calling RobotStateClient.get_robot_hardware_configuration()")
    hw = client.get_robot_hardware_configuration()
    vlog("ASSERT: hw.can_power_command_request_off_robot is True")
    assert hw.can_power_command_request_off_robot is True
    vlog("PASS: HardwareConfiguration advertises can_power_command_request_off_robot=True")
