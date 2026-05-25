/**
 * Snapshot of mock-robot state returned by ``GET /api/robot/state``.
 *
 * @example {
 *   "power_state": "OFF",
 *   "estop_cut": false,
 *   "stand_state": "sitting",
 *   "battery_pct": 80,
 *   "mission_state": "IDLE"
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
}
