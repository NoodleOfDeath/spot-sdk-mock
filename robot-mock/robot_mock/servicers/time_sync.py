"""TimeSyncService implementation - reaches STATUS_OK on the first valid round trip."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Optional

from bosdyn.api import time_sync_pb2, time_sync_service_pb2_grpc

from ._header import fill_response_header


class TimeSyncServicer(time_sync_service_pb2_grpc.TimeSyncServiceServicer):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # round-trip counter per clock_identifier
        self._rounds = {}

    def _now_ts(self):
        from google.protobuf.timestamp_pb2 import Timestamp
        ts = Timestamp()
        ts.GetCurrentTime()
        return ts

    def TimeSyncUpdate(self, request, context):
        response = time_sync_pb2.TimeSyncUpdateResponse()
        fill_response_header(response, request)

        with self._lock:
            clock_id = request.clock_identifier
            if not clock_id:
                clock_id = "mock-clock-" + uuid.uuid4().hex[:8]
                self._rounds[clock_id] = 0
            else:
                self._rounds.setdefault(clock_id, 0)
            self._rounds[clock_id] += 1
            rounds_done = self._rounds[clock_id]

        response.clock_identifier = clock_id

        state = response.state
        # Use server response timestamps for measurement
        meas = self._now_ts()
        state.measurement_time.CopyFrom(meas)

        if rounds_done < 2 or not request.HasField("previous_round_trip"):
            # First request: need more samples
            state.status = time_sync_pb2.TimeSyncState.STATUS_MORE_SAMPLES_NEEDED
            return response

        # We have a previous round trip — declare sync OK with near-zero skew.
        state.status = time_sync_pb2.TimeSyncState.STATUS_OK
        # round_trip_time and clock_skew are google.protobuf.Duration
        state.best_estimate.round_trip_time.seconds = 0
        state.best_estimate.round_trip_time.nanos = 1_000_000  # 1 ms
        state.best_estimate.clock_skew.seconds = 0
        state.best_estimate.clock_skew.nanos = 0
        return response
