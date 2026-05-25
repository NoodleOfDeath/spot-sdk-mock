import { test, expect } from "@playwright/test";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";
const API_URL = process.env.API_URL ?? "http://localhost:3001";

test.use({ viewport: { width: 1400, height: 900 } });

test("Header links, no Walk/State tabs, StateLegend live-updates on walk", async ({
  page,
  request,
}) => {
  test.setTimeout(45_000);

  await page.goto(WEB_URL);
  await expect(page).toHaveTitle(/Spot Mock/i);

  // 1. GitHub link visible top-right with proper aria-label.
  const github = page.getByLabel("GitHub source");
  await expect(github).toBeVisible();

  // 2. API Docs link points at localhost:3001/api/docs.
  const docs = page.getByLabel("API Docs");
  await expect(docs).toBeVisible();
  const docsHref = await docs.getAttribute("href");
  expect(docsHref).toContain("localhost:3001/api/docs");

  // 3. No Walk/State tab toggle exists.
  await expect(page.getByTestId("viewer-tabs")).toHaveCount(0);
  await expect(page.getByTestId("tab-state")).toHaveCount(0);
  await expect(page.getByTestId("tab-walk")).toHaveCount(0);

  // 4. StateLegend visible with ≥ 6 rows.
  const legend = page.getByTestId("state-legend");
  await expect(legend).toBeVisible();
  await expect
    .poll(async () => await legend.locator("tbody > tr").count())
    .toBeGreaterThanOrEqual(6);

  // Wait for window.__spotX / __spotScale and ensure the GUI has caught
  // up with whatever pose robot_mock currently reports.
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

  // 5. Trigger a 5 m walk; poll the API until locomotion_target_m clears.
  const cmdRes = await request.post(`${API_URL}/api/robot/command`, {
    data: { type: "walk", distance_m: 5.0 },
  });
  expect(cmdRes.ok()).toBeTruthy();

  // 7a. Locomotion row should reflect the in-flight walk at some point.
  const locRow = page.getByTestId("legend-row-locomotion");
  await expect(locRow).toBeVisible();
  await expect
    .poll(
      async () => (await locRow.innerText()).toLowerCase(),
      { timeout: 6_000 }
    )
    .toMatch(/of\s+5\.00m/);

  // Poll until the walk completes.
  const pollDeadline = Date.now() + 12_000;
  let lastState: { locomotion_target_m: number | null } | null = null;
  while (Date.now() < pollDeadline) {
    const r = await request.get(`${API_URL}/api/robot/state`);
    if (r.ok()) {
      lastState = await r.json();
      if (lastState && lastState.locomotion_target_m === null) break;
    }
    await page.waitForTimeout(200);
  }
  expect(lastState?.locomotion_target_m).toBeNull();

  // Let one render frame settle so window.__spotX has the final value.
  await page.waitForTimeout(200);

  // 6. window.__spotX moved by 5.0 * window.__spotScale (±0.1).
  const finalX = (await page.evaluate(() => window.__spotX)) as number;
  const movedMeters = (finalX - initialX) / scale;
  expect(Math.abs(movedMeters - 5.0)).toBeLessThan(0.1);

  // 7b. Locomotion row clears to "—" after completion.
  await expect
    .poll(
      async () => (await locRow.innerText()).trim(),
      { timeout: 4_000 }
    )
    .toMatch(/—/);
});
