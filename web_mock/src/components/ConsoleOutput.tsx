import { useEffect, useRef } from "react";
import { useAppSelector } from "../store/index.js";

function classify(line: string): string {
  if (/\bPASS(ED)?\b/.test(line)) return "pass";
  if (/\b(FAIL|FAILED|ERROR|Traceback)\b/.test(line)) return "fail";
  if (/^>>|^==/.test(line)) return "muted";
  return "";
}

export function ConsoleOutput() {
  const lines = useAppSelector((s) => s.runner.lines);
  const exitCode = useAppSelector((s) => s.runner.exitCode);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines.length]);

  return (
    <>
      <div className="console" ref={ref} data-testid="console-output">
        {lines.length === 0 ? (
          <span className="line muted">Console idle — click ▶ Run on a test.</span>
        ) : (
          lines.map((l, i) => (
            <div className={`line ${classify(l)}`} key={i}>
              {l}
            </div>
          ))
        )}
      </div>
      {exitCode !== null && (
        <span
          className={`exit ${exitCode === 0 ? "ok" : "err"}`}
          data-testid="exit-badge"
        >
          exit {exitCode}
        </span>
      )}
    </>
  );
}
