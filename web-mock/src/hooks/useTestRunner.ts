import { useCallback, useRef, useState } from "react";
import { API_BASE } from "../api.js";

export type Runner = {
  running: boolean;
  lines: string[];
  exitCode: number | null;
  run: (id: string) => void;
};

export function useTestRunner(): Runner {
  const [running, setRunning] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  const [exitCode, setExitCode] = useState<number | null>(null);
  const ctrl = useRef<AbortController | null>(null);

  const run = useCallback((id: string) => {
    if (ctrl.current) ctrl.current.abort();
    const ac = new AbortController();
    ctrl.current = ac;
    setLines([]);
    setExitCode(null);
    setRunning(true);

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/tests/run`, {
          method: "POST",
          headers: { "content-type": "application/json", accept: "text/event-stream" },
          body: JSON.stringify({ test: id }),
          signal: ac.signal,
        });
        if (!res.ok || !res.body) {
          setLines((p) => [...p, `error: HTTP ${res.status}`]);
          setRunning(false);
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buf.indexOf("\n\n")) !== -1) {
            const chunk = buf.slice(0, idx);
            buf = buf.slice(idx + 2);
            const line = chunk.replace(/^data:\s?/, "");
            if (line.startsWith("{") && line.includes("exit_code")) {
              try {
                const parsed = JSON.parse(line);
                setExitCode(parsed.exit_code);
              } catch {
                /* ignore */
              }
            } else if (line.length > 0) {
              setLines((p) => [...p, line]);
            }
          }
        }
      } catch (e: unknown) {
        if ((e as { name?: string })?.name !== "AbortError") {
          setLines((p) => [...p, `stream error: ${(e as Error).message ?? String(e)}`]);
        }
      } finally {
        setRunning(false);
      }
    })();
  }, []);

  return { running, lines, exitCode, run };
}
