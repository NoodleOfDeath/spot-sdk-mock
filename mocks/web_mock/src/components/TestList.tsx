import { thunks, useAppDispatch, useAppSelector } from "../store/index.js";
import { setActiveTestId } from "../store/uiSlice.js";

export function TestList() {
  const dispatch = useAppDispatch();
  const tests = useAppSelector((s) => s.tests.items);
  const loading = useAppSelector((s) => s.tests.loading);
  const error = useAppSelector((s) => s.tests.error);
  const runningId = useAppSelector((s) =>
    s.runner.running ? s.runner.activeId : null
  );

  const onRun = (id: string) => {
    dispatch(setActiveTestId(id));
    dispatch(thunks.runTest(id));
  };

  if (error) {
    return <p style={{ color: "var(--red)" }}>Failed to load tests: {error}</p>;
  }
  if (loading && tests.length === 0) {
    return <p style={{ color: "var(--muted)" }}>Loading tests…</p>;
  }
  if (tests.length === 0) {
    return <p style={{ color: "var(--muted)" }}>No tests found.</p>;
  }

  const runAllBusy = runningId === "__all__";

  return (
    <div className="test-list" data-testid="test-list">
      <button
        type="button"
        className="run-all"
        data-testid="run-all-button"
        disabled={runAllBusy}
        onClick={() => {
          dispatch(setActiveTestId("__all__"));
          dispatch(thunks.runAll());
        }}
      >
        {runAllBusy ? "Running all…" : `▶▶ Run all ${tests.length} tests`}
      </button>
      {tests.map((t) => (
        <div className="test-card" key={t.id} data-testid="test-card">
          <span title={t.id}>
            {t.suite === "mission" ? "🎯 " : ""}
            {t.name}
          </span>
          <button
            type="button"
            disabled={runningId === t.id}
            data-testid="run-button"
            onClick={() => onRun(t.id)}
          >
            ▶ Run
          </button>
        </div>
      ))}
    </div>
  );
}
