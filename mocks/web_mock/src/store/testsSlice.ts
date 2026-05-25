import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { fetchTests, type TestEntry } from "../api.js";

type TestsState = {
  items: TestEntry[];
  loading: boolean;
  error: string | null;
};

const initialState: TestsState = { items: [], loading: false, error: null };

const loadTests = createAsyncThunk("tests/load", async () => fetchTests());

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
      s.items = a.payload;
    });
    b.addCase(loadTests.rejected, (s, a) => {
      s.loading = false;
      s.error = a.error.message ?? "load failed";
    });
  },
});

export const testsReducer = slice.reducer;
export const testsThunks = { loadTests };
