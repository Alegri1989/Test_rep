import pytest
from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry

CREATE_VACANCY_URL = "https://gsz.gov.by/registration/employer/vacancy/create/"
CREATE_FUTURE_VACANCY_URL = "https://gsz.gov.by/registration/employer/vacancy/create_future/"
EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"
FUTURE_DRAFT_LIST_URL = "https://gsz.gov.by/registration/employer/future-vacancy/list/draft/"


@pytest.fixture(scope="function")
def open_create_vacancy_page(auth_employer_page: Page) -> Page:
    """Открывает страницу создания вакансии."""
    goto_with_retry(auth_employer_page, CREATE_VACANCY_URL, wait_until="load")
    return auth_employer_page


@pytest.fixture(scope="function")
def open_create_future_vacancy_page(auth_employer_page: Page) -> Page:
    """Открывает страницу создания перспективной вакансии."""
    goto_with_retry(auth_employer_page, CREATE_FUTURE_VACANCY_URL, wait_until="load")
    return auth_employer_page
