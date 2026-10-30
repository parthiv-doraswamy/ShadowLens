import { expect, test } from "@playwright/test";

test("dashboard bootstrap renders its public shell", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("ShadowLens");
  await expect(page.getByRole("heading", { name: "ShadowLens", level: 1 })).toBeVisible();
  await expect(page.getByText("LOCAL-FIRST SECURITY AUDITING")).toBeVisible();
});

test("design system showcase exposes working component interactions", async ({ page }) => {
  await page.goto("/design-system");
  await expect(page.getByRole("heading", { name: "Interface system" })).toBeVisible();
  await page.getByRole("tab", { name: "Forms" }).click();
  await page.getByLabel("Search inventory").fill("ollama");
  await expect(page.getByLabel("Search inventory")).toHaveValue("ollama");
  await page.getByRole("tab", { name: "Buttons" }).click();
  await page.getByRole("button", { name: "Open dialog" }).click();
  await expect(page.getByRole("dialog", { name: "Confirm example action" })).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Open drawer" }).click();
  await expect(page.getByRole("dialog", { name: "Evidence context" })).toBeVisible();
});
