import { useEffect } from "react";
import { thunks, useAppDispatch, useAppSelector } from "../store/index.js";

export function MissionPanel() {
  const dispatch = useAppDispatch();
  const missionState = useAppSelector((s) => s.mission.current);
  const robot = useAppSelector((s) => s.robot.current);

  useEffect(() => {
    dispatch(thunks.refreshMission());
    const handle = setInterval(
      () => dispatch(thunks.refreshMission()),
      1500
    );
    return () => clearInterval(handle);
  }, [dispatch]);

  const stateName =
    missionState?.mission_state ?? robot?.mission_state ?? "IDLE";
  const badgeClass =
    stateName === "PLAYING" ? "ok" : stateName === "PAUSED" ? "muted" : "err";

  return (
    <div
      data-testid="mission-panel"
      style={{ display: "flex", flexDirection: "column", gap: 10 }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <strong>Mission:</strong>
        <span
          className={`exit ${badgeClass}`}
          data-testid="mission-state-badge"
        >
          {stateName}
        </span>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button
          type="button"
          data-testid="mission-play"
          onClick={() => dispatch(thunks.playMission())}
        >
          ▶ Play
        </button>
        <button
          type="button"
          data-testid="mission-pause"
          onClick={() => dispatch(thunks.pauseMission())}
        >
          ⏸ Pause
        </button>
        <button
          type="button"
          data-testid="mission-restart"
          onClick={() => dispatch(thunks.restartMission())}
        >
          ↻ Restart
        </button>
      </div>
      {missionState?.questions?.length ? (
        <div className="panel" style={{ padding: 8 }}>
          {missionState.questions.map((q) => (
            <div key={q.id} data-testid="mission-question">
              <div style={{ marginBottom: 6 }}>{q.text}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {q.options.map((opt) => (
                  <button
                    type="button"
                    key={opt.answer_code}
                    onClick={() =>
                      dispatch(
                        thunks.answerQuestion({
                          question_id: q.id,
                          answer_code: opt.answer_code,
                        })
                      )
                    }
                  >
                    {opt.text}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <span style={{ color: "var(--muted)", fontSize: 12 }}>
          No active mission questions.
        </span>
      )}
    </div>
  );
}
