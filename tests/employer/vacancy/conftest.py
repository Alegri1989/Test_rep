import pytest
from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry

CREATE_VACANCY_URL = "https://gsz.gov.by/registration/employer/vacancy/create/"
EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"


@pytest.fixture(scope="function")
def open_create_vacancy_page(auth_employer_page: Page) -> Page:
    """Открывает страницу создания вакансии."""
    goto_with_retry(auth_employer_page, CREATE_VACANCY_URL, wait_until="load")
    return auth_employer_page
