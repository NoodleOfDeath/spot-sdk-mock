"""Shared, thread-safe robot state for the mock Spot server."""
from __future__ import annotations

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

    def new_command_id(self) -> int:
        self._next_command_id += 1
        return self._next_command_id

    def new_power_command_id(self) -> int:
        self._next_power_command_id += 1
        return self._next_power_command_id


# Module-level singleton used by all servicers
ROBOT_STATE = RobotState()
