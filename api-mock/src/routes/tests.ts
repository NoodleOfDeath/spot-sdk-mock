import { Router } from "express";
import { spawn } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

export const testsRouter = Router();

type TestEntry = { id: string; file: string; name: string };

const SDK_TESTS_DIR =
  process.env.SDK_TESTS_DIR ?? "/app/robot_mock/tests/sdk";
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
  const child = spawn(
    "pytest",
    [join(SDK_TESTS_DIR, entry.file) + `::${entry.name}`, "-v", "-s", "--mock"],
    {
      cwd: "/app",
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    }
  );

  send(`>> pytest ${target} -v -s --mock`);

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

  child.on("close", (code) => {
    if (buf.length) send(buf);
    res.write(`data: ${JSON.stringify({ exit_code: code ?? -1 })}\n\n`);
    res.end();
  });

  req.on("close", () => {
    if (!child.killed) child.kill("SIGTERM");
  });
});
