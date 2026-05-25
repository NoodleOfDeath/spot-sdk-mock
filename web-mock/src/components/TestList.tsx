import { useEffect, useState } from "react";
import { fetchTests, type TestEntry } from "../api.js";

type Props = {
  onRun: (id: string) => void;
  runningId: string | null;
};

export function TestList({ onRun, runningId }: Props) {
  const [tests, setTests] = useState<TestEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTests()
      .then(setTests)
      .catch((e) => setError(e.message ?? String(e)));
  }, []);

  if (error) {
    return <p style={{ color: "var(--red)" }}>Failed to load tests: {error}</p>;
  }
  if (tests.length === 0) {
    return <p style={{ color: "var(--muted)" }}>Loading tests…</p>;
  }

  return (
    <div className="test-list" data-testid="test-list">
      {tests.map((t) => (
        <div className="test-card" key={t.id} data-testid="test-card">
          <span title={t.id}>{t.name}</span>
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
