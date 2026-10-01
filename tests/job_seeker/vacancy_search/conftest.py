import pytest
from playwright.sync_api import Page
from pages.job_seeker_vacancy_search_page import JobSeekerVacancySearchPage
from helpers.network_helper import goto_with_retry

VACANCY_SEARCH_URL = "https://gsz.gov.by/registration/vacancy-search/"


@pytest.fixture(scope="function")
def vacancy_search_page(auth_page: Page) -> JobSeekerVacancySearchPage:
    """Открывает страницу поиска вакансий соискателя и возвращает объект страницы."""
    goto_with_retry(auth_page, VACANCY_SEARCH_URL, wait_until="load")
    auth_page.wait_for_selector("#id_profession", state="visible", timeout=30000)
    auth_page.wait_for_load_state("networkidle")
    return JobSeekerVacancySearchPage(auth_page)
