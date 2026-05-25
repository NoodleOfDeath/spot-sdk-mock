"""Shared, thread-safe robot state for the mock Spot server."""
from __future__ import annotations

import math
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EstopEndpointRecord:
    role: str
    name: str
    unique_id: str
    timeout_sec: float
    last_checkin_ns: int = 0
    stop_level: int = 4  # ESTOP_LEVEL_NONE in EstopStopLevel; 4 = ESTOP_LEVEL_NONE
    challenge: int = 0


@dataclass
class LeaseRecord:
    resource: str
    epoch: str
    sequence: list = field(default_factory=lambda: [0])
    client_names: list = field(default_factory=list)
    owner_client_name: str = ""
    owner_user_name: str = ""
    last_retain_ns: int = 0


@dataclass
class CommandRecord:
    command_id: int
    command_type: str  # 'stand', 'sit', 'selfright', 'stop', 'safe_power_off', 'velocity', 'trajectory'
    issued_ns: int
    is_mobility: bool = True
    completed: bool = False


@dataclass
class BodyPoseSE2:
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0


@dataclass
class PowerCommandRecord:
    power_command_id: int
    request: int  # PowerCommandRequest.Request enum value
    started_ns: int
    target_state: int  # final MotorPowerState
    transitional_state: int  # POWERING_ON/POWERING_OFF
    duration_sec: float = 1.0


class RobotState:
    """Single shared robot state, guarded by an internal lock."""

    # PowerState.MotorPowerState enum values
    MOTOR_OFF = 1            # MOTOR_POWER_STATE_OFF
    MOTOR_ON = 2             # MOTOR_POWER_STATE_ON
    MOTOR_POWERING_ON = 3    # MOTOR_POWER_STATE_POWERING_ON
    MOTOR_POWERING_OFF = 4   # MOTOR_POWER_STATE_POWERING_OFF
    MOTOR_ERROR = 5          # MOTOR_POWER_STATE_ERROR

    def __init__(self) -> None:
        self.lock = threading.RLock()
        # Power
        self.motor_power_state: int = self.MOTOR_OFF
        self._power_transition_target: Optional[PowerCommandRecord] = None
        # Estop
        self.estop_endpoints: Dict[str, EstopEndpointRecord] = {}
        self.estop_config_id: str = "mock-config-" + uuid.uuid4().hex[:8]
        # Lease
        self.lease_epoch: str = "mock-epoch-" + uuid.uuid4().hex[:8]
        self.leases: Dict[str, LeaseRecord] = {
            "body": LeaseRecord(resource="body", epoch=self.lease_epoch),
            "mobility": LeaseRecord(resource="mobility", epoch=self.lease_epoch),
            "gripper": LeaseRecord(resource="gripper", epoch=self.lease_epoch),
            "full-arm": LeaseRecord(resource="full-arm", epoch=self.lease_epoch),
            "arm": LeaseRecord(resource="arm", epoch=self.lease_epoch),
        }
        # Stand/sit state: 'sit' or 'stand'
        self.stand_state: str = "sit"
        # Body pose stub (z height when standing vs sitting)
        self.body_height: float = 0.20
        # SE2 ground-plane pose (x, y in metres; heading in radians about Z).
        self.body_pose_se2: BodyPoseSE2 = BodyPoseSE2()
        # Locomotion (SE2 trajectory) tracking.
        self.locomotion_target_m: Optional[float] = None
        self.locomotion_start_time_ns: Optional[int] = None
        self.gait_cycles: int = 0
        self._locomotion_stop: Optional[threading.Event] = None
        # Commands
        self.commands: Dict[int, CommandRecord] = {}
        self._next_command_id: int = 1000
        self._next_power_command_id: int = 1
        self.power_commands: Dict[int, PowerCommandRecord] = {}
        # Server identity
        self.boot_time_ns: int = time.time_ns()
        # Mission
        self.mission_state: str = "IDLE"  # IDLE / PLAYING / PAUSED
        self.mission_tick: int = 0
        self.mission_id: int = 0
        self.next_question_id: int = 1
        # active question: dict(id, text, options=[{code,text}], answered_code?)
        self.active_question: Optional[dict] = None
        self.answered_questions: list = []

    # ----- Power helpers -----
    def settle_power_state(self) -> None:
        """Advance power transition based on elapsed time. Caller must hold lock."""
        rec = self._power_transition_target
        if rec is None:
            return
        elapsed = (time.time_ns() - rec.started_ns) / 1e9
        if elapsed >= rec.duration_sec:
            self.motor_power_state = rec.target_state
            self._power_transition_target = None

    def is_estop_cut(self) -> bool:
        """True if any registered endpoint reports a non-none stop level, or no endpoints exist *and* the system is in safety mode.

        For the mock we treat 'no endpoints' as 'not cut' so that the SDK can power on
        without any explicit estop registration (matches the SDK's `safe_power_on` flow
        only after an estop endpoint is registered+checked in)."""
        # ESTOP_LEVEL_NONE == 4 (highest numeric value, weakest stop level)
        # ESTOP_LEVEL_CUT == 1
        for ep in self.estop_endpoints.values():
            if ep.stop_level < 4:  # any actual stop
                return True
        return False

    def locomotion_elapsed_ms(self) -> int:
        if self.locomotion_start_time_ns is None:
            return 0
        return int((time.time_ns() - self.locomotion_start_time_ns) / 1e6)

    def start_locomotion(
        self, goal_x: float, goal_y: float, goal_heading: float = 0.0
    ) -> None:
        """Begin a 1.0 m/s straight-line advance toward (goal_x, goal_y).

        Caller must hold ``self.lock``. Cancels any prior locomotion.
        """
        if self._locomotion_stop is not None:
            self._locomotion_stop.set()

        start_x = self.body_pose_se2.x
        start_y = self.body_pose_se2.y
        dx = goal_x - start_x
        dy = goal_y - start_y
        target_m = math.hypot(dx, dy)
        if target_m < 1e-6:
            self.body_pose_se2.heading = goal_heading
            return

        self.locomotion_target_m = target_m
        self.locomotion_start_time_ns = time.time_ns()
        self.gait_cycles = 0

        stop_event = threading.Event()
        self._locomotion_stop = stop_event

        SPEED = 1.0  # m/s
        CYCLES_PER_SEC = 2.0  # 2 Hz trot

        def runner():
            while not stop_event.is_set():
                time.sleep(0.1)
                with self.lock:
                    if (
                        stop_event.is_set()
                        or self.locomotion_start_time_ns is None
                    ):
                        return
                    elapsed = (
                        time.time_ns() - self.locomotion_start_time_ns
                    ) / 1e9
                    travelled = elapsed * SPEED
                    if travelled >= target_m:
                        self.body_pose_se2.x = goal_x
                        self.body_pose_se2.y = goal_y
                        self.body_pose_se2.heading = goal_heading
                        self.gait_cycles = int(elapsed * CYCLES_PER_SEC)
                        self.locomotion_target_m = None
                        return
                    frac = travelled / target_m
                    self.body_pose_se2.x = start_x + dx * frac
                    self.body_pose_se2.y = start_y + dy * frac
                    self.gait_cycles = int(elapsed * CYCLES_PER_SEC)

        threading.Thread(target=runner, daemon=True).start()

    def new_command_id(self) -> int:
        self._next_command_id += 1
        return self._next_command_id

    def new_power_command_id(self) -> int:
        self._next_power_command_id += 1
        return self._next_power_command_id


# Module-level singleton used by all servicers
ROBOT_STATE = RobotState()
