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

test("dashboard shell provides all primary workspace destinations", async ({ page }) => {
  await page.goto("/app/overview");
  await expect(page.getByRole("heading", { name: "Overview", level: 1 })).toBeVisible();
  await expect(page.getByText("PREVIEW ENVIRONMENT")).toBeVisible();
  await expect(page.getByText(/No backend API is connected/)).toBeVisible();
  await page.getByRole("link", { name: /AI Inventory/ }).click();
  await expect(page).toHaveURL(/\/app\/inventory$/);
  await expect(page.getByRole("heading", { name: "AI Inventory", level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: /AI Inventory/ })).toHaveAttribute("aria-current", "page");
  await page.getByRole("link", { name: /System & Privacy/ }).click();
  await expect(page).toHaveURL(/\/app\/system$/);
  await expect(page.getByRole("heading", { name: "System & Privacy", level: 1 })).toBeVisible();
});

test("dashboard shell navigation is usable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/overview");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toBeVisible();
  await page.getByRole("link", { name: /Leak Alerts/ }).click();
  await expect(page).toHaveURL(/\/app\/alerts$/);
  await expect(page.getByRole("heading", { name: "Leak Alerts", level: 1 })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open navigation" })).toHaveAttribute("aria-expanded", "false");
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
