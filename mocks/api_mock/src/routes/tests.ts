import { Router } from "express";
import { spawn } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";

export const testsRouter = Router();

type TestEntry = {
  id: string;
  file: string;
  name: string;
  suite: string;
};

const PROJECT_ROOT = process.env.PROJECT_ROOT ?? "/app";
const MANIFEST_PATH =
  process.env.MANIFEST_PATH ?? "/app/.test_manifest.json";

function loadManifest(): TestEntry[] {
  if (!existsSync(MANIFEST_PATH)) return [];
  try {
    return JSON.parse(readFileSync(MANIFEST_PATH, "utf-8"));
  } catch {
    return [];
  }
}

testsRouter.get("/tests", (_req, res) => {
  res.json(loadManifest());
});

testsRouter.post("/tests/run", (req, res) => {
  const testId: string | undefined = req.body?.test;
  const manifest = loadManifest();
  const entry = manifest.find((t) => t.id === testId);
  if (!entry) {
    res.status(404).json({ error: `unknown test: ${testId}` });
    return;
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  const send = (line: string) => {
    res.write(`data: ${line.replace(/\n+$/, "")}\n\n`);
  };

  const target = `${entry.file}::${entry.name}`;
  send(`>> pytest ${target} -v -s --mock`);

  const child = spawn(
    "pytest",
    [
      `${entry.file}::${entry.name}`,
      "-v",
      "-s",
      "-p",
      "no:cacheprovider",
      "--mock",
    ],
    {
      // Project root holds the conftest.py + pytest.ini that register --mock.
      cwd: PROJECT_ROOT,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        PYTHONDONTWRITEBYTECODE: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  child.on("error", (err) => {
    send(`!! spawn error: ${err.message}`);
  });

  let buf = "";
  const onData = (chunk: Buffer) => {
    buf += chunk.toString();
    let idx;
    while ((idx = buf.indexOf("\n")) !== -1) {
      const line = buf.slice(0, idx);
      buf = buf.slice(idx + 1);
      send(line);
    }
  };
  child.stdout.on("data", onData);
  child.stderr.on("data", onData);

  let finished = false;
  child.on("close", (code) => {
    if (finished) return;
    finished = true;
    if (buf.length) send(buf);
    res.write(`data: ${JSON.stringify({ exit_code: code ?? -1 })}\n\n`);
    res.end();
  });

  res.on("close", () => {
    finished = true;
    if (!child.killed) child.kill("SIGTERM");
  });
});

testsRouter.post("/tests/run-all", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  const send = (line: string) => {
    res.write(`data: ${line.replace(/\n+$/, "")}\n\n`);
  };

  const targets = [
    "robot_mock/tests/",
    "vendor/spot-sdk/python/bosdyn-client/tests/",
    "vendor/spot-sdk/python/bosdyn-mission/tests/",
  ];
  send(`>> pytest ${targets.join(" ")} -v -s --mock`);

  const child = spawn(
    "pytest",
    [...targets, "-v", "-s", "-p", "no:cacheprovider", "--mock"],
    {
      cwd: PROJECT_ROOT,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        PYTHONDONTWRITEBYTECODE: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  child.on("error", (err) => {
    send(`!! spawn error: ${err.message}`);
  });

  let buf = "";
  const onData = (chunk: Buffer) => {
    buf += chunk.toString();
    let idx;
    while ((idx = buf.indexOf("\n")) !== -1) {
      const line = buf.slice(0, idx);
      buf = buf.slice(idx + 1);
      send(line);
    }
  };
  child.stdout.on("data", onData);
  child.stderr.on("data", onData);

  let finished = false;
  child.on("close", (code) => {
    if (finished) return;
    finished = true;
    if (buf.length) send(buf);
    res.write(`data: ${JSON.stringify({ exit_code: code ?? -1 })}\n\n`);
    res.end();
  });

  res.on("close", () => {
    finished = true;
    if (!child.killed) child.kill("SIGTERM");
  });
  void req; // unused but kept for parity
});
