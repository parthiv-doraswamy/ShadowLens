import { expect, test } from "@playwright/test";

test("landing page presents the product and its visibility boundaries", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("ShadowLens");
  await expect(page.getByRole("heading", { name: /See the AI/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /Explore the platform/ })).toHaveAttribute("href", "#platform");
  await expect(page.getByRole("heading", { name: /Every signal has/ })).toBeVisible();
  await expect(page.getByText("ILLUSTRATIVE · NOT LIVE DATA")).toBeVisible();
  await expect(page.getByText(/Encrypted traffic is never described/)).toBeVisible();
});

test("landing navigation reaches platform sections and design preview", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Visibility model" }).click();
  await expect(page).toHaveURL(/#visibility$/);
  await expect(page.getByRole("heading", { name: /visibility level/ })).toBeVisible();
  await page.getByRole("link", { name: /Interface preview/ }).click();
  await expect(page).toHaveURL(/\/design-system$/);
  await expect(page.getByRole("heading", { name: "Interface system" })).toBeVisible();
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
