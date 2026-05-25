import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 60_000,
  retries: 0,
  reporter: [
    ["list"],
    ["html", { outputFolder: "test-results/html", open: "never" }],
  ],
  outputDir: "test-results/artifacts",
  use: {
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
    headless: true,
    // Always capture a trace + screenshot + video so failures are debuggable.
    trace: "on",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
