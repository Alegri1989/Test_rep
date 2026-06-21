import pytest
from playwright.sync_api import sync_playwright, Page
from pages.vacancy_search_page import VacancySearchPage


@pytest.fixture(scope="session", autouse=True)
def run_global_auth():
    """Полностью отключает запуск глобальной сессионной авторизации для этой папки."""
    pass


@pytest.fixture(scope="function")
def guest_page(pytestconfig) -> Page:
    """Создает гостевую страницу с десктопным разрешением для стабильности headless режима."""
    # 🛡️ Безопасное чтение флага headed для совместимости дома и в GitHub Actions
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True  # Если флага нет в конфигурации, запускаем в headless-режиме

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"])

        # Насильно задаем десктопный размер экрана 1920x1080, чтобы верстка ГСЗ не сжималась
        context = browser.new_context(
            locale="ru-RU",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # Шаг 1: Заходим на главную страницу портала
        page.goto("https://gsz.gov.by")
        page.wait_for_load_state("load")

        # Шаг 2: Принимаем куки один раз на главной
        try:
            cookie_btn = page.locator("text=ПРИНЯТЬ").first
            cookie_btn.wait_for(state="visible", timeout=3000)
            cookie_btn.click()
            cookie_btn.wait_for(state="hidden", timeout=3000)
            page.wait_for_load_state("load")
        except Exception:
            pass

        yield page

        context.close()
        browser.close()


@pytest.fixture(scope="function")
def vacancy_page(guest_page: Page) -> VacancySearchPage:
    """Фикстура автоматической инициализации страницы поиска вакансий."""
    return VacancySearchPage(guest_page)
