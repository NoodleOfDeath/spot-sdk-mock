import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, useSelector, type TypedUseSelectorHook } from "react-redux";
import { uiReducer } from "./uiSlice.js";
import { testsReducer, testsThunks } from "./testsSlice.js";
import { runnerReducer, runnerThunks } from "./runnerSlice.js";
import { robotReducer, robotThunks } from "./robotSlice.js";
import { missionReducer, missionThunks } from "./missionSlice.js";

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    tests: testsReducer,
    runner: runnerReducer,
    robot: robotReducer,
    mission: missionReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

export const thunks = {
  ...testsThunks,
  ...runnerThunks,
  ...robotThunks,
  ...missionThunks,
};
