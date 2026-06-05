import os
import pytest
from playwright.sync_api import sync_playwright

AUTH_STATE_PATH = "auth_state.json"

def block_ads_route(route):
    url = route.request.url.lower()
    if "googleads" in url or "googlesyndication" in url:
        if route.request.resource_type == "script":
            return route.abort()
    return route.continue_()


@pytest.fixture(scope="session", autouse=True)
def run_global_auth(pytestconfig):
    is_headless = not pytestconfig.getoption("headed")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=["--disable-features=Translate", "--lang=en-US"]
        )
        context = browser.new_context(locale="en-US")
        context.route("**/*", block_ads_route)
        page = context.new_page()

        page.goto("https://automationexercise.com/login", wait_until="domcontentloaded")
        page.locator(".login-form").wait_for(state="visible")
        page.locator(".login-form input[type='email']").fill("1234@tut.by")
        page.locator(".login-form input[type='password']").fill("12345")
        page.locator(".login-form button[type='submit']").click()
        page.wait_for_selector("text=Logged in as")

        context.storage_state(path=AUTH_STATE_PATH)
        browser.close()
    yield
    if os.path.exists(AUTH_STATE_PATH):
        os.remove(AUTH_STATE_PATH)


@pytest.fixture(scope="function")
def auth_page(pytestconfig):
    is_headless = not pytestconfig.getoption("headed")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,  # Динамически подставляем режим
            args=["--disable-features=Translate", "--lang=en-US"]
        )
        context = browser.new_context(
            storage_state=AUTH_STATE_PATH,
            record_video_dir="videos/",
            locale="en-US"
        )
        context.route("**/*", block_ads_route)
        page = context.new_page()
        yield page
        context.close()
        browser.close()