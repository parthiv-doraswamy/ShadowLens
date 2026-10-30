import { expect, test } from "@playwright/test";

test("dashboard bootstrap renders its public shell", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("ShadowLens");
  await expect(page.getByRole("heading", { name: "ShadowLens", level: 1 })).toBeVisible();
  await expect(page.getByText("LOCAL-FIRST SECURITY AUDITING")).toBeVisible();
});
