/**
 * One option a mission Question presents to the operator.
 *
 * @example { "answer_code": 1, "text": "Yes — proceed" }
 */
export interface MissionOption {
  answer_code: number;
  text: string;
}

/**
 * An active mission Question awaiting an answer.
 *
 * @example {
 *   "id": 1,
 *   "source": "mock-mission",
 *   "text": "Continue mission to the next waypoint?",
 *   "options": [{ "answer_code": 1, "text": "Yes — proceed" }]
 * }
 */
export interface MissionQuestion {
  id: number;
  source: string;
  text: string;
  options: MissionOption[];
}

/** Snapshot returned by ``GET /api/mission/question``. */
export interface MissionStateSnapshot {
  mission_state: "IDLE" | "PLAYING" | "PAUSED";
  questions: MissionQuestion[];
}

/** Standard response for ``POST /api/mission/play|pause|restart``. */
export interface MissionActionResult {
  /** Mirror of the upstream bosdyn-mission status enum, e.g. ``STATUS_OK``. */
  status: string;
}

/** Body for ``POST /api/mission/answer``. */
export interface MissionAnswerRequest {
  question_id: number;
  answer_code: number;
}

/** Generic error envelope. */
export interface ErrorResponse {
  error: string;
}
