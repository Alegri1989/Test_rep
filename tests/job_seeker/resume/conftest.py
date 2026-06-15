import pytest
from playwright.sync_api import Page
from pages.resume_page import ResumePage


@pytest.fixture(scope="function")
def open_create_resume_page(auth_page: Page):
    """Прекондишн: переход в список резюме и клик по кнопке Создать."""
    resume_list_url = (
        "https://gsz.gov.by/registration/job-seeker/resume/list/"
    )

    auth_page.goto(resume_list_url)
    # Ждем только полной загрузки элементов страницы вместо ожидания затишья сети
    auth_page.wait_for_load_state("load")

    resume_page = ResumePage(auth_page)
    resume_page.create_resume_button.click()
    auth_page.wait_for_load_state("load")

    return auth_page