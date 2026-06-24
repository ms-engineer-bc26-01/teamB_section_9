import { test, expect } from '@playwright/test';

test('top page is displayed', async ({ page }) => {
  await page.goto('/');

  await expect(page).toHaveTitle(/Climo/);
});
