import pytest
from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


@pytest.fixture(scope="function")
def open_profile_page(auth_page):
    """Чистое открытие страницы профиля соискателя с устойчивостью к медленной сети."""
    profile_url = "https://gsz.gov.by/registration/job-seeker/personal-info/"

    clean_url = profile_url.replace(" ", "")
    goto_with_retry(auth_page, clean_url, wait_until="load")

    return auth_page
