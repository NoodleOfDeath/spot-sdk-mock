import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { fetchRobotState, type RobotState as RobotStateT } from "../api.js";

type RobotSliceState = {
  current: RobotStateT | null;
};

const initialState: RobotSliceState = { current: null };

const pollRobot = createAsyncThunk("robot/poll", async () => fetchRobotState());

const slice = createSlice({
  name: "robot",
  initialState,
  reducers: {},
  extraReducers: (b) => {
    b.addCase(pollRobot.fulfilled, (s, a) => {
      s.current = a.payload;
    });
  },
});

export const robotReducer = slice.reducer;
export const robotThunks = { pollRobot };
