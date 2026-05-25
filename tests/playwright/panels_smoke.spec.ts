import { test, expect } from "@playwright/test";

const WEB_URL = process.env.WEB_URL ?? "http://localhost:4000";

test.use({ viewport: { width: 1400, height: 900 } });

test("Tests panel splits into Local + Vendor, drag handle resizes both", async ({
  page,
}) => {
  test.setTimeout(45_000);

  await page.goto(WEB_URL);
  await expect(page).toHaveTitle(/Spot Mock/i);

  const localPanel = page.getByTestId("local-test-panel");
  const vendorPanel = page.getByTestId("vendor-test-panel");
  const handle = page.getByTestId("panels-drag-handle");

  // 2. Both panels and their headings are visible.
  await expect(localPanel).toBeVisible();
  await expect(vendorPanel).toBeVisible();
  await expect(
    localPanel.getByRole("heading", { name: /Custom Tests|Local Tests/i })
  ).toBeVisible();
  await expect(vendorPanel.getByRole("heading", { name: /Spot SDK Tests/i })).toBeVisible();

  // 3. Each panel has its own aria-labelled search input.
  const localSearch = page.getByLabel(/Filter (custom|local) tests/i);
  const vendorSearch = page.getByLabel("Filter SDK tests");
  await expect(localSearch).toBeVisible();
  await expect(vendorSearch).toBeVisible();

  // 4. DragHandle is visible between panels.
  await expect(handle).toBeVisible();

  // Wait for the manifest to have populated at least one test in each
  // section so the layout has stabilised before we measure heights.
  await expect
    .poll(async () => await localPanel.locator('[data-testid="test-card"]').count())
    .toBeGreaterThan(0);
  await expect
    .poll(async () => await vendorPanel.locator('[data-testid="test-card"]').count())
    .toBeGreaterThan(0);

  // 5. Record initial heights.
  const initLocal = await localPanel.boundingBox();
  const initVendor = await vendorPanel.boundingBox();
  expect(initLocal && initVendor).toBeTruthy();
  const localH0 = initLocal!.height;
  const vendorH0 = initVendor!.height;

  // 6. Drag the handle 80 px downward.
  const handleBox = await handle.boundingBox();
  expect(handleBox).toBeTruthy();
  const startX = handleBox!.x + handleBox!.width / 2;
  const startY = handleBox!.y + handleBox!.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  // Move in small steps so the pointermove handler fires repeatedly.
  for (let i = 1; i <= 8; i++) {
    await page.mouse.move(startX, startY + i * 10, { steps: 2 });
  }
  await page.mouse.up();
  await page.waitForTimeout(150);

  // 7. Local panel grew ~80 px, vendor shrank ~80 px.
  const afterLocal = await localPanel.boundingBox();
  const afterVendor = await vendorPanel.boundingBox();
  expect(afterLocal && afterVendor).toBeTruthy();
  expect(Math.abs(afterLocal!.height - (localH0 + 80))).toBeLessThanOrEqual(5);
  expect(Math.abs(afterVendor!.height - (vendorH0 - 80))).toBeLessThanOrEqual(5);

  // 8. Both remain above 120 px minimum.
  expect(afterLocal!.height).toBeGreaterThanOrEqual(120);
  expect(afterVendor!.height).toBeGreaterThanOrEqual(120);

  // 9. Typing "power" in Local filters only the local panel.
  const vendorCountBefore = await vendorPanel
    .locator('[data-testid="test-card"]')
    .count();
  await localSearch.fill("power");
  await expect
    .poll(async () => {
      const cards = await localPanel.locator('[data-testid="test-card"]').count();
      return cards;
    })
    .toBeGreaterThan(0);
  // Every visible local card mentions "power".
  const localCards = localPanel.locator('[data-testid="test-card"]');
  const localCount = await localCards.count();
  for (let i = 0; i < localCount; i++) {
    const text = (await localCards.nth(i).innerText()).toLowerCase();
    expect(text).toContain("power");
  }
  // Vendor panel card count unchanged.
  const vendorCountAfter = await vendorPanel
    .locator('[data-testid="test-card"]')
    .count();
  expect(vendorCountAfter).toBe(vendorCountBefore);

  // 10. Clicking the Local "Run Filtered" button streams SSE into the
  //     ConsoleOutput within 10 s.
  const runAllLocal = page.getByTestId("run-all-local");
  await expect(runAllLocal).toHaveText(/Run Filtered/i);
  const consoleOut = page.getByTestId("console-output");
  await runAllLocal.click();
  await expect(async () => {
    const text = (await consoleOut.innerText()).trim();
    expect(text.length).toBeGreaterThan(0);
    expect(text).not.toMatch(/Console idle/i);
  }).toPass({ timeout: 10_000 });
});
