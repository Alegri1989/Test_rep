import pytest
from playwright.sync_api import sync_playwright
from helpers.network_helper import goto_with_retry


@pytest.fixture(scope="session", autouse=False)
def run_global_auth():
    """Отключаем автоматическую авторизацию для тестов главной страницы."""
    pass


@pytest.fixture(scope="function")
def guest_page(pytestconfig):
    """Создает чистую страницу браузера и честно принимает куки-плашку."""
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    slow_mo_val = 400
    try:
        if pytestconfig.getoption("slowmo") != 0:
            slow_mo_val = pytestconfig.getoption("slowmo")
    except ValueError:
        pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], slow_mo=slow_mo_val, channel="chrome")
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()
        page.set_default_navigation_timeout(45000)

        # Навигация и клик по куки-панели (по аналогии с LoginPage)
        goto_with_retry(page, "https://gsz.gov.by", wait_until="load")
        cookie_accept = page.locator("a.cookie-panel__info_button")
        cookie_accept.wait_for(state="visible", timeout=5000)
        cookie_accept.click()

        page.wait_for_timeout(2000)

        # Переводим страницу обратно на главную для старта тестов
        goto_with_retry(page, "https://gsz.gov.by", wait_until="load")
        page.wait_for_load_state("networkidle")

        yield page

        context.close()
        browser.close()
