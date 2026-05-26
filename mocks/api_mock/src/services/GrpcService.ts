import { spawn } from "node:child_process";
import type {
  PowerCommandResult,
  RobotStateSummary,
  WalkCommandResult,
} from "../models/RobotState";
import type {
  MissionActionResult,
  MissionStateSnapshot,
} from "../models/MissionState";

const HOST = process.env.ROBOT_MOCK_HOST ?? "robot_mock";
const PORT = String(process.env.ROBOT_MOCK_PORT ?? "44444");

/** Generic helper that invokes the Python helper module and parses JSON stdout. */
function runHelper<T>(args: string[]): Promise<T> {
  return new Promise((resolve, reject) => {
    const child = spawn("python3", args, {
      cwd: "/app",
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        ROBOT_MOCK_HOST: HOST,
        ROBOT_MOCK_PORT: PORT,
      },
    });
    let out = "";
    let err = "";
    child.stdout.on("data", (c) => (out += c.toString()));
    child.stderr.on("data", (c) => (err += c.toString()));
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`helper exited ${code}: ${err.trim() || out.trim()}`));
        return;
      }
      try {
        resolve(JSON.parse(out) as T);
      } catch (e) {
        reject(new Error(`bad JSON from helper: ${out}`));
      }
    });
  });
}

export class GrpcService {
  static getRobotState(): Promise<RobotStateSummary> {
    return runHelper<RobotStateSummary>(["-m", "robot_mock_helpers.get_state"]);
  }

  static missionAction(
    action: "play" | "pause" | "restart"
  ): Promise<MissionActionResult> {
    return runHelper<MissionActionResult>([
      "-m",
      "robot_mock_helpers.mission",
      action,
    ]);
  }

  static getMissionQuestion(): Promise<MissionStateSnapshot> {
    return runHelper<MissionStateSnapshot>([
      "-m",
      "robot_mock_helpers.mission",
      "question",
    ]);
  }

  static powerCommand(on: boolean): Promise<PowerCommandResult> {
    return runHelper<PowerCommandResult>([
      "-m",
      "robot_mock_helpers.power_command",
      on ? "on" : "off",
    ]);
  }

  static walkCommand(distance_m: number): Promise<WalkCommandResult> {
    return runHelper<WalkCommandResult>([
      "-m",
      "robot_mock_helpers.walk_command",
      String(distance_m),
    ]);
  }

  static answerMissionQuestion(
    question_id: number,
    answer_code: number
  ): Promise<MissionActionResult> {
    return runHelper<MissionActionResult>([
      "-m",
      "robot_mock_helpers.mission",
      "answer",
      String(question_id),
      String(answer_code),
    ]);
  }
}
