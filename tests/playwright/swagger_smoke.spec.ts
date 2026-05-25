import { test, expect } from "@playwright/test";
import path from "node:path";

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DOCS_URL = process.env.DOCS_URL ?? "http://localhost:3001/api/docs/";
const SCREENSHOT_PATH = path.join(REPO_ROOT, "assets", "swagger.png");

test.use({ viewport: { width: 1400, height: 1800 } });

test("Swagger UI lists routes + screenshot", async ({ page, request }) => {
  test.setTimeout(60_000);

  // Spec contains ≥5 routes (matches the goal-condition curl assertion).
  const specRes = await request.get(`${DOCS_URL.replace(/\/$/, "")}/swagger.json`);
  expect(specRes.ok()).toBeTruthy();
  const spec = await specRes.json();
  const routes = Object.keys(spec.paths || {});
  expect(routes.length).toBeGreaterThanOrEqual(5);

  await page.goto(DOCS_URL);

  // Title is set by ``customSiteTitle`` in setup().
  await expect(page).toHaveTitle(/Spot Mock API/i);

  // Wait for the operation rows — swagger-ui renders each as
  // ``.opblock`` once the spec loads.
  const opBlocks = page.locator(".opblock");
  await expect(opBlocks.first()).toBeVisible({ timeout: 15_000 });
  const count = await opBlocks.count();
  expect(count).toBeGreaterThanOrEqual(5);

  // Capture the README screenshot with all operations collapsed.
  await page.waitForTimeout(400);
  await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true });

  // Then expand every operation and assert the first GET's schema renders.
  for (let i = 0; i < count; i++) {
    const block = opBlocks.nth(i);
    const summary = block.locator(".opblock-summary").first();
    if (await summary.isVisible()) {
      await summary.click();
    }
  }

  const firstGet = page.locator(".opblock.opblock-get").first();
  await expect(firstGet).toBeVisible();
  await expect(firstGet.locator(".responses-wrapper")).toBeVisible({
    timeout: 5_000,
  });
});
