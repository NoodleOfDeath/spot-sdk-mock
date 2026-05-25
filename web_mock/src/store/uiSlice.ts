import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export type ViewerTab = "state" | "walk";

type UiState = {
  activeTestId: string | null;
  tab: ViewerTab;
};

const initialState: UiState = {
  activeTestId: null,
  tab: "state",
};

const slice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setActiveTestId(state, action: PayloadAction<string | null>) {
      state.activeTestId = action.payload;
    },
    setTab(state, action: PayloadAction<ViewerTab>) {
      state.tab = action.payload;
    },
  },
});

export const { setActiveTestId, setTab } = slice.actions;
export const uiReducer = slice.reducer;
