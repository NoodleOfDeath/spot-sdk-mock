import { test, expect } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";
import crypto from "node:crypto";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";
const API_URL = process.env.API_URL ?? "http://localhost:3001";
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const FRAMES_DIR = path.join(REPO_ROOT, "assets", "frames");

function sha256File(p: string): string {
  return crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
}

test.use({ viewport: { width: 1280, height: 800 } });

test("Walk 5m end-to-end measurement", async ({ page, request }) => {
  test.setTimeout(45_000);
  fs.mkdirSync(FRAMES_DIR, { recursive: true });

  await page.goto(WEB_URL);
  await expect(page).toHaveTitle(/Spot Mock/i);

  // Open the Walk tab.
  await page.getByTestId("tab-walk").click();
  const walk = page.getByTestId("walk-animation");
  await expect(walk).toBeVisible();
  const canvas = walk.locator("canvas");
  await expect(canvas).toBeVisible();

  // Wait for window.__spotX / __spotScale to be exposed by the animation loop.
  await expect
    .poll(async () => await page.evaluate(() => typeof window.__spotScale))
    .toBe("number");

  // Wait for the GUI's first poll (and one render frame after) so that
  // window.__spotX reflects the API-reported body_pose_se2.x. Without
  // this, initialX is read while stateRef is still null and reports 0.
  const apiStartState = await (
    await request.get(`${API_URL}/api/robot/state`)
  ).json();
  const apiStartX = apiStartState.body_pose_se2.x as number;
  await expect
    .poll(
      async () => {
        const scale = (await page.evaluate(() => window.__spotScale)) as number;
        const x = (await page.evaluate(() => window.__spotX)) as number;
        return Math.abs(x - apiStartX * scale) < 0.01;
      },
      { timeout: 5_000 }
    )
    .toBe(true);

  const initialX = (await page.evaluate(
    () => window.__spotX
  )) as number;
  const scale = (await page.evaluate(
    () => window.__spotScale
  )) as number;
  expect(scale).toBeGreaterThan(0);

  // Pre-walk screenshot of the canvas only.
  const startPath = path.join(FRAMES_DIR, "walk_start.png");
  await canvas.screenshot({ path: startPath });
  const startHash = sha256File(startPath);

  // Kick off a 5m walk.
  const startMs = Date.now();
  const cmdRes = await request.post(`${API_URL}/api/robot/command`, {
    data: { type: "walk", distance_m: 5.0 },
  });
  expect(cmdRes.ok()).toBeTruthy();

  // Poll the state endpoint until locomotion_target_m clears (≤ 12 s).
  let lastState: any = null;
  const pollDeadline = Date.now() + 12_000;
  while (Date.now() < pollDeadline) {
    const r = await request.get(`${API_URL}/api/robot/state`);
    if (r.ok()) {
      lastState = await r.json();
      if (lastState.locomotion_target_m === null) break;
    }
    await page.waitForTimeout(200);
  }
  expect(lastState).not.toBeNull();
  expect(lastState.locomotion_target_m).toBeNull();
  const elapsed = Date.now() - startMs;
  const gaitCycles = lastState.gait_cycles as number;

  // Give one render frame for the GUI to apply the final position.
  await page.waitForTimeout(150);
  const finalX = (await page.evaluate(() => window.__spotX)) as number;
  const movedMeters = (finalX - initialX) / scale;
  expect(Math.abs(movedMeters - 5.0)).toBeLessThan(0.1);

  // Gait cycles: 5m at 1m/s = 5s, 2Hz = 10 cycles; allow 1 missed.
  expect(gaitCycles).toBeGreaterThanOrEqual(9);

  // "Legs frozen" — model is translation-only in POC, so position should
  // remain stable for 500 ms after the walk completes.
  const xA = (await page.evaluate(() => window.__spotX)) as number;
  await page.waitForTimeout(500);
  const xB = (await page.evaluate(() => window.__spotX)) as number;
  expect(Math.abs(xB - xA)).toBeLessThan(0.001);

  // Post-walk screenshot of the same canvas clip.
  const endPath = path.join(FRAMES_DIR, "walk_end.png");
  await canvas.screenshot({ path: endPath });
  const endHash = sha256File(endPath);
  expect(startHash).not.toBe(endHash);

  console.log(
    `WALK CONFIRMED: 5.0m in ${elapsed}ms, ${gaitCycles} gait cycles`
  );
  console.log(`POSITION CONFIRMED: x=${finalX.toFixed(2)}`);
  console.log(
    `HASH CONFIRMED: start != end (${startHash.slice(0, 8)}… → ${endHash.slice(
      0,
      8
    )}…)`
  );
});
