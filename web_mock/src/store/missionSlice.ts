import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import {
  answerMissionQuestion,
  fetchMissionQuestion,
  postMission,
  type MissionState,
} from "../api.js";

type SliceState = {
  current: MissionState | null;
};

const initialState: SliceState = { current: null };

const refreshMission = createAsyncThunk("mission/refresh", async () =>
  fetchMissionQuestion()
);

const playMission = createAsyncThunk("mission/play", async () => {
  await postMission("play");
  return fetchMissionQuestion();
});

const pauseMission = createAsyncThunk("mission/pause", async () => {
  await postMission("pause");
  return fetchMissionQuestion();
});

const restartMission = createAsyncThunk("mission/restart", async () => {
  await postMission("restart");
  return fetchMissionQuestion();
});

const answerQuestion = createAsyncThunk(
  "mission/answer",
  async (args: { question_id: number; answer_code: number }) => {
    await answerMissionQuestion(args.question_id, args.answer_code);
    return fetchMissionQuestion();
  }
);

const slice = createSlice({
  name: "mission",
  initialState,
  reducers: {},
  extraReducers: (b) => {
    for (const t of [
      refreshMission,
      playMission,
      pauseMission,
      restartMission,
      answerQuestion,
    ]) {
      b.addCase(t.fulfilled, (s, a) => {
        s.current = a.payload;
      });
    }
  },
});

export const missionReducer = slice.reducer;
export const missionThunks = {
  refreshMission,
  playMission,
  pauseMission,
  restartMission,
  answerQuestion,
};
