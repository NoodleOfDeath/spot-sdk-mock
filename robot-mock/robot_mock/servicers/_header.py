"""Common request/response header helpers."""
from __future__ import annotations

import time

from bosdyn.api import header_pb2
from google.protobuf.timestamp_pb2 import Timestamp


def _now_ts() -> Timestamp:
    ts = Timestamp()
    ts.GetCurrentTime()
    return ts


def fill_response_header(response, request) -> None:
    """Populate response.header with OK status and timestamps.

    Mirrors the standard Spot pattern: copies the request header into request_header
    on the response, stamps request_received_timestamp and response_timestamp.
    """
    header = response.header
    if request is not None and request.HasField("header"):
        header.request_header.CopyFrom(request.header)
    now = _now_ts()
    header.request_received_timestamp.CopyFrom(now)
    header.response_timestamp.CopyFrom(now)
    header.error.code = header_pb2.CommonError.CODE_OK
