import { test, expect } from "@playwright/test";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";

test("Run all tests button + point light on the Three.js scene", async ({ page }) => {
  await page.goto(WEB_URL);

  // Test list loads.
  const cards = page.getByTestId("test-card");
  await expect(cards.first()).toBeVisible({ timeout: 20_000 });

  // Point light is present on the RobotViewer mount (set in useEffect).
  await expect(page.getByTestId("robot-viewer")).toBeVisible();
  await expect(page.getByTestId("robot-viewer").locator("canvas")).toBeVisible();
  await expect(page.getByTestId("robot-viewer")).toHaveAttribute(
    "data-point-light",
    "true"
  );

  // Run All button exists and fires an SSE stream.
  const runAll = page.getByTestId("run-all-button");
  await expect(runAll).toBeVisible();
  await runAll.click();

  const console_ = page.getByTestId("console-output");
  await expect(console_).toBeVisible();
  await expect(async () => {
    const text = (await console_.innerText()).trim();
    expect(text.length).toBeGreaterThan(0);
    expect(text).not.toMatch(/Console idle/i);
  }).toPass({ timeout: 30_000 });
});
