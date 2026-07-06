import os
import logging
import logging.config
import pytest
import allure
from os import path
from playwright.sync_api import sync_playwright, Page
from pages.vacancy_search_page import VacancySearchPage
from pages.public_work_page import PublicWorkPage
from pages.gpd_page import GpdPage
from pages.future_work_page import FutureWorkPage
from pages.education_page import EducationPage
from pages.foreign_page import ForeignPage
from pages.opfr_page import OpfrPage
from pages.public_resume_search_page import PublicResumeSearchPage
from pages.departments_page import DepartmentsPage
from pages.activity_page import ActivityPage
from pages.news_page import NewsPage
from pages.services_page import ServicesPage
from helpers.network_helper import goto_with_retry

ROOT_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
lof_file_path = path.join(ROOT_DIR, "logging.ini")


@pytest.fixture(scope="session", autouse=True)
def run_global_auth():
    """Полностью отключает запуск глобальной сессионной авторизации для этой папки."""
    pass


@pytest.fixture(scope="function")
def guest_page(pytestconfig, request) -> Page:
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

        file_logger = logging.getLogger("file")
        page.on(
            "request",
            lambda req: file_logger.debug(f"СЕТЬ: ЗАПРОС -> {req.method} {req.url}")
            if req.url.startswith("https://gsz.gov.by")
            and req.resource_type in ["xhr", "fetch", "document"]
            else None,
        )
        page.on(
            "response",
            lambda res: file_logger.debug(f"СЕТЬ: ОТВЕТ <- [{res.status}] {res.url}")
            if res.url.startswith("https://gsz.gov.by")
            and res.request.resource_type in ["xhr", "fetch", "document"]
            else None,
        )

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

        try:
            if not page.is_closed():
                page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

        logging.shutdown()

        if os.path.exists("log.txt"):
            try:
                with open("log.txt", "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
                if log_content.strip():
                    allure.attach(log_content, name="Сетевые логи", attachment_type=allure.attachment_type.TEXT)
            except Exception:
                pass
            open("log.txt", "w").close()

        logging.config.fileConfig(lof_file_path)

        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            try:
                if not page.is_closed():
                    allure.attach(
                        page.screenshot(full_page=True, timeout=5000),
                        name="Скриншот при падении",
                        attachment_type=allure.attachment_type.PNG,
                    )
            except Exception:
                pass

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
def education_page(guest_page: Page) -> EducationPage:
    """Фикстура автоматической инициализации страницы обучения."""
    return EducationPage(guest_page)


@pytest.fixture(scope="function")
def foreign_page(guest_page: Page) -> ForeignPage:
    """Фикстура автоматической инициализации страницы занятости иностранных граждан."""
    return ForeignPage(guest_page)


@pytest.fixture(scope="function")
def opfr_page(guest_page: Page) -> OpfrPage:
    """Фикстура автоматической инициализации страницы ОПФР-организаций."""
    return OpfrPage(guest_page)


@pytest.fixture(scope="function")
def public_resume_search_page(guest_page: Page) -> PublicResumeSearchPage:
    """Фикстура автоматической инициализации страницы публичного поиска резюме."""
    return PublicResumeSearchPage(guest_page)


@pytest.fixture(scope="function")
def departments_page(guest_page: Page) -> DepartmentsPage:
    """Фикстура автоматической инициализации страницы справочника отделов занятости."""
    return DepartmentsPage(guest_page)


@pytest.fixture(scope="function")
def activity_page(guest_page: Page) -> ActivityPage:
    """Фикстура автоматической инициализации страницы публичного списка мероприятий."""
    return ActivityPage(guest_page)


@pytest.fixture(scope="function")
def news_page(guest_page: Page) -> NewsPage:
    """Фикстура автоматической инициализации страницы публичного списка новостей."""
    return NewsPage(guest_page)


@pytest.fixture(scope="function")
def services_page(guest_page: Page) -> ServicesPage:
    """Фикстура автоматической инициализации страницы публичного списка услуг."""
    return ServicesPage(guest_page)


@pytest.fixture(scope="function")
def test_sorting():
    """Локальная фикстура-заглушка для связывания аргумента теста с хуком генерации тестов."""
    pass