import { useEffect } from "react";
import { TestList } from "./components/TestList.js";
import { ConsoleOutput } from "./components/ConsoleOutput.js";
import { RobotViewer } from "./components/RobotViewer.js";
import { WalkAnimation } from "./components/WalkAnimation.js";
import { MissionPanel } from "./components/MissionPanel.js";
import { thunks, useAppDispatch, useAppSelector } from "./store/index.js";
import { setTab } from "./store/uiSlice.js";

export function App() {
  const dispatch = useAppDispatch();
  const tab = useAppSelector((s) => s.ui.tab);
  const activeTestId = useAppSelector((s) => s.ui.activeTestId);
  const tests = useAppSelector((s) => s.tests.items);

  useEffect(() => {
    dispatch(thunks.loadTests());
    const robotPoll = setInterval(
      () => dispatch(thunks.pollRobot()),
      2000
    );
    dispatch(thunks.pollRobot());
    return () => clearInterval(robotPoll);
  }, [dispatch]);

  const activeTest = tests.find((t) => t.id === activeTestId) ?? null;
  const showMissionPanel = activeTest?.suite === "mission";

  return (
    <>
      <header>
        <h1>Spot Mock — SDK Test Console</h1>
        <span className="badge">stack: robot_mock + api_mock + web_mock</span>
      </header>
      <main>
        <div className="col">
          <div
            className="panel"
            style={{ flex: 1, display: "flex", flexDirection: "column" }}
          >
            <h2>SDK Tests</h2>
            <TestList />
          </div>
        </div>
        <div className="col">
          <div className="panel">
            <div className="tabs" data-testid="viewer-tabs">
              <button
                type="button"
                className={tab === "state" ? "tab active" : "tab"}
                data-testid="tab-state"
                onClick={() => dispatch(setTab("state"))}
              >
                State
              </button>
              <button
                type="button"
                className={tab === "walk" ? "tab active" : "tab"}
                data-testid="tab-walk"
                onClick={() => dispatch(setTab("walk"))}
              >
                Walk
              </button>
            </div>
            <div className="viewer" data-testid="viewer-container">
              {tab === "state" ? <RobotViewer /> : <WalkAnimation />}
            </div>
          </div>
          {showMissionPanel ? (
            <div className="panel">
              <h2>Mission Controls</h2>
              <MissionPanel />
            </div>
          ) : null}
          <div
            className="panel"
            style={{ flex: 1, display: "flex", flexDirection: "column" }}
          >
            <h2>Console {activeTestId ? `— ${activeTestId}` : ""}</h2>
            <ConsoleOutput />
          </div>
        </div>
      </main>
    </>
  );
}
