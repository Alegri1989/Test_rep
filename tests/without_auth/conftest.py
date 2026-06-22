import pytest
from playwright.sync_api import sync_playwright, Page
from pages.vacancy_search_page import VacancySearchPage
from pages.public_work_page import PublicWorkPage
from pages.gpd_page import GpdPage
from pages.future_work_page import FutureWorkPage
from helpers.network_helper import goto_with_retry


@pytest.fixture(scope="session", autouse=True)
def run_global_auth():
    """Полностью отключает запуск глобальной сессионной авторизации для этой папки."""
    pass


@pytest.fixture(scope="function")
def guest_page(pytestconfig) -> Page:
    """Создает гостевую страницу с десктопным разрешением для стабильности headless режима."""
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], channel="chrome")

        context = browser.new_context(
            locale="ru-RU",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.set_default_navigation_timeout(45000)
        page.set_default_timeout(15000)

        goto_with_retry(page, "https://gsz.gov.by", wait_until="load")

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


@pytest.fixture(scope="function")
def public_work_page(guest_page: Page) -> PublicWorkPage:
    """Фикстура автоматической инициализации страницы временных оплачиваемых работ."""
    return PublicWorkPage(guest_page)


@pytest.fixture(scope="function")
def gpd_page(guest_page: Page) -> GpdPage:
    """Фикстура автоматической инициализации страницы работ по гражданско-правовым договорам."""
    return GpdPage(guest_page)


@pytest.fixture(scope="function")
def future_work_page(guest_page: Page) -> FutureWorkPage:
    """Фикстура автоматической инициализации страницы перспективных рабочих мест."""
    return FutureWorkPage(guest_page)


@pytest.fixture(scope="function")
def test_sorting():
    """Локальная фикстура-заглушка для связывания аргумента теста с хуком генерации тестов."""
    pass