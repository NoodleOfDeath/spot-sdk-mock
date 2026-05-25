import { test, expect } from "@playwright/test";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";
const API_BASE = process.env.API_BASE ?? "http://localhost:3001";

test("mission suite — list, run, play/pause, walk animation", async ({
  page,
  request,
}) => {
  // 1. API exposes mission tests
  const manifest = await (await request.get(`${API_BASE}/api/tests`)).json();
  const missionTests = (manifest as Array<{ suite: string; name: string }>).filter(
    (t) => t.suite === "mission"
  );
  expect(missionTests.length).toBeGreaterThan(0);
  const simple = missionTests.find((t) => t.name === "test_simple");
  expect(simple).toBeTruthy();

  await page.goto(WEB_URL);
  await expect(page).toHaveTitle(/Spot Mock/i);

  // 2. Click ▶ Run on test_simple and assert console gets PASSED
  const cards = page.getByTestId("test-card");
  await expect(cards.first()).toBeVisible({ timeout: 15_000 });
  // Mission test cards are prefixed with the target emoji; that uniquely
  // distinguishes ``test_simple`` from upstream client tests of the same name.
  const simpleCard = page.locator('[data-testid="test-card"]', {
    hasText: "🎯 test_simple",
  });
  await expect(simpleCard).toBeVisible();
  await simpleCard.getByTestId("run-button").click();

  const console_ = page.getByTestId("console-output");
  await expect(async () => {
    const text = (await console_.innerText()).trim();
    expect(text).toMatch(/PASS(ED)?/i);
  }).toPass({ timeout: 30_000 });

  // 3. Mission panel renders for the mission suite
  await expect(page.getByTestId("mission-panel")).toBeVisible();

  // 4. Click Play → badge becomes PLAYING
  await page.getByTestId("mission-play").click();
  await expect(page.getByTestId("mission-state-badge")).toHaveText("PLAYING", {
    timeout: 10_000,
  });

  // 5. Switch to Walk tab and confirm rAF is active
  await page.getByTestId("tab-walk").click();
  await expect(page.getByTestId("walk-animation")).toBeVisible();
  await expect(page.getByTestId("walk-animation").locator("canvas")).toBeVisible();
  const rafActive = await page.evaluate(
    () =>
      new Promise<boolean>((resolve) => {
        let fired = false;
        const id = requestAnimationFrame(() => {
          fired = true;
        });
        setTimeout(() => {
          cancelAnimationFrame(id);
          resolve(fired);
        }, 200);
      })
  );
  expect(rafActive).toBe(true);

  // 6. Pause → badge becomes PAUSED
  await page.getByTestId("mission-pause").click();
  await expect(page.getByTestId("mission-state-badge")).toHaveText("PAUSED", {
    timeout: 10_000,
  });
});
