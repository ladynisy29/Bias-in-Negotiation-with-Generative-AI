const { test, expect } = require("@playwright/test");

test("human message receives AI response", async ({ page }) => {
  await page.goto("/src/pages/Onboarding.html");

  await page.fill("#initial-offer", "900000");
  await page.click("#next-button");

  await page.waitForURL(/Chat\.html/);
  await expect(page.locator("#message-form")).toBeVisible();

  await page.fill("#message-input", "I can offer 900000");
  await page.fill("#offer-input", "900000");
  await page.click("#send-button");

  await expect(page.locator("#messages .bubble.ai").first()).toBeVisible({ timeout: 20000 });
});
