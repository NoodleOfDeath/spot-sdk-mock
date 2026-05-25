"""Mock Spot gRPC server entry point.

Run: ``python robot_mock/server.py``

Binds an insecure gRPC server on ``localhost:44444`` (configurable via
``MOCK_ROBOT_PORT``) hosting every base + robot service the Spot SDK
clients call during normal operation.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from concurrent import futures

import grpc

# Ensure package import works regardless of how this file is invoked.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bosdyn.api import (
    auth_service_pb2_grpc,
    directory_registration_service_pb2_grpc,
    directory_service_pb2_grpc,
    estop_service_pb2_grpc,
    image_service_pb2_grpc,
    lease_service_pb2_grpc,
    power_service_pb2_grpc,
    robot_command_service_pb2_grpc,
    robot_id_service_pb2_grpc,
    robot_state_service_pb2_grpc,
    time_sync_service_pb2_grpc,
)

from robot_mock.servicers.auth import AuthServicer
from robot_mock.servicers.directory import (
    DirectoryRegistrationServicer,
    DirectoryServicer,
)
from robot_mock.servicers.estop import EstopServicer
from robot_mock.servicers.image import ImageServicer
from robot_mock.servicers.lease import LeaseServicer
from robot_mock.servicers.power import PowerServicer
from robot_mock.servicers.robot_command import RobotCommandServicer
from robot_mock.servicers.robot_id import RobotIdServicer
from robot_mock.servicers.robot_state import RobotStateServicer
from robot_mock.servicers.time_sync import TimeSyncServicer

DEFAULT_PORT = 44444

logger = logging.getLogger("robot_mock")


def build_server(port: int | None = None) -> tuple[grpc.Server, int]:
    """Build and configure (but do not start) the gRPC server.

    Returns the configured server and the port it will listen on.
    """
    port = port if port is not None else int(os.environ.get("MOCK_ROBOT_PORT", DEFAULT_PORT))
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=16),
        options=[
            ("grpc.max_send_message_length", 100 * 1024 * 1024),
            ("grpc.max_receive_message_length", 100 * 1024 * 1024),
        ],
    )

    directory_servicer = DirectoryServicer()

    robot_id_service_pb2_grpc.add_RobotIdServiceServicer_to_server(RobotIdServicer(), server)
    auth_service_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    directory_service_pb2_grpc.add_DirectoryServiceServicer_to_server(directory_servicer, server)
    directory_registration_service_pb2_grpc.add_DirectoryRegistrationServiceServicer_to_server(
        DirectoryRegistrationServicer(directory_servicer), server
    )
    time_sync_service_pb2_grpc.add_TimeSyncServiceServicer_to_server(TimeSyncServicer(), server)
    estop_service_pb2_grpc.add_EstopServiceServicer_to_server(EstopServicer(), server)
    lease_service_pb2_grpc.add_LeaseServiceServicer_to_server(LeaseServicer(), server)
    power_service_pb2_grpc.add_PowerServiceServicer_to_server(PowerServicer(), server)
    robot_command_service_pb2_grpc.add_RobotCommandServiceServicer_to_server(
        RobotCommandServicer(), server
    )
    robot_state_service_pb2_grpc.add_RobotStateServiceServicer_to_server(
        RobotStateServicer(), server
    )
    image_service_pb2_grpc.add_ImageServiceServicer_to_server(ImageServicer(), server)

    bound_port = server.add_insecure_port(f"[::]:{port}")
    return server, bound_port


def serve(port: int | None = None) -> None:
    server, bound = build_server(port=port)
    server.start()
    logger.info("robot_mock server listening on port %d", bound)

    stop_event = threading.Event()

    def _handle_signal(signum, frame):  # noqa: ARG001
        logger.info("received signal %d; shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    stop_event.wait()
    server.stop(grace=2.0).wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    serve()
