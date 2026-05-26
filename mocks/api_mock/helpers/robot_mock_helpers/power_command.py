"""Issue a PowerCommand to robot_mock — REQUEST_ON_MOTORS / REQUEST_OFF_MOTORS."""
from __future__ import annotations

import json
import os
import sys

import grpc
from bosdyn.api import power_pb2, power_service_pb2_grpc


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: power_command.py <on|off>", file=sys.stderr)
        return 1
    arg = sys.argv[1].lower()
    if arg not in ("on", "off"):
        print(f"unknown power state: {arg}", file=sys.stderr)
        return 1

    host = os.environ.get("ROBOT_MOCK_HOST", "robot_mock")
    port = int(os.environ.get("ROBOT_MOCK_PORT", "44444"))
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = power_service_pb2_grpc.PowerServiceStub(channel)

    req = power_pb2.PowerCommandRequest()
    req.header.client_name = "api_mock-power_command"
    req.header.request_timestamp.GetCurrentTime()
    req.request = (
        power_pb2.PowerCommandRequest.REQUEST_ON_MOTORS
        if arg == "on"
        else power_pb2.PowerCommandRequest.REQUEST_OFF_MOTORS
    )
    resp = stub.PowerCommand(req, timeout=4.0)
    status_field = resp.DESCRIPTOR.fields_by_name["status"]
    status_name = status_field.enum_type.values_by_number[resp.status].name
    json.dump(
        {
            "power_command_id": int(resp.power_command_id),
            "status": status_name,
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
