import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { fetchTests, type TestEntry, type TestManifest } from "../api.js";

type TestsState = {
  /** Flattened ``local + vendor`` list (preserved for legacy consumers). */
  items: TestEntry[];
  local: TestEntry[];
  vendor: TestEntry[];
  loading: boolean;
  error: string | null;
};

const initialState: TestsState = {
  items: [],
  local: [],
  vendor: [],
  loading: false,
  error: null,
};

const loadTests = createAsyncThunk<TestManifest>("tests/load", async () =>
  fetchTests()
);

const slice = createSlice({
  name: "tests",
  initialState,
  reducers: {},
  extraReducers: (b) => {
    b.addCase(loadTests.pending, (s) => {
      s.loading = true;
      s.error = null;
    });
    b.addCase(loadTests.fulfilled, (s, a) => {
      s.loading = false;
      s.local = a.payload.local;
      s.vendor = a.payload.vendor;
      s.items = [...a.payload.local, ...a.payload.vendor];
    });
    b.addCase(loadTests.rejected, (s, a) => {
      s.loading = false;
      s.error = a.error.message ?? "load failed";
    });
  },
});

export const testsReducer = slice.reducer;
export const testsThunks = { loadTests };
