import { spawn } from "node:child_process";

export type RobotStateSummary = {
  power_state: string;
  estop_cut: boolean;
  stand_state: string;
  battery_pct: number;
};

const HOST = process.env.ROBOT_MOCK_HOST ?? "robot_mock";
const PORT = Number(process.env.ROBOT_MOCK_PORT ?? 44444);

export function getRobotState(): Promise<RobotStateSummary> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "python3",
      ["-m", "robot_mock_helpers.get_state"],
      {
        cwd: "/app",
        env: {
          ...process.env,
          PYTHONUNBUFFERED: "1",
          ROBOT_MOCK_HOST: HOST,
          ROBOT_MOCK_PORT: String(PORT),
        },
      }
    );
    let out = "";
    let err = "";
    child.stdout.on("data", (c) => (out += c.toString()));
    child.stderr.on("data", (c) => (err += c.toString()));
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`get_state exited ${code}: ${err.trim() || out.trim()}`));
        return;
      }
      try {
        resolve(JSON.parse(out));
      } catch (e) {
        reject(new Error(`bad JSON from helper: ${out}`));
      }
    });
  });
}
