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

test("all analyst page templates render with synthetic-data disclaimers", async ({ page }) => {
  const routes = [
    ["/app/overview","Overview"],["/app/inventory","AI Inventory"],["/app/alerts","Leak Alerts"],
    ["/app/graph","Agent Graph"],["/app/compliance","Compliance"],["/app/ingest","Data Sources"],
    ["/app/policies","Policy Studio"],["/app/system","System & Privacy"],
  ] as const;
  for (const [route,title] of routes) {
    await page.goto(route);
    await expect(page.getByRole("heading", { name:title, level:1 })).toBeVisible();
    await expect(page.getByText(/Preview dataset|Synthetic finding records|Conceptual graph|Control mappings|Ingestion is not connected|Candidate policy|static preview/i).first()).toBeVisible();
    await expect(page.getByText("UI TEMPLATE READY")).toBeVisible();
  }
});

test("inventory filters and detail preview are interactive", async ({ page }) => {
  await page.goto("/app/inventory");
  await page.getByLabel("Filter inventory").fill("ollama");
  await expect(page.getByRole("row").filter({hasText:"Ollama"})).toBeVisible();
  await expect(page.getByRole("row").filter({hasText:"Cursor"})).toHaveCount(0);
  await page.getByRole("button", {name:"Details"}).click();
  await expect(page.getByText("Sample detail · Ollama")).toBeVisible();
  await page.getByRole("button", {name:"Close details"}).click();
});

test("alert filters and finding selection work without changing backend state", async ({ page }) => {
  await page.goto("/app/alerts");
  await page.getByLabel("Filter severity").selectOption("High");
  await expect(page.getByText("SL-DEMO-014")).toBeVisible();
  await expect(page.getByText("SL-DEMO-011")).toHaveCount(0);
  await page.getByLabel("Filter severity").selectOption("All");
  await page.getByRole("button", {name:/SL-DEMO-011/}).click();
  await expect(page.getByText("New AI destination observed")).toBeVisible();
  await expect(page.getByText("UNAVAILABLE", {exact:true})).toBeVisible();
});

test("data source tabs and policy editor are safe previews", async ({ page }) => {
  await page.goto("/app/ingest");
  await page.getByRole("tab", {name:"Gateway"}).click();
  await expect(page.getByText(/does not passively decrypt arbitrary HTTPS traffic/)).toBeVisible();
  await page.goto("/app/policies");
  await page.getByRole("tab", {name:"Simulation diff"}).click();
  await expect(page.getByText("No simulation results")).toBeVisible();
  await page.getByRole("tab", {name:"Editor"}).click();
  await page.getByLabel("Candidate YAML policy").fill("version: 1");
  await page.getByRole("button", {name:"Preview syntax check"}).click();
  await expect(page.getByText(/backend schema validator is not connected/)).toBeVisible();
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
