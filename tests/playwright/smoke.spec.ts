import { test, expect } from "@playwright/test";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";

test("GUI loads, lists tests, runs one, streams console output", async ({ page }) => {
  await page.goto(WEB_URL);

  await expect(page).toHaveTitle(/Spot Mock/i);

  const cards = page.getByTestId("test-card");
  await expect(cards.first()).toBeVisible({ timeout: 15_000 });
  const count = await cards.count();
  expect(count).toBeGreaterThan(0);

  await expect(page.getByTestId("robot-viewer")).toBeVisible();
  await expect(page.getByTestId("robot-viewer").locator("canvas")).toBeVisible();

  const console_ = page.getByTestId("console-output");
  await expect(console_).toBeVisible();

  await page.getByTestId("run-button").first().click();

  await expect(async () => {
    const text = (await console_.innerText()).trim();
    expect(text.length).toBeGreaterThan(0);
    expect(text).not.toMatch(/Console idle/i);
  }).toPass({ timeout: 30_000 });
});
