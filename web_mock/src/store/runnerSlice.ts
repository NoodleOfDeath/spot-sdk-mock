import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import { API_BASE } from "../api.js";

type RunnerState = {
  running: boolean;
  activeId: string | null;
  lines: string[];
  exitCode: number | null;
};

const initialState: RunnerState = {
  running: false,
  activeId: null,
  lines: [],
  exitCode: null,
};

let currentAbort: AbortController | null = null;

const runTest = createAsyncThunk<void, string>(
  "runner/run",
  async (id, { dispatch }) => {
    if (currentAbort) currentAbort.abort();
    const ac = new AbortController();
    currentAbort = ac;
    dispatch(slice.actions._start(id));
    try {
      const res = await fetch(`${API_BASE}/api/tests/run`, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "text/event-stream" },
        body: JSON.stringify({ test: id }),
        signal: ac.signal,
      });
      if (!res.ok || !res.body) {
        dispatch(slice.actions._appendLine(`error: HTTP ${res.status}`));
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
              dispatch(slice.actions._exit(parsed.exit_code));
            } catch {
              /* ignore */
            }
          } else if (line.length > 0) {
            dispatch(slice.actions._appendLine(line));
          }
        }
      }
    } catch (e: unknown) {
      if ((e as { name?: string })?.name !== "AbortError") {
        dispatch(
          slice.actions._appendLine(`stream error: ${(e as Error).message ?? String(e)}`)
        );
      }
    } finally {
      dispatch(slice.actions._stop());
    }
  }
);

const slice = createSlice({
  name: "runner",
  initialState,
  reducers: {
    _start(state, action: PayloadAction<string>) {
      state.running = true;
      state.activeId = action.payload;
      state.lines = [];
      state.exitCode = null;
    },
    _appendLine(state, action: PayloadAction<string>) {
      state.lines.push(action.payload);
    },
    _exit(state, action: PayloadAction<number>) {
      state.exitCode = action.payload;
    },
    _stop(state) {
      state.running = false;
    },
  },
});

export const runnerReducer = slice.reducer;
export const runnerThunks = { runTest };
