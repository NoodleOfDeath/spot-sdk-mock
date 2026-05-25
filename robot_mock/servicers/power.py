"""PowerService implementation."""
from __future__ import annotations

import time

from bosdyn.api import power_pb2, power_service_pb2_grpc, robot_state_pb2

from ..state import ROBOT_STATE, PowerCommandRecord
from ._header import fill_response_header
from .lease import fill_lease_use_result


# Time it takes to traverse a power transition. Kept short for tests.
POWER_TRANSITION_SEC = 0.5


class PowerServicer(power_service_pb2_grpc.PowerServiceServicer):
    def PowerCommand(self, request, context):
        response = power_pb2.PowerCommandResponse()
        fill_response_header(response, request)
        fill_lease_use_result(response.lease_use_result, request.lease)

        with ROBOT_STATE.lock:
            ROBOT_STATE.settle_power_state()
            req = request.request
            now_ns = time.time_ns()

            if req == power_pb2.PowerCommandRequest.REQUEST_ON_MOTORS:
                if ROBOT_STATE.is_estop_cut():
                    response.status = power_pb2.STATUS_ESTOPPED
                    response.power_command_id = 0
                    return response
                if ROBOT_STATE.motor_power_state == ROBOT_STATE.MOTOR_ON:
                    # Already on - synthesize a completed command id.
                    cid = ROBOT_STATE.new_power_command_id()
                    ROBOT_STATE.power_commands[cid] = PowerCommandRecord(
                        power_command_id=cid,
                        request=req,
                        started_ns=now_ns - int(POWER_TRANSITION_SEC * 1e9 * 2),
                        target_state=ROBOT_STATE.MOTOR_ON,
                        transitional_state=ROBOT_STATE.MOTOR_POWERING_ON,
                        duration_sec=POWER_TRANSITION_SEC,
                    )
                    response.power_command_id = cid
                    response.status = power_pb2.STATUS_SUCCESS
                    return response
                # Start transition OFF -> POWERING_ON -> ON
                ROBOT_STATE.motor_power_state = ROBOT_STATE.MOTOR_POWERING_ON
                cid = ROBOT_STATE.new_power_command_id()
                ROBOT_STATE.power_commands[cid] = PowerCommandRecord(
                    power_command_id=cid,
                    request=req,
                    started_ns=now_ns,
                    target_state=ROBOT_STATE.MOTOR_ON,
                    transitional_state=ROBOT_STATE.MOTOR_POWERING_ON,
                    duration_sec=POWER_TRANSITION_SEC,
                )
                ROBOT_STATE._power_transition_target = ROBOT_STATE.power_commands[cid]
                response.power_command_id = cid
                response.status = power_pb2.STATUS_IN_PROGRESS
                return response

            if req == power_pb2.PowerCommandRequest.REQUEST_OFF_MOTORS:
                if ROBOT_STATE.motor_power_state == ROBOT_STATE.MOTOR_OFF:
                    cid = ROBOT_STATE.new_power_command_id()
                    ROBOT_STATE.power_commands[cid] = PowerCommandRecord(
                        power_command_id=cid,
                        request=req,
                        started_ns=now_ns - int(POWER_TRANSITION_SEC * 1e9 * 2),
                        target_state=ROBOT_STATE.MOTOR_OFF,
                        transitional_state=ROBOT_STATE.MOTOR_POWERING_OFF,
                        duration_sec=POWER_TRANSITION_SEC,
                    )
                    response.power_command_id = cid
                    response.status = power_pb2.STATUS_SUCCESS
                    return response
                ROBOT_STATE.motor_power_state = ROBOT_STATE.MOTOR_POWERING_OFF
                cid = ROBOT_STATE.new_power_command_id()
                ROBOT_STATE.power_commands[cid] = PowerCommandRecord(
                    power_command_id=cid,
                    request=req,
                    started_ns=now_ns,
                    target_state=ROBOT_STATE.MOTOR_OFF,
                    transitional_state=ROBOT_STATE.MOTOR_POWERING_OFF,
                    duration_sec=POWER_TRANSITION_SEC,
                )
                ROBOT_STATE._power_transition_target = ROBOT_STATE.power_commands[cid]
                # If sitting/standing - reset to sit on power off
                ROBOT_STATE.stand_state = "sit"
                response.power_command_id = cid
                response.status = power_pb2.STATUS_IN_PROGRESS
                return response

            response.status = power_pb2.STATUS_SUCCESS
            response.power_command_id = ROBOT_STATE.new_power_command_id()
            return response

    def PowerCommandFeedback(self, request, context):
        response = power_pb2.PowerCommandFeedbackResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            ROBOT_STATE.settle_power_state()
            rec = ROBOT_STATE.power_commands.get(request.power_command_id)
            if rec is None:
                response.status = power_pb2.STATUS_INTERNAL_ERROR
                return response
            if ROBOT_STATE._power_transition_target is rec:
                response.status = power_pb2.STATUS_IN_PROGRESS
            elif ROBOT_STATE.motor_power_state == rec.target_state:
                response.status = power_pb2.STATUS_SUCCESS
            else:
                response.status = power_pb2.STATUS_IN_PROGRESS
        return response

    def FanPowerCommand(self, request, context):
        # Not used by typical SDK clients; provide a minimal stub.
        from bosdyn.api import power_pb2 as p
        response = p.FanPowerCommandResponse()
        fill_response_header(response, request)
        return response

    def FanPowerCommandFeedback(self, request, context):
        from bosdyn.api import power_pb2 as p
        response = p.FanPowerCommandFeedbackResponse()
        fill_response_header(response, request)
        return response

    def GetFanInformation(self, request, context):
        from bosdyn.api import power_pb2 as p
        response = p.GetFanInformationResponse()
        fill_response_header(response, request)
        return response

    def ResetSafetyStop(self, request, context):
        from bosdyn.api import power_pb2 as p
        response = p.ResetSafetyStopResponse()
        fill_response_header(response, request)
        return response
