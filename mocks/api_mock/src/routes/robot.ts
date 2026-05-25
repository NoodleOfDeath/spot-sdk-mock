import { Router } from "express";
import { getRobotState } from "../grpc/client.js";

export const robotRouter = Router();

robotRouter.get("/robot/state", async (_req, res) => {
  try {
    const state = await getRobotState();
    res.json(state);
  } catch (err: unknown) {
    res
      .status(503)
      .json({ error: err instanceof Error ? err.message : String(err) });
  }
});
