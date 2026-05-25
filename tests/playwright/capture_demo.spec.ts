// Choreographed walkthrough of the GUI — saves screenshots into
// ``assets/frames/`` for ``scripts/make_gif.py`` to stitch into
// ``assets/demo.gif``. Intentionally written as a Playwright spec so we
// can lean on the existing runner (no ts-node dep) — invoke with:
//
//   npx playwright test capture_demo.spec.ts
//
// The stack must already be running (docker compose up).
import { test, expect, Page } from "@playwright/test";
import { mkdirSync, readdirSync, unlinkSync, existsSync } from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const FRAMES_DIR = path.join(REPO_ROOT, "assets", "frames");
const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";
const API_BASE = process.env.API_BASE ?? "http://localhost:3001";

let frameIdx = 0;

async function shot(page: Page, label: string) {
  frameIdx += 1;
  const seq = String(frameIdx).padStart(3, "0");
  const fname = `frame_${seq}_${label}.png`;
  await page.screenshot({ path: path.join(FRAMES_DIR, fname), fullPage: false });
}

test.use({ viewport: { width: 1280, height: 720 } });

test("capture choreographed demo", async ({ page, request }) => {
  test.setTimeout(180_000);

  // Health check.
  const h = await request.get(`${API_BASE}/api/health`);
  if (!h.ok()) throw new Error(`api_mock not reachable: ${h.status()}`);

  mkdirSync(FRAMES_DIR, { recursive: true });
  // Clean previous frames.
  if (existsSync(FRAMES_DIR)) {
    for (const f of readdirSync(FRAMES_DIR)) {
      if (f.endsWith(".png")) unlinkSync(path.join(FRAMES_DIR, f));
    }
  }
  frameIdx = 0;

  await page.goto(WEB_URL);
  await expect(page.getByTestId("test-card").first()).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByTestId("robot-viewer")).toBeVisible();
  // 1. initial
  await shot(page, "01_initial");

  // 2-3. Drag the left/right splitter to give the console more room, then back.
  const splitter = page.getByTestId("splitter-left");
  const box = await splitter.boundingBox();
  if (!box) throw new Error("splitter not found");
  const startX = box.x + box.width / 2;
  const startY = box.y + box.height / 2;

  await page.mouse.move(startX, startY);
  await page.mouse.down();
  for (let i = 1; i <= 6; i++) {
    await page.mouse.move(startX - i * 25, startY);
  }
  await page.mouse.up();
  await page.waitForTimeout(120);
  await shot(page, "02_panel_drag");

  await page.mouse.move(startX - 150, startY);
  await page.mouse.down();
  for (let i = 1; i <= 6; i++) {
    await page.mouse.move(startX - 150 + i * 25, startY);
  }
  await page.mouse.up();
  await page.waitForTimeout(120);
  await shot(page, "03_panel_reset");

  // 4. Click ▶ Run on the first test card.
  const firstRun = page.getByTestId("test-card").first().getByTestId("run-button");
  await firstRun.click();
  await page.waitForTimeout(150);
  await shot(page, "04_test_started");

  const console_ = page.getByTestId("console-output");

  // 5. wait for ≥3 lines of streaming output.
  await expect(async () => {
    const text = (await console_.innerText()).trim();
    const lines = text.split("\n").filter((l) => l.trim().length > 0);
    expect(lines.length).toBeGreaterThanOrEqual(3);
  }).toPass({ timeout: 30_000 });
  await shot(page, "05_console_streaming");

  // 6. wait for PASSED.
  await expect(async () => {
    const text = await console_.innerText();
    expect(text).toMatch(/PASS(ED)?/i);
  }).toPass({ timeout: 30_000 });
  await shot(page, "06_test_passed");

  // 7. Walk tab.
  await page.getByTestId("tab-walk").click();
  await page.waitForTimeout(250);
  await shot(page, "07_walk_tab");

  // 8. To get the Mission Panel, run a mission test first.
  // Then click Play Mission, expect badge = PLAYING.
  const missionCard = page.locator('[data-testid="test-card"]', {
    hasText: "🎯 test_simple",
  });
  await missionCard.getByTestId("run-button").click();
  await expect(page.getByTestId("mission-panel")).toBeVisible({
    timeout: 15_000,
  });
  await page.getByTestId("mission-play").click();
  await expect(page.getByTestId("mission-state-badge")).toHaveText("PLAYING", {
    timeout: 10_000,
  });
  await shot(page, "08_mission_playing");

  // 9. Camera rotate — switch back to State tab (RobotViewer canvas), drag.
  await page.getByTestId("tab-state").click();
  await page.waitForTimeout(200);
  const viewer = page.getByTestId("robot-viewer");
  const vbox = await viewer.boundingBox();
  if (!vbox) throw new Error("robot-viewer not found");
  const cx = vbox.x + vbox.width / 2;
  const cy = vbox.y + vbox.height / 2;
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  for (let i = 1; i <= 10; i++) {
    await page.mouse.move(cx + i * 20, cy - i * 8);
    await page.waitForTimeout(40);
    await shot(page, `09_rotate_${String(i).padStart(2, "0")}`);
  }
  await page.mouse.up();

  // 10. Pause mission.
  await page.getByTestId("mission-pause").click();
  await expect(page.getByTestId("mission-state-badge")).toHaveText("PAUSED", {
    timeout: 10_000,
  });
  await shot(page, "10_mission_paused");

  // 11. Run all.
  await page.getByTestId("run-all-button").click();
  await page.waitForTimeout(2000);
  await shot(page, "11_run_all_started");

  // 12. Final wide shot.
  await page.waitForTimeout(400);
  await shot(page, "12_final");

  console.log(`captured ${frameIdx} frames at ${FRAMES_DIR}`);
});
