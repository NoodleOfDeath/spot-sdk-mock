export const API_BASE = (
  import.meta.env.VITE_API_BASE ?? "http://localhost:3001"
).replace(/\/$/, "");

export type TestEntry = {
  id: string;
  file: string;
  name: string;
  suite: string;
};

export type TestManifest = {
  local: TestEntry[];
  vendor: TestEntry[];
};

export type TestSource = "local" | "vendor";

export type BodyPoseSE2 = {
  x: number;
  y: number;
  heading: number;
};

export type RobotState = {
  power_state: string;
  estop_cut: boolean;
  stand_state: string;
  battery_pct: number;
  mission_state: "IDLE" | "PLAYING" | "PAUSED";
  body_pose_se2: BodyPoseSE2;
  locomotion_target_m: number | null;
  locomotion_elapsed_ms: number;
  gait_cycles: number;
};

export type MissionQuestion = {
  id: number;
  source: string;
  text: string;
  options: { answer_code: number; text: string }[];
};

export type MissionState = {
  mission_state: "IDLE" | "PLAYING" | "PAUSED";
  questions: MissionQuestion[];
};

export async function fetchTests(): Promise<TestManifest> {
  const res = await fetch(`${API_BASE}/api/tests`);
  if (!res.ok) throw new Error(`tests: ${res.status}`);
  const parsed = await res.json();
  if (Array.isArray(parsed)) {
    // Tolerate the legacy flat-array shape — treat as vendor-only.
    return { local: [], vendor: parsed as TestEntry[] };
  }
  return {
    local: Array.isArray(parsed?.local) ? parsed.local : [],
    vendor: Array.isArray(parsed?.vendor) ? parsed.vendor : [],
  };
}

export async function fetchRobotState(): Promise<RobotState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/robot/state`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function postWalkCommand(distance_m: number): Promise<void> {
  await fetch(`${API_BASE}/api/robot/command`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ type: "walk", distance_m }),
  });
}

export async function postMission(
  action: "play" | "pause" | "restart"
): Promise<void> {
  await fetch(`${API_BASE}/api/mission/${action}`, { method: "POST" });
}

export async function fetchMissionQuestion(): Promise<MissionState | null> {
  try {
    const res = await fetch(`${API_BASE}/api/mission/question`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function answerMissionQuestion(
  question_id: number,
  answer_code: number
): Promise<void> {
  await fetch(`${API_BASE}/api/mission/answer`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question_id, answer_code }),
  });
}
