/**
 * SE2 ground-plane body pose: ``x``/``y`` in metres, ``heading`` in radians
 * about the world Z axis.
 */
export interface BodyPoseSE2 {
  x: number;
  y: number;
  heading: number;
}

/**
 * Snapshot of mock-robot state returned by ``GET /api/robot/state``.
 *
 * @example {
 *   "power_state": "OFF",
 *   "estop_cut": false,
 *   "stand_state": "sitting",
 *   "battery_pct": 80,
 *   "mission_state": "IDLE",
 *   "body_pose_se2": { "x": 0, "y": 0, "heading": 0 },
 *   "locomotion_target_m": null,
 *   "locomotion_elapsed_ms": 0,
 *   "gait_cycles": 0
 * }
 */
export interface RobotStateSummary {
  /** Motor power state (``OFF`` / ``ON`` / ``POWERING_ON`` / ``POWERING_OFF`` / ``ERROR``). */
  power_state: string;
  /** ``true`` if any registered EStop endpoint is in the cut/stopped state. */
  estop_cut: boolean;
  /** Crude inference: ``sitting`` when motors off, ``standing`` when on. */
  stand_state: string;
  /** Battery charge percentage (0–100). */
  battery_pct: number;
  /** Mission lifecycle: ``IDLE`` / ``PLAYING`` / ``PAUSED``. */
  mission_state: "IDLE" | "PLAYING" | "PAUSED";
  /** SE2 ground-plane pose of the body in the odom frame. */
  body_pose_se2: BodyPoseSE2;
  /** Distance remaining to walk in metres, or ``null`` if not walking. */
  locomotion_target_m: number | null;
  /** Milliseconds since the current walk began (0 if no walk has been issued). */
  locomotion_elapsed_ms: number;
  /** Trot cycles completed during the current walk (2 Hz). */
  gait_cycles: number;
}

/**
 * Payload for ``POST /api/robot/command`` — kicks off a straight-line walk.
 *
 * @example { "type": "walk", "distance_m": 5.0 }
 */
export interface WalkCommandRequest {
  /** Always ``"walk"`` for now. */
  type: "walk";
  /** Distance to walk forward along +X, in metres. */
  distance_m: number;
}

/**
 * Response from ``POST /api/robot/command``.
 */
export interface WalkCommandResult {
  command_id: number;
  status: string;
}

/**
 * Payload for ``POST /api/robot/power``.
 *
 * @example { "on": true }
 */
export interface PowerCommandRequest {
  /** ``true`` powers on motors, ``false`` powers them off. */
  on: boolean;
}

/**
 * Response from ``POST /api/robot/power``.
 */
export interface PowerCommandResult {
  power_command_id: number;
  status: string;
}
