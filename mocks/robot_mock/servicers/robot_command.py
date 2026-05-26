"""RobotCommandService implementation."""
from __future__ import annotations

import time

from bosdyn.api import (
    basic_command_pb2,
    robot_command_pb2,
    robot_command_service_pb2_grpc,
)

from ..state import ROBOT_STATE, CommandRecord
from ._header import fill_response_header
from .lease import fill_lease_use_result


class RobotCommandServicer(robot_command_service_pb2_grpc.RobotCommandServiceServicer):
    def RobotCommand(self, request, context):
        response = robot_command_pb2.RobotCommandResponse()
        fill_response_header(response, request)
        fill_lease_use_result(response.lease_use_result, request.lease)

        # Determine command type from oneof.
        cmd = request.command
        cmd_type = "unknown"
        is_mobility = True

        if cmd.HasField("full_body_command"):
            fb = cmd.full_body_command
            if fb.HasField("stop_request"):
                cmd_type = "stop"
                is_mobility = False
            elif fb.HasField("selfright_request"):
                cmd_type = "selfright"
                is_mobility = False
            elif fb.HasField("safe_power_off_request"):
                cmd_type = "safe_power_off"
                is_mobility = False
            elif fb.HasField("freeze_request"):
                cmd_type = "freeze"
                is_mobility = False
            else:
                cmd_type = "full_body_other"
        elif cmd.HasField("synchronized_command"):
            sc = cmd.synchronized_command
            if sc.HasField("mobility_command"):
                mc = sc.mobility_command
                if mc.HasField("stand_request"):
                    cmd_type = "stand"
                elif mc.HasField("sit_request"):
                    cmd_type = "sit"
                elif mc.HasField("se2_velocity_request"):
                    cmd_type = "velocity"
                elif mc.HasField("se2_trajectory_request"):
                    cmd_type = "trajectory"
                elif mc.HasField("stop_request"):
                    cmd_type = "stop"
                else:
                    cmd_type = "mobility_other"

        # Validate: for mobility commands, motors must be ON.
        with ROBOT_STATE.lock:
            ROBOT_STATE.settle_power_state()
            if is_mobility and cmd_type in (
                "stand",
                "sit",
                "velocity",
                "trajectory",
            ):
                if ROBOT_STATE.motor_power_state != ROBOT_STATE.MOTOR_ON:
                    response.status = robot_command_pb2.RobotCommandResponse.STATUS_NOT_POWERED_ON
                    response.message = "motors not on"
                    response.robot_command_id = 0
                    return response

            cid = ROBOT_STATE.new_command_id()
            ROBOT_STATE.commands[cid] = CommandRecord(
                command_id=cid,
                command_type=cmd_type,
                issued_ns=time.time_ns(),
                is_mobility=is_mobility,
                completed=False,
            )

            # Apply effects on state immediately for simplicity.
            if cmd_type == "stand":
                ROBOT_STATE.stand_state = "stand"
                ROBOT_STATE.body_height = 0.50
            elif cmd_type == "sit":
                ROBOT_STATE.stand_state = "sit"
                ROBOT_STATE.body_height = 0.20
            elif cmd_type == "safe_power_off":
                ROBOT_STATE.stand_state = "sit"
                ROBOT_STATE.motor_power_state = ROBOT_STATE.MOTOR_OFF
            elif cmd_type == "trajectory":
                # Parse goal pose from the final trajectory point.
                traj = cmd.synchronized_command.mobility_command.se2_trajectory_request.trajectory
                if traj.points:
                    last = traj.points[-1]
                    ROBOT_STATE.start_locomotion(
                        last.pose.position.x,
                        last.pose.position.y,
                        last.pose.angle,
                    )

        response.status = robot_command_pb2.RobotCommandResponse.STATUS_OK
        response.robot_command_id = cid
        return response

    def RobotCommandFeedback(self, request, context):
        response = robot_command_pb2.RobotCommandFeedbackResponse()
        fill_response_header(response, request)

        cid = request.robot_command_id
        with ROBOT_STATE.lock:
            ROBOT_STATE.settle_power_state()
            rec = ROBOT_STATE.commands.get(cid)
            if rec is None:
                # Unknown command id - return processing status as a fallback.
                fb = response.feedback
                fb.synchronized_feedback.SetInParent()
                return response
            elapsed = (time.time_ns() - rec.issued_ns) / 1e9
            fb = response.feedback

            if rec.command_type == "stand":
                msg = fb.synchronized_feedback.mobility_command_feedback
                msg.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                sf = msg.stand_feedback
                sf.status = basic_command_pb2.StandCommand.Feedback.STATUS_IS_STANDING
                sf.standing_state = basic_command_pb2.StandCommand.Feedback.STANDING_CONTROLLED
            elif rec.command_type == "sit":
                msg = fb.synchronized_feedback.mobility_command_feedback
                msg.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                msg.sit_feedback.status = basic_command_pb2.SitCommand.Feedback.STATUS_IS_SITTING
            elif rec.command_type == "velocity":
                msg = fb.synchronized_feedback.mobility_command_feedback
                msg.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                # SE2VelocityCommand.Feedback has no status field, so just leave it set in parent.
                msg.se2_velocity_feedback.SetInParent()
            elif rec.command_type == "trajectory":
                msg = fb.synchronized_feedback.mobility_command_feedback
                msg.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                t = msg.se2_trajectory_feedback
                if ROBOT_STATE.locomotion_target_m is None:
                    t.status = basic_command_pb2.SE2TrajectoryCommand.Feedback.STATUS_AT_GOAL
                    t.body_movement_status = (
                        basic_command_pb2.SE2TrajectoryCommand.Feedback.BODY_STATUS_SETTLED
                    )
                else:
                    t.status = (
                        basic_command_pb2.SE2TrajectoryCommand.Feedback.STATUS_GOING_TO_GOAL
                    )
                    t.body_movement_status = (
                        basic_command_pb2.SE2TrajectoryCommand.Feedback.BODY_STATUS_MOVING
                    )
                t.final_goal_status = (
                    basic_command_pb2.SE2TrajectoryCommand.Feedback.FINAL_GOAL_STATUS_ACHIEVABLE
                )
            elif rec.command_type == "selfright":
                fbm = fb.full_body_feedback
                fbm.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                fbm.selfright_feedback.status = (
                    basic_command_pb2.SelfRightCommand.Feedback.STATUS_COMPLETED
                )
            elif rec.command_type == "safe_power_off":
                fbm = fb.full_body_feedback
                fbm.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                fbm.safe_power_off_feedback.status = (
                    basic_command_pb2.SafePowerOffCommand.Feedback.STATUS_POWERED_OFF
                )
            elif rec.command_type == "stop":
                if rec.is_mobility:
                    msg = fb.synchronized_feedback.mobility_command_feedback
                    msg.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                    msg.stop_feedback.SetInParent()
                else:
                    fbm = fb.full_body_feedback
                    fbm.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                    fbm.stop_feedback.SetInParent()
            elif rec.command_type == "freeze":
                fbm = fb.full_body_feedback
                fbm.status = basic_command_pb2.RobotCommandFeedbackStatus.STATUS_PROCESSING
                fbm.freeze_feedback.SetInParent()
            else:
                fb.synchronized_feedback.SetInParent()
        return response

    def ClearBehaviorFault(self, request, context):
        response = robot_command_pb2.ClearBehaviorFaultResponse()
        fill_response_header(response, request)
        response.status = robot_command_pb2.ClearBehaviorFaultResponse.STATUS_NOT_CLEARED
        return response
