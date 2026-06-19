import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session", autouse=False)
def run_global_auth():
    """Отключаем автоматическую авторизацию для тестов главной страницы."""
    pass


@pytest.fixture(scope="function")
def guest_page(pytestconfig):
    """Создает чистую страницу браузера и честно принимает куки-плашку."""
    is_headless = not pytestconfig.getoption("headed")
    slow_mo_val = pytestconfig.getoption("slowmo")
    if slow_mo_val == 0:
        slow_mo_val = 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], slow_mo=slow_mo_val)
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()

        # Навигация и клик по куки-панели (по аналогии с LoginPage)
        page.goto("https://gsz.gov.by")
        cookie_accept = page.locator("a.cookie-panel__info_button")
        cookie_accept.wait_for(state="visible", timeout=5000)
        cookie_accept.click()

        page.wait_for_timeout(2000)

        # Переводим страницу обратно на главную для старта тестов
        page.goto("https://gsz.gov.by")
        page.wait_for_load_state("networkidle")

        yield page

        context.close()
        browser.close()