import { test, expect } from "@playwright/test";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";
const API_URL = process.env.API_URL ?? "http://localhost:3001";

test.use({ viewport: { width: 1400, height: 900 } });

test("Power-gated walk, legend layout, toast on failure", async ({
  page,
  request,
}) => {
  test.setTimeout(60_000);

  // Ensure robot starts powered off so the test is deterministic.
  await request.post(`${API_URL}/api/robot/power`, { data: { on: false } });
  // Walk back to origin if needed (only effective when motors are on; we
  // ignore failures here).
  for (let i = 0; i < 30; i++) {
    const s = await (await request.get(`${API_URL}/api/robot/state`)).json();
    if (
      s.power_state.replace(/^STATE_/, "") === "OFF" &&
      s.locomotion_target_m === null
    ) {
      break;
    }
    await new Promise((r) => setTimeout(r, 200));
  }

  await page.goto(WEB_URL);
  await expect(page).toHaveTitle(/Spot Mock/i);

  // 1. Legend is to the right of the canvas + has overflow-y: auto.
  const viewer = page.getByTestId("viewer-container");
  const legend = page.getByTestId("state-legend");
  await expect(viewer).toBeVisible();
  await expect(legend).toBeVisible();
  const vBox = await viewer.boundingBox();
  const lBox = await legend.boundingBox();
  expect(vBox && lBox).toBeTruthy();
  expect(lBox!.x).toBeGreaterThan(vBox!.x + vBox!.width - 5);
  const overflowY = await legend.evaluate(
    (el) => getComputedStyle(el as HTMLElement).overflowY
  );
  expect(overflowY).toBe("auto");

  // 2. "Power On" button visible; robot at rest.
  const powerBtn = page.getByTestId("power-button");
  await expect(powerBtn).toBeVisible();
  await expect(powerBtn).toHaveText(/Power On/i);

  // 3. Walk command while off → 400 with {error: "robot not powered on"}.
  const offRes = await request.post(`${API_URL}/api/robot/command`, {
    data: { type: "walk", distance_m: 5.0 },
  });
  expect(offRes.status()).toBe(400);
  const offBody = await offRes.json();
  expect(offBody.error).toMatch(/not powered on/i);

  // 4. Click "Power On"; wait for button to become "Power Off" (≤ 5 s).
  await powerBtn.click();
  await expect(powerBtn).toHaveText(/Power Off/i, { timeout: 5_000 });

  // Let the GUI catch up so window.__spotX reflects the robot's pose.
  await expect
    .poll(async () => await page.evaluate(() => typeof window.__spotScale))
    .toBe("number");
  const apiStart = await (
    await request.get(`${API_URL}/api/robot/state`)
  ).json();
  const apiStartX = apiStart.body_pose_se2.x as number;
  await expect
    .poll(
      async () => {
        const scale = (await page.evaluate(() => window.__spotScale)) as number;
        const x = (await page.evaluate(() => window.__spotX)) as number;
        return Math.abs(x - apiStartX * scale) < 0.05;
      },
      { timeout: 5_000 }
    )
    .toBe(true);

  const initialX = (await page.evaluate(() => window.__spotX)) as number;
  const scale = (await page.evaluate(() => window.__spotScale)) as number;
  expect(scale).toBeGreaterThan(0);

  // 5. Issue the walk; poll until complete.
  const onRes = await request.post(`${API_URL}/api/robot/command`, {
    data: { type: "walk", distance_m: 5.0 },
  });
  expect(onRes.ok()).toBeTruthy();

  const deadline = Date.now() + 12_000;
  let last: { locomotion_target_m: number | null } | null = null;
  while (Date.now() < deadline) {
    const r = await request.get(`${API_URL}/api/robot/state`);
    if (r.ok()) {
      last = await r.json();
      if (last && last.locomotion_target_m === null) break;
    }
    await page.waitForTimeout(200);
  }
  expect(last?.locomotion_target_m).toBeNull();
  await page.waitForTimeout(200);

  // 6. window.__spotX moved by 5.0 * scale (±0.1).
  const finalX = (await page.evaluate(() => window.__spotX)) as number;
  const movedMeters = (finalX - initialX) / scale;
  expect(Math.abs(movedMeters - 5.0)).toBeLessThan(0.1);

  // 7. Click "Power Off"; assert button reverts to "Power On".
  await powerBtn.click();
  await expect(powerBtn).toHaveText(/Power On/i, { timeout: 5_000 });
});
