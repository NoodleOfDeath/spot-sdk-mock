import { Router } from "express";
import { spawn } from "node:child_process";

export const missionRouter = Router();

type Result = { status?: string; mission_state?: string; [k: string]: unknown };

const HOST = process.env.ROBOT_MOCK_HOST ?? "robot_mock";
const PORT = String(process.env.ROBOT_MOCK_PORT ?? "44444");

function runHelper(args: string[]): Promise<Result> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "python3",
      ["-m", "robot_mock_helpers.mission", ...args],
      {
        cwd: "/app",
        env: {
          ...process.env,
          PYTHONUNBUFFERED: "1",
          ROBOT_MOCK_HOST: HOST,
          ROBOT_MOCK_PORT: PORT,
        },
      }
    );
    let out = "";
    let err = "";
    child.stdout.on("data", (c) => (out += c.toString()));
    child.stderr.on("data", (c) => (err += c.toString()));
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`mission helper exited ${code}: ${err.trim() || out}`));
        return;
      }
      try {
        resolve(JSON.parse(out));
      } catch {
        reject(new Error(`bad JSON: ${out}`));
      }
    });
  });
}

missionRouter.post("/mission/play", async (_req, res) => {
  try {
    res.json(await runHelper(["play"]));
  } catch (e) {
    res.status(503).json({ error: (e as Error).message });
  }
});

missionRouter.post("/mission/pause", async (_req, res) => {
  try {
    res.json(await runHelper(["pause"]));
  } catch (e) {
    res.status(503).json({ error: (e as Error).message });
  }
});

missionRouter.post("/mission/restart", async (_req, res) => {
  try {
    res.json(await runHelper(["restart"]));
  } catch (e) {
    res.status(503).json({ error: (e as Error).message });
  }
});

missionRouter.get("/mission/question", async (_req, res) => {
  try {
    res.json(await runHelper(["question"]));
  } catch (e) {
    res.status(503).json({ error: (e as Error).message });
  }
});

missionRouter.post("/mission/answer", async (req, res) => {
  const qid = Number(req.body?.question_id);
  const code = Number(req.body?.answer_code);
  if (!Number.isFinite(qid) || !Number.isFinite(code)) {
    res.status(400).json({ error: "question_id and answer_code are required numbers" });
    return;
  }
  try {
    res.json(await runHelper(["answer", String(qid), String(code)]));
  } catch (e) {
    res.status(503).json({ error: (e as Error).message });
  }
});
