import pytest
from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry

CREATE_GPD_URL = "https://gsz.gov.by/registration/employer/gpd/create/"
GPD_ARCHIVE_URL = "https://gsz.gov.by/registration/employer/gpd/list/archive/"


@pytest.fixture(scope="function")
def open_create_gpd_page(auth_employer_page: Page) -> Page:
    """Открывает страницу создания вакансии по ГПД."""
    goto_with_retry(auth_employer_page, CREATE_GPD_URL, wait_until="load")
    return auth_employer_page
