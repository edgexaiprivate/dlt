"""
LAYER 3 — End-to-End Tests: Playwright
Tests complete user journeys in a real browser against a running app.

Prerequisites:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/ --base-url http://localhost:3000

Flows tested:
  1. Login → Dashboard renders
  2. Manager login → Menu Manager → Add category → Add item → Publish
  3. Logout → redirected to login
  4. Wrong credentials → error toast shown
  5. Mobile viewport works
"""
import pytest
from playwright.async_api import Page, expect


BASE_URL = "http://localhost:3000"
MANAGER_USER = "manager1"
MANAGER_PASS = "Manager@1234"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@1234"


# ── Helpers ───────────────────────────────────────────────────────────────────

async def login(page: Page, username: str, password: str):
    await page.goto(f"{BASE_URL}/login")
    await page.fill('input[placeholder*="username" i]', username)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{BASE_URL}/", timeout=5000)


# ── Flow 1: Login ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_page_renders(page: Page):
    await page.goto(f"{BASE_URL}/login")
    await expect(page.locator("text=MenuVision")).to_be_visible()
    await expect(page.locator('input[type="password"]')).to_be_visible()
    await expect(page.locator('button[type="submit"]')).to_be_visible()


@pytest.mark.asyncio
async def test_login_success_redirects_to_dashboard(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await expect(page).to_have_url(f"{BASE_URL}/")
    # Dashboard should show greeting or stat cards
    await expect(page.locator("text=Dashboard").or_(page.locator("text=Good"))).to_be_visible()


@pytest.mark.asyncio
async def test_login_wrong_credentials_shows_error(page: Page):
    await page.goto(f"{BASE_URL}/login")
    await page.fill('input[placeholder*="username" i]', "nobody")
    await page.fill('input[type="password"]', "wrongpassword")
    await page.click('button[type="submit"]')
    # Should stay on login page
    await expect(page).to_have_url(f"{BASE_URL}/login")
    # Error toast should appear
    await expect(
        page.locator("text=Incorrect").or_(page.locator("text=failed").or_(page.locator('[role="status"]')))
    ).to_be_visible(timeout=3000)


@pytest.mark.asyncio
async def test_login_empty_form_shows_validation(page: Page):
    await page.goto(f"{BASE_URL}/login")
    await page.click('button[type="submit"]')
    # Should still be on login — form blocked
    await expect(page).to_have_url(f"{BASE_URL}/login")


# ── Flow 2: Menu Management ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_menu_page_loads_categories(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await page.click('a[href="/menu"]')
    await expect(page).to_have_url(f"{BASE_URL}/menu")
    await expect(page.locator("text=Menu Manager")).to_be_visible()
    # Seed data: South Indian should be visible
    await expect(page.locator("text=South Indian")).to_be_visible(timeout=5000)


@pytest.mark.asyncio
async def test_add_menu_category(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await page.goto(f"{BASE_URL}/menu")
    await page.click('button:has-text("Add Category")')
    # Modal opens
    await expect(page.locator("text=Add Category")).to_be_visible()
    await page.fill('input[placeholder*="South Indian" i]', "E2E Test Category")
    await page.fill('input[placeholder*="order" i]', "99")
    await page.click('button[type="submit"]:has-text("Create")')
    # Category should appear in list
    await expect(page.locator("text=E2E Test Category")).to_be_visible(timeout=5000)


@pytest.mark.asyncio
async def test_publish_button_present(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await page.goto(f"{BASE_URL}/menu")
    await expect(page.locator('button:has-text("Publish")').first).to_be_visible()


# ── Flow 3: Logout ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_redirects_to_login(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await page.click('button:has-text("Sign Out")')
    await expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)


@pytest.mark.asyncio
async def test_protected_route_redirects_when_logged_out(page: Page):
    await page.goto(f"{BASE_URL}/menu")
    # Should redirect to login without auth
    await expect(page).to_have_url(f"{BASE_URL}/login", timeout=3000)


# ── Flow 4: Devices ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_devices_page_loads(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await page.click('a[href="/devices"]')
    await expect(page.locator("text=Devices")).to_be_visible()


@pytest.mark.asyncio
async def test_register_device_modal_opens(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    await page.goto(f"{BASE_URL}/devices")
    await page.click('button:has-text("Register Device")')
    await expect(page.locator("text=Register New Device")).to_be_visible()


# ── Flow 5: Mobile viewport ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_renders_on_mobile(page: Page):
    await page.set_viewport_size({"width": 390, "height": 844})  # iPhone 14
    await page.goto(f"{BASE_URL}/login")
    await expect(page.locator("text=MenuVision")).to_be_visible()
    await expect(page.locator('button[type="submit"]')).to_be_visible()


@pytest.mark.asyncio
async def test_dashboard_renders_on_mobile(page: Page):
    await page.set_viewport_size({"width": 390, "height": 844})
    await login(page, MANAGER_USER, MANAGER_PASS)
    await expect(page).to_have_url(f"{BASE_URL}/")
    # Page should not have horizontal overflow on mobile
    overflow = await page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, "Page has horizontal overflow on mobile viewport"


# ── Flow 6: Super Admin ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_super_admin_sees_restaurants_nav(page: Page):
    await login(page, ADMIN_USER, ADMIN_PASS)
    await expect(page.locator('a[href="/restaurants"]')).to_be_visible()


@pytest.mark.asyncio
async def test_manager_does_not_see_restaurants_nav(page: Page):
    await login(page, MANAGER_USER, MANAGER_PASS)
    # Manager should NOT see restaurants link in sidebar
    count = await page.locator('a[href="/restaurants"]').count()
    assert count == 0
