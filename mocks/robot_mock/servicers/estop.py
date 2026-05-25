"""EstopService implementation."""
from __future__ import annotations

import time
import uuid

from bosdyn.api import estop_pb2, estop_service_pb2_grpc

from ..state import ROBOT_STATE, EstopEndpointRecord
from ._header import fill_response_header


class EstopServicer(estop_service_pb2_grpc.EstopServiceServicer):
    def SetEstopConfig(self, request, context):
        response = estop_pb2.SetEstopConfigResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            # Replace endpoints from the new config.
            ROBOT_STATE.estop_endpoints.clear()
            new_id = "mock-config-" + uuid.uuid4().hex[:8]
            ROBOT_STATE.estop_config_id = new_id
            for ep in request.config.endpoints:
                ROBOT_STATE.estop_endpoints[ep.unique_id or ep.name] = EstopEndpointRecord(
                    role=ep.role,
                    name=ep.name,
                    unique_id=ep.unique_id or ep.name,
                    timeout_sec=ep.timeout.seconds + ep.timeout.nanos / 1e9,
                )
            response.active_config.CopyFrom(request.config)
            response.active_config.unique_id = new_id
            response.status = estop_pb2.SetEstopConfigResponse.STATUS_SUCCESS
        return response

    def GetEstopConfig(self, request, context):
        response = estop_pb2.GetEstopConfigResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            response.active_config.unique_id = ROBOT_STATE.estop_config_id
            for rec in ROBOT_STATE.estop_endpoints.values():
                ep = response.active_config.endpoints.add()
                ep.role = rec.role
                ep.name = rec.name
                ep.unique_id = rec.unique_id
                ep.timeout.seconds = int(rec.timeout_sec)
                ep.timeout.nanos = int((rec.timeout_sec - int(rec.timeout_sec)) * 1e9)
        return response

    def RegisterEstopEndpoint(self, request, context):
        response = estop_pb2.RegisterEstopEndpointResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            new = request.new_endpoint
            uid = new.unique_id or "mock-ep-" + uuid.uuid4().hex[:8]
            ROBOT_STATE.estop_endpoints[uid] = EstopEndpointRecord(
                role=new.role,
                name=new.name,
                unique_id=uid,
                timeout_sec=new.timeout.seconds + new.timeout.nanos / 1e9 or 1.0,
            )
            response.new_endpoint.CopyFrom(new)
            response.new_endpoint.unique_id = uid
            response.status = estop_pb2.RegisterEstopEndpointResponse.STATUS_SUCCESS
        return response

    def DeregisterEstopEndpoint(self, request, context):
        response = estop_pb2.DeregisterEstopEndpointResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            uid = request.target_endpoint.unique_id or request.target_endpoint.name
            ROBOT_STATE.estop_endpoints.pop(uid, None)
            response.status = estop_pb2.DeregisterEstopEndpointResponse.STATUS_SUCCESS
        return response

    def EstopCheckIn(self, request, context):
        response = estop_pb2.EstopCheckInResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            uid = request.endpoint.unique_id or request.endpoint.name
            rec = ROBOT_STATE.estop_endpoints.get(uid)
            if rec is None:
                response.status = estop_pb2.EstopCheckInResponse.STATUS_ENDPOINT_UNKNOWN
                response.challenge = 0
                return response
            # Validate challenge/response if a previous challenge was issued.
            if rec.challenge and request.challenge != rec.challenge:
                # First check-in often has challenge==0; tolerate that.
                if request.challenge != 0:
                    response.status = estop_pb2.EstopCheckInResponse.STATUS_INCORRECT_CHALLENGE_RESPONSE
                    response.challenge = rec.challenge
                    return response
            rec.last_checkin_ns = time.time_ns()
            rec.stop_level = request.stop_level or estop_pb2.ESTOP_LEVEL_NONE
            # Issue a new challenge (just an incrementing counter).
            rec.challenge = (rec.challenge + 1) & 0xFFFFFFFF or 1
            response.challenge = rec.challenge
            response.status = estop_pb2.EstopCheckInResponse.STATUS_OK
        return response

    def GetEstopSystemStatus(self, request, context):
        response = estop_pb2.GetEstopSystemStatusResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            status = response.status
            min_level = estop_pb2.ESTOP_LEVEL_NONE
            for rec in ROBOT_STATE.estop_endpoints.values():
                eps = status.endpoints.add()
                eps.endpoint.role = rec.role
                eps.endpoint.name = rec.name
                eps.endpoint.unique_id = rec.unique_id
                eps.endpoint.timeout.seconds = int(rec.timeout_sec)
                lvl = rec.stop_level or estop_pb2.ESTOP_LEVEL_NONE
                eps.stop_level = lvl
                if lvl < min_level and lvl != 0:
                    min_level = lvl
            status.stop_level = min_level
            status.stop_level_details = "mock estop status"
        return response
