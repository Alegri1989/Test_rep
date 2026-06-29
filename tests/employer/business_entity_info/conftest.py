import pytest
from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry

EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"
EMPLOYER_EDIT_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/edit/"


@pytest.fixture(scope="function")
def open_employer_info_page(auth_employer_page: Page) -> Page:
    """Открывает страницу сведений о нанимателе (auth уже в состоянии нанимателя)."""
    goto_with_retry(auth_employer_page, EMPLOYER_INFO_URL, wait_until="load")
    return auth_employer_page


@pytest.fixture(scope="function")
def open_employer_edit_info_page(auth_employer_page: Page) -> Page:
    """Открывает страницу редактирования сведений о нанимателе."""
    goto_with_retry(auth_employer_page, EMPLOYER_EDIT_INFO_URL, wait_until="load")
    return auth_employer_page
