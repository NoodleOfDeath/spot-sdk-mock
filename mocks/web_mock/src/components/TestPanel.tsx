import { useMemo, useState } from "react";
import type { TestEntry, TestSource } from "../api.js";
import { thunks, useAppDispatch, useAppSelector } from "../store/index.js";
import { setActiveTestId } from "../store/uiSlice.js";

interface TestPanelProps {
  title: string;
  source: TestSource;
  tests: TestEntry[];
  height: number;
  searchLabel: string;
  runAllTestId: string;
  searchTestId: string;
  panelTestId: string;
}

/**
 * Single section panel: title + count, scoped Run-All button, search filter
 * and a scrollable list of test cards clipped to ``height`` px.
 */
export function TestPanel({
  title,
  source,
  tests,
  height,
  searchLabel,
  runAllTestId,
  searchTestId,
  panelTestId,
}: TestPanelProps) {
  const dispatch = useAppDispatch();
  const [filter, setFilter] = useState("");
  const runningId = useAppSelector((s) =>
    s.runner.running ? s.runner.activeId : null
  );

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return tests;
    return tests.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.id.toLowerCase().includes(q) ||
        t.file.toLowerCase().includes(q)
    );
  }, [filter, tests]);

  const runAllTag = `__all_${source}__`;
  const runAllBusy = runningId === runAllTag;
  const hasFilter = filter.trim().length > 0;
  const total = tests.length;
  const shownCount = filtered.length;

  const onRunAll = () => {
    dispatch(setActiveTestId(runAllTag));
    dispatch(
      thunks.runAll({ source, filter: hasFilter ? filter.trim() : null })
    );
  };

  const onRun = (id: string) => {
    dispatch(setActiveTestId(id));
    dispatch(thunks.runTest(id));
  };

  const runAllLabel = runAllBusy
    ? "Running…"
    : hasFilter
      ? `▶▶ Run Filtered ${shownCount} Tests`
      : `▶▶ Run All ${total} Tests`;

  return (
    <section
      className="test-panel"
      data-testid={panelTestId}
      data-source={source}
      style={{ height: `${height}px` }}
    >
      <header className="test-panel-header">
        <h2>
          {title} <span className="count-badge">{total}</span>
        </h2>
        <button
          type="button"
          className="run-all"
          data-testid={runAllTestId}
          disabled={runAllBusy || shownCount === 0}
          onClick={onRunAll}
        >
          {runAllLabel}
        </button>
        <input
          type="search"
          className="test-search"
          placeholder="Filter…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label={searchLabel}
          data-testid={searchTestId}
        />
      </header>
      <div className="test-list" data-testid={`${panelTestId}-list`}>
        {filtered.length === 0 ? (
          <p className="muted">
            {total === 0 ? "No tests found." : "No matches."}
          </p>
        ) : (
          filtered.map((t) => (
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
          ))
        )}
      </div>
    </section>
  );
}
