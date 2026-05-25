import { spawn, ChildProcess } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import type { Request, Response } from "express";
import type { TestEntry } from "../models/TestManifest";

const PROJECT_ROOT = process.env.PROJECT_ROOT ?? "/app";
const MANIFEST_PATH =
  process.env.MANIFEST_PATH ?? "/app/.test_manifest.json";

export class TestRunnerService {
  static loadManifest(): TestEntry[] {
    if (!existsSync(MANIFEST_PATH)) return [];
    try {
      return JSON.parse(readFileSync(MANIFEST_PATH, "utf-8"));
    } catch {
      return [];
    }
  }

  static streamPytest(
    req: Request,
    res: Response,
    args: string[],
    preamble: string
  ): void {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders?.();

    const send = (line: string) => {
      res.write(`data: ${line.replace(/\n+$/, "")}\n\n`);
    };

    send(preamble);

    const child: ChildProcess = spawn(
      "pytest",
      [...args, "-v", "-s", "-p", "no:cacheprovider", "--mock"],
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
    child.stdout?.on("data", onData);
    child.stderr?.on("data", onData);

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
    void req;
  }
}
