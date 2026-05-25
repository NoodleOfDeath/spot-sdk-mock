"""RobotStateService implementation."""
from __future__ import annotations

import math
import time

from bosdyn.api import (
    geometry_pb2,
    robot_state_pb2,
    robot_state_service_pb2_grpc,
)
from google.protobuf.timestamp_pb2 import Timestamp

from ..state import ROBOT_STATE
from ._header import fill_response_header


def _now_ts() -> Timestamp:
    ts = Timestamp()
    ts.GetCurrentTime()
    return ts


def _identity_pose(z: float = 0.0) -> geometry_pb2.SE3Pose:
    p = geometry_pb2.SE3Pose()
    p.position.x = 0.0
    p.position.y = 0.0
    p.position.z = z
    p.rotation.w = 1.0
    p.rotation.x = 0.0
    p.rotation.y = 0.0
    p.rotation.z = 0.0
    return p


def _build_kinematic_state(
    standing: bool, body_x: float, body_y: float, body_heading: float
) -> robot_state_pb2.KinematicState:
    ks = robot_state_pb2.KinematicState()
    ks.acquisition_timestamp.CopyFrom(_now_ts())
    snap = ks.transforms_snapshot
    # Tree: vision -> odom -> body -> {ground_plane}
    # body relative to odom carries SE2 pose (x, y, yaw) and stand/sit height.
    body_z = 0.50 if standing else 0.20

    def add_edge(child: str, parent: str, z: float = 0.0):
        snap.child_to_parent_edge_map[child].parent_frame_name = parent
        pose = snap.child_to_parent_edge_map[child].parent_tform_child
        pose.position.x = 0.0
        pose.position.y = 0.0
        pose.position.z = z
        pose.rotation.w = 1.0

    # vision -> odom (root vision has no parent)
    snap.child_to_parent_edge_map["vision"].parent_frame_name = ""
    snap.child_to_parent_edge_map["vision"].parent_tform_child.rotation.w = 1.0
    add_edge("odom", "vision", 0.0)

    # body -> odom carries SE2 pose
    snap.child_to_parent_edge_map["body"].parent_frame_name = "odom"
    body_pose = snap.child_to_parent_edge_map["body"].parent_tform_child
    body_pose.position.x = body_x
    body_pose.position.y = body_y
    body_pose.position.z = body_z
    half = body_heading / 2.0
    body_pose.rotation.w = math.cos(half)
    body_pose.rotation.x = 0.0
    body_pose.rotation.y = 0.0
    body_pose.rotation.z = math.sin(half)

    add_edge("flat_body", "body", 0.0)
    add_edge("gpe", "vision", 0.0)
    # Zero velocity
    ks.velocity_of_body_in_vision.linear.x = 0.0
    ks.velocity_of_body_in_vision.linear.y = 0.0
    ks.velocity_of_body_in_vision.linear.z = 0.0
    ks.velocity_of_body_in_vision.angular.x = 0.0
    ks.velocity_of_body_in_vision.angular.y = 0.0
    ks.velocity_of_body_in_vision.angular.z = 0.0
    return ks


class RobotStateServicer(robot_state_service_pb2_grpc.RobotStateServiceServicer):
    def GetRobotState(self, request, context):
        response = robot_state_pb2.RobotStateResponse()
        fill_response_header(response, request)

        with ROBOT_STATE.lock:
            ROBOT_STATE.settle_power_state()
            state = response.robot_state

            # Power state
            ps = state.power_state
            ps.timestamp.CopyFrom(_now_ts())
            ps.motor_power_state = ROBOT_STATE.motor_power_state
            ps.shore_power_state = robot_state_pb2.PowerState.STATE_OFF_SHORE_POWER \
                if hasattr(robot_state_pb2.PowerState, "STATE_OFF_SHORE_POWER") else 0
            ps.locomotion_charge_percentage.value = 80.0

            # Battery
            batt = state.battery_states.add()
            batt.timestamp.CopyFrom(_now_ts())
            batt.identifier = "mock-battery"
            batt.charge_percentage.value = 80.0
            batt.estimated_runtime.seconds = 3600
            batt.current.value = 5.0
            batt.voltage.value = 50.0
            batt.temperatures.append(30.0)
            batt.status = robot_state_pb2.BatteryState.STATUS_DISCHARGING

            # Estop states - one software endpoint reflecting registered endpoints overall
            est = state.estop_states.add()
            est.timestamp.CopyFrom(_now_ts())
            est.name = "mock-estop"
            est.type = robot_state_pb2.EStopState.TYPE_SOFTWARE
            est.state = (
                robot_state_pb2.EStopState.STATE_ESTOPPED
                if ROBOT_STATE.is_estop_cut()
                else robot_state_pb2.EStopState.STATE_NOT_ESTOPPED
            )

            # Kinematic state
            standing = ROBOT_STATE.stand_state == "stand"
            state.kinematic_state.CopyFrom(
                _build_kinematic_state(
                    standing,
                    ROBOT_STATE.body_pose_se2.x,
                    ROBOT_STATE.body_pose_se2.y,
                    ROBOT_STATE.body_pose_se2.heading,
                )
            )

        return response

    def GetRobotMetrics(self, request, context):
        response = robot_state_pb2.RobotMetricsResponse()
        fill_response_header(response, request)
        m = response.robot_metrics
        m.timestamp.CopyFrom(_now_ts())
        with ROBOT_STATE.lock:
            entries = [
                ("distance", float(ROBOT_STATE.body_pose_se2.x), "m"),
                ("gait_cycles", float(ROBOT_STATE.gait_cycles), ""),
                ("electric_power", 50.0, "W"),
                ("body_pose_x", float(ROBOT_STATE.body_pose_se2.x), "m"),
                ("body_pose_y", float(ROBOT_STATE.body_pose_se2.y), "m"),
                ("body_pose_heading", float(ROBOT_STATE.body_pose_se2.heading), "rad"),
                (
                    "locomotion_elapsed_ms",
                    float(ROBOT_STATE.locomotion_elapsed_ms()),
                    "ms",
                ),
            ]
            if ROBOT_STATE.locomotion_target_m is not None:
                entries.append(
                    ("locomotion_target_m", float(ROBOT_STATE.locomotion_target_m), "m")
                )
        for name, value, unit in entries:
            entry = m.metrics.add()
            entry.label = name
            entry.float_value = value
            entry.units = unit
        return response

    def GetRobotHardwareConfiguration(self, request, context):
        response = robot_state_pb2.RobotHardwareConfigurationResponse()
        fill_response_header(response, request)
        hw = response.hardware_configuration
        hw.can_power_command_request_off_robot = True
        hw.can_power_command_request_cycle_robot = False
        hw.can_power_command_request_payload_ports = False
        hw.can_power_command_request_wifi_radio = False
        hw.has_audio_visual_system = False
        return response

    def GetRobotLinkModel(self, request, context):
        response = robot_state_pb2.RobotLinkModelResponse()
        fill_response_header(response, request)
        return response
