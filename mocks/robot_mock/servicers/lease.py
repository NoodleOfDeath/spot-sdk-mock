"""LeaseService implementation."""
from __future__ import annotations

import time

from bosdyn.api import lease_pb2, lease_service_pb2_grpc

from ..state import ROBOT_STATE
from ._header import fill_response_header


def _copy_lease(record, lease_proto):
    lease_proto.resource = record.resource
    lease_proto.epoch = record.epoch
    del lease_proto.sequence[:]
    lease_proto.sequence.extend(record.sequence)
    del lease_proto.client_names[:]
    lease_proto.client_names.extend(record.client_names)


def _copy_owner(record, owner_proto):
    owner_proto.client_name = record.owner_client_name
    owner_proto.user_name = record.owner_user_name


def _check_lease(req_lease) -> int:
    """Return a LeaseUseResult.Status given a request's lease proto."""
    if not req_lease.resource:
        return lease_pb2.LeaseUseResult.STATUS_UNMANAGED
    with ROBOT_STATE.lock:
        record = ROBOT_STATE.leases.get(req_lease.resource)
        if record is None:
            return lease_pb2.LeaseUseResult.STATUS_INVALID_LEASE
        if req_lease.epoch and req_lease.epoch != record.epoch:
            return lease_pb2.LeaseUseResult.STATUS_WRONG_EPOCH
        # Anything from current owner is OK for the mock.
        return lease_pb2.LeaseUseResult.STATUS_OK


def fill_lease_use_result(result, req_lease):
    status = _check_lease(req_lease)
    result.status = status
    if req_lease and req_lease.resource:
        result.attempted_lease.CopyFrom(req_lease)
        with ROBOT_STATE.lock:
            rec = ROBOT_STATE.leases.get(req_lease.resource)
            if rec is not None:
                _copy_lease(rec, result.latest_known_lease)
                _copy_owner(rec, result.owner)


class LeaseServicer(lease_service_pb2_grpc.LeaseServiceServicer):
    def AcquireLease(self, request, context):
        response = lease_pb2.AcquireLeaseResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            rec = ROBOT_STATE.leases.get(request.resource)
            if rec is None:
                response.status = lease_pb2.AcquireLeaseResponse.STATUS_INVALID_RESOURCE
                return response
            if rec.owner_client_name and rec.owner_client_name != _peer_client_name(context):
                # In the mock, allow re-acquisition for tests. Reset sequence.
                pass
            rec.sequence = [rec.sequence[0] + 1] if rec.sequence else [1]
            rec.client_names = [_peer_client_name(context)]
            rec.owner_client_name = _peer_client_name(context)
            rec.owner_user_name = "mock-user"
            rec.last_retain_ns = time.time_ns()
            _copy_lease(rec, response.lease)
            _copy_owner(rec, response.lease_owner)
            response.status = lease_pb2.AcquireLeaseResponse.STATUS_OK
        return response

    def TakeLease(self, request, context):
        response = lease_pb2.TakeLeaseResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            rec = ROBOT_STATE.leases.get(request.resource)
            if rec is None:
                response.status = lease_pb2.TakeLeaseResponse.STATUS_INVALID_RESOURCE
                return response
            rec.sequence = [rec.sequence[0] + 1] if rec.sequence else [1]
            rec.client_names = [_peer_client_name(context)]
            rec.owner_client_name = _peer_client_name(context)
            rec.owner_user_name = "mock-user"
            rec.last_retain_ns = time.time_ns()
            _copy_lease(rec, response.lease)
            _copy_owner(rec, response.lease_owner)
            response.status = lease_pb2.TakeLeaseResponse.STATUS_OK
        return response

    def ReturnLease(self, request, context):
        response = lease_pb2.ReturnLeaseResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            rec = ROBOT_STATE.leases.get(request.lease.resource)
            if rec is None:
                response.status = lease_pb2.ReturnLeaseResponse.STATUS_INVALID_RESOURCE
                return response
            # Clear ownership
            rec.client_names = []
            rec.owner_client_name = ""
            rec.owner_user_name = ""
            response.status = lease_pb2.ReturnLeaseResponse.STATUS_OK
        return response

    def ListLeases(self, request, context):
        response = lease_pb2.ListLeasesResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            for rec in ROBOT_STATE.leases.values():
                lr = response.resources.add()
                lr.resource = rec.resource
                _copy_lease(rec, lr.lease)
                _copy_owner(rec, lr.lease_owner)
                lr.is_stale = False
            # Build a simple tree: body has mobility & gripper as sub-resources.
            tree = response.resource_tree
            tree.resource = "body"
            for sub in ("mobility", "gripper", "arm", "full-arm"):
                if sub in ROBOT_STATE.leases:
                    sub_node = tree.sub_resources.add()
                    sub_node.resource = sub
        return response

    def RetainLease(self, request, context):
        response = lease_pb2.RetainLeaseResponse()
        fill_response_header(response, request)
        with ROBOT_STATE.lock:
            rec = ROBOT_STATE.leases.get(request.lease.resource)
            if rec is None:
                response.lease_use_result.status = lease_pb2.LeaseUseResult.STATUS_INVALID_LEASE
                return response
            rec.last_retain_ns = time.time_ns()
        fill_lease_use_result(response.lease_use_result, request.lease)
        return response


def _peer_client_name(context) -> str:
    """Extract a stable identifier for the calling client."""
    try:
        return context.peer() or "mock-client"
    except Exception:
        return "mock-client"
