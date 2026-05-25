import { useEffect, useState } from "react";
import { fetchRobotState, type RobotState } from "../api.js";

type Tone = "ok" | "warn" | "bad" | "muted";

interface Row {
  field: string;
  value: string;
  tone: Tone;
}

function powerTone(power: string): Tone {
  if (power === "ON" || power === "STATE_ON") return "ok";
  if (power.includes("POWERING_ON")) return "warn";
  if (power.includes("POWERING_OFF") || power === "ERROR") return "bad";
  return "muted";
}

function powerLabel(power: string): string {
  return power.replace(/^STATE_/, "");
}

function missionTone(state: string): Tone {
  if (state === "PLAYING") return "warn";
  if (state === "PAUSED") return "muted";
  return "muted";
}

function rad2deg(r: number): number {
  return (r * 180) / Math.PI;
}

function buildRows(s: RobotState): Row[] {
  const power = powerLabel(s.power_state);
  const pos = s.body_pose_se2;
  const positionText = `x: ${pos.x.toFixed(2)}m  y: ${pos.y.toFixed(
    2
  )}m  hdg: ${rad2deg(pos.heading).toFixed(1)}°`;
  const locText =
    s.locomotion_target_m == null
      ? "—"
      : `${pos.x.toFixed(2)}m of ${s.locomotion_target_m.toFixed(2)}m`;
  return [
    { field: "Power", value: power, tone: powerTone(s.power_state) },
    {
      field: "EStop",
      value: s.estop_cut ? "CUT" : "CLEAR",
      tone: s.estop_cut ? "bad" : "ok",
    },
    { field: "Lease", value: "body · mobility", tone: "muted" },
    {
      field: "Mission",
      value: s.mission_state,
      tone: missionTone(s.mission_state),
    },
    { field: "Position", value: positionText, tone: "muted" },
    {
      field: "Battery",
      value: `${Math.round(s.battery_pct)}%`,
      tone: s.battery_pct >= 20 ? "ok" : "bad",
    },
    {
      field: "Gait Cycles",
      value: String(s.gait_cycles ?? 0),
      tone: "muted",
    },
    {
      field: "Locomotion",
      value: locText,
      tone: s.locomotion_target_m == null ? "muted" : "warn",
    },
  ];
}

/**
 * Live-updating legend of every field exposed by ``GET /api/robot/state``.
 * Polls every 500 ms so the locomotion row reflects in-flight walks.
 */
export function StateLegend() {
  const [state, setState] = useState<RobotState | null>(null);

  useEffect(() => {
    let cancel = false;
    const tick = async () => {
      if (cancel) return;
      const next = await fetchRobotState();
      if (!cancel && next) setState(next);
    };
    tick();
    const id = setInterval(tick, 500);
    return () => {
      cancel = true;
      clearInterval(id);
    };
  }, []);

  const rows: Row[] = state
    ? buildRows(state)
    : [{ field: "Status", value: "Loading…", tone: "muted" }];

  return (
    <table
      className="state-legend"
      data-testid="state-legend"
      aria-label="Robot state legend"
    >
      <tbody>
        {rows.map((r) => (
          <tr
            key={r.field}
            data-testid={`legend-row-${r.field.toLowerCase().replace(/ /g, "-")}`}
            aria-label={`${r.field}: ${r.value}`}
          >
            <th scope="row">{r.field}</th>
            <td className={`legend-value tone-${r.tone}`}>{r.value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
