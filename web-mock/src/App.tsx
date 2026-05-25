import { useState } from "react";
import { TestList } from "./components/TestList.js";
import { ConsoleOutput } from "./components/ConsoleOutput.js";
import { RobotViewer } from "./components/RobotViewer.js";
import { useTestRunner } from "./hooks/useTestRunner.js";

export function App() {
  const [activeTestId, setActiveTestId] = useState<string | null>(null);
  const runner = useTestRunner();

  const onRun = (id: string) => {
    setActiveTestId(id);
    runner.run(id);
  };

  return (
    <>
      <header>
        <h1>Spot Mock — SDK Test Console</h1>
        <span className="badge">stack: robot_mock + api_mock + web</span>
      </header>
      <main>
        <div className="col">
          <div className="panel" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <h2>SDK Tests</h2>
            <TestList onRun={onRun} runningId={runner.running ? activeTestId : null} />
          </div>
        </div>
        <div className="col">
          <div className="panel">
            <h2>Robot</h2>
            <div className="viewer">
              <RobotViewer />
            </div>
          </div>
          <div className="panel" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <h2>Console {activeTestId ? `— ${activeTestId}` : ""}</h2>
            <ConsoleOutput lines={runner.lines} exitCode={runner.exitCode} />
          </div>
        </div>
      </main>
    </>
  );
}
