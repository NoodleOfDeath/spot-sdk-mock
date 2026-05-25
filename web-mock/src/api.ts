export const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:3001").replace(/\/$/, "");

export type TestEntry = { id: string; file: string; name: string };

export type RobotState = {
  power_state: string;
  estop_cut: boolean;
  stand_state: string;
  battery_pct: number;
};

export async function fetchTests(): Promise<TestEntry[]> {
  const res = await fetch(`${API_BASE}/api/tests`);
  if (!res.ok) throw new Error(`tests: ${res.status}`);
  return res.json();
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
