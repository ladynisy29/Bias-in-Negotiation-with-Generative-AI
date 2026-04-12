const { test, expect } = require("@playwright/test");

test("onboarding form renders", async ({ page }) => {
  await page.goto("/src/pages/Onboarding.html");
  await expect(page.getByRole("heading", { name: "Participant Information" })).toBeVisible();
  await expect(page.locator("#onboarding-form")).toBeVisible();
  await expect(page.locator("#age")).toBeVisible();
  await expect(page.locator("#gender")).toBeVisible();
});

test("chat page redirects without session id", async ({ page }) => {
  await page.goto("/src/pages/Chat.html");
  await expect(page).toHaveURL(/Onboarding\.html/);
});
