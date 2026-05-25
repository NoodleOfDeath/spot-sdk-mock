import { useEffect, useRef, useState } from "react";
import { TestList } from "./components/TestList.js";
import { ConsoleOutput } from "./components/ConsoleOutput.js";
import { RobotViewer } from "./components/RobotViewer.js";
import { StateLegend } from "./components/StateLegend.js";
import { HeaderLinks } from "./components/HeaderLinks.js";
import { MissionPanel } from "./components/MissionPanel.js";
import { Splitter } from "./components/Splitter.js";
import { thunks, useAppDispatch, useAppSelector } from "./store/index.js";

const STORAGE_KEY = "spot-mock:panel-sizes:v1";

type Sizes = { left: number; viewer: number };

function loadSizes(): Sizes {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<Sizes>;
      return {
        left: typeof parsed.left === "number" ? parsed.left : 360,
        viewer: typeof parsed.viewer === "number" ? parsed.viewer : 460,
      };
    }
  } catch {
    /* ignore */
  }
  return { left: 360, viewer: 460 };
}

function saveSizes(s: Sizes) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {
    /* ignore */
  }
}

export function App() {
  const dispatch = useAppDispatch();
  const activeTestId = useAppSelector((s) => s.ui.activeTestId);
  const tests = useAppSelector((s) => s.tests.items);
  const [sizes, setSizes] = useState<Sizes>(() => loadSizes());
  const sizesRef = useRef(sizes);
  sizesRef.current = sizes;

  useEffect(() => {
    dispatch(thunks.loadTests());
    dispatch(thunks.pollRobot());
    const robotPoll = setInterval(() => dispatch(thunks.pollRobot()), 500);
    return () => clearInterval(robotPoll);
  }, [dispatch]);

  useEffect(() => {
    saveSizes(sizes);
  }, [sizes]);

  const activeTest = tests.find((t) => t.id === activeTestId) ?? null;
  const showMissionPanel = activeTest?.suite === "mission";

  return (
    <>
      <header>
        <h1>Spot Mock — SDK Test Console</h1>
        <span className="badge">stack: robot_mock + api_mock + web_mock</span>
        <HeaderLinks />
      </header>
      <main
        className="resizable"
        style={{ gridTemplateColumns: `${sizes.left}px 4px 1fr` }}
      >
        <div className="col">
          <div
            className="panel test-list-panel"
            style={{ flex: 1, display: "flex", flexDirection: "column" }}
          >
            <TestList />
          </div>
        </div>
        <Splitter
          direction="vertical"
          testId="splitter-left"
          min={200}
          max={700}
          getSize={() => sizesRef.current.left}
          onSize={(v) => setSizes((s) => ({ ...s, left: v }))}
        />
        <div
          className="col"
          style={{
            display: "grid",
            gridTemplateRows: `${sizes.viewer}px 4px 1fr`,
            gap: 0,
            minHeight: 0,
          }}
        >
          <div className="panel viewer-panel" style={{ minHeight: 0 }}>
            <div
              className="viewer"
              data-testid="viewer-container"
              style={{ height: `calc(${sizes.viewer}px - 200px)` }}
            >
              <RobotViewer />
            </div>
            <StateLegend />
          </div>
          <Splitter
            direction="horizontal"
            testId="splitter-right"
            min={180}
            max={900}
            getSize={() => sizesRef.current.viewer}
            onSize={(v) => setSizes((s) => ({ ...s, viewer: v }))}
          />
          <div
            className="panel"
            style={{ display: "flex", flexDirection: "column", minHeight: 0 }}
          >
            {showMissionPanel ? (
              <>
                <h2>Mission Controls</h2>
                <MissionPanel />
                <div style={{ height: 8 }} />
              </>
            ) : null}
            <h2>Console {activeTestId ? `— ${activeTestId}` : ""}</h2>
            <ConsoleOutput />
          </div>
        </div>
      </main>
    </>
  );
}
