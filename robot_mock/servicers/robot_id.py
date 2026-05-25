"""RobotIdService implementation."""
from __future__ import annotations

from bosdyn.api import robot_id_pb2, robot_id_service_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp

from ._header import fill_response_header


class RobotIdServicer(robot_id_service_pb2_grpc.RobotIdServiceServicer):
    def GetRobotId(self, request, context):
        response = robot_id_pb2.RobotIdResponse()
        fill_response_header(response, request)
        rid = response.robot_id
        rid.serial_number = "MOCK-0001"
        rid.species = "spot"
        rid.version = "3.0.0"
        rid.nickname = "mock-spot"
        rid.computer_serial_number = "MOCK-COMPUTER-0001"
        # SoftwareRelease
        sw = rid.software_release
        sw.name = "spot"
        sw.type = "RELEASE"
        sw.version.major_version = 5
        sw.version.minor_version = 1
        sw.version.patch_level = 4
        sw.changeset = "mockchangeset"
        sw.api_version = "5.1.4"
        sw.build_information = "mock build"
        now = Timestamp()
        now.GetCurrentTime()
        sw.changeset_date.CopyFrom(now)
        sw.install_date.CopyFrom(now)
        return response
