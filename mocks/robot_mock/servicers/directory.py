"""DirectoryService and DirectoryRegistrationService implementations."""
from __future__ import annotations

from typing import Iterable

from bosdyn.api import (
    directory_pb2,
    directory_registration_pb2,
    directory_registration_service_pb2_grpc,
    directory_service_pb2_grpc,
)
from google.protobuf.timestamp_pb2 import Timestamp

from ._header import fill_response_header


# Service catalog: (name, type, authority)
SERVICE_CATALOG = [
    ("robot-id", "bosdyn.api.RobotIdService", "id.spot.robot"),
    ("auth", "bosdyn.api.AuthService", "auth.spot.robot"),
    ("directory", "bosdyn.api.DirectoryService", "api.spot.robot"),
    (
        "directory-registration",
        "bosdyn.api.DirectoryRegistrationService",
        "api.spot.robot",
    ),
    ("time-sync", "bosdyn.api.TimeSyncService", "time-sync.spot.robot"),
    ("estop", "bosdyn.api.EstopService", "estop.spot.robot"),
    ("lease", "bosdyn.api.LeaseService", "lease.spot.robot"),
    ("power", "bosdyn.api.PowerService", "power.spot.robot"),
    ("robot-command", "bosdyn.api.RobotCommandService", "command.spot.robot"),
    ("robot-state", "bosdyn.api.RobotStateService", "state.spot.robot"),
    ("image", "bosdyn.api.ImageService", "image.spot.robot"),
    ("robot-mission", "bosdyn.api.mission.MissionService", "mission.spot.robot"),
]


def _make_entry(name: str, type_: str, authority: str) -> directory_pb2.ServiceEntry:
    e = directory_pb2.ServiceEntry()
    e.name = name
    e.type = type_
    e.authority = authority
    e.user_token_required = name != "auth" and name != "robot-id"
    now = Timestamp()
    now.GetCurrentTime()
    e.last_update.CopyFrom(now)
    return e


class DirectoryServicer(directory_service_pb2_grpc.DirectoryServiceServicer):
    def __init__(self) -> None:
        self._entries = {n: _make_entry(n, t, a) for n, t, a in SERVICE_CATALOG}

    def add_entry(self, name: str, type_: str, authority: str) -> None:
        self._entries[name] = _make_entry(name, type_, authority)

    def ListServiceEntries(self, request, context):
        response = directory_pb2.ListServiceEntriesResponse()
        fill_response_header(response, request)
        for entry in self._entries.values():
            response.service_entries.add().CopyFrom(entry)
        return response

    def GetServiceEntry(self, request, context):
        response = directory_pb2.GetServiceEntryResponse()
        fill_response_header(response, request)
        entry = self._entries.get(request.service_name)
        if entry is None:
            response.status = directory_pb2.GetServiceEntryResponse.STATUS_NONEXISTENT_SERVICE
        else:
            response.status = directory_pb2.GetServiceEntryResponse.STATUS_OK
            response.service_entry.CopyFrom(entry)
        return response


class DirectoryRegistrationServicer(
    directory_registration_service_pb2_grpc.DirectoryRegistrationServiceServicer
):
    """No-op storage: accept everything."""

    def __init__(self, directory: DirectoryServicer) -> None:
        self._directory = directory

    def RegisterService(self, request, context):
        response = directory_registration_pb2.RegisterServiceResponse()
        fill_response_header(response, request)
        # Add to the underlying directory so subsequent lookups succeed.
        entry = request.service_entry
        if entry.name:
            self._directory.add_entry(entry.name, entry.type, entry.authority)
        response.status = directory_registration_pb2.RegisterServiceResponse.STATUS_OK
        return response

    def UnregisterService(self, request, context):
        response = directory_registration_pb2.UnregisterServiceResponse()
        fill_response_header(response, request)
        response.status = directory_registration_pb2.UnregisterServiceResponse.STATUS_OK
        return response

    def UpdateService(self, request, context):
        response = directory_registration_pb2.UpdateServiceResponse()
        fill_response_header(response, request)
        response.status = directory_registration_pb2.UpdateServiceResponse.STATUS_OK
        return response
