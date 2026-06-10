import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="function")
def open_profile_page(auth_page):
    """Чистое открытие страницы профиля соискателя."""
    profile_url = "https://gsz.gov.by/registration/job-seeker/personal-info/"

    clean_url = profile_url.replace(" ", "")
    auth_page.goto(clean_url)

    return auth_page