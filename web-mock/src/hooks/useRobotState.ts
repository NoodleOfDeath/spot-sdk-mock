import { useEffect, useState } from "react";
import { fetchRobotState, type RobotState } from "../api.js";

export function useRobotState(intervalMs = 2000): RobotState | null {
  const [state, setState] = useState<RobotState | null>(null);
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      const s = await fetchRobotState();
      if (!cancelled) setState(s);
    };
    tick();
    const handle = setInterval(tick, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(handle);
    };
  }, [intervalMs]);
  return state;
}
