import allure
import pytest
from playwright.sync_api import Page
from pages.resume_page import ResumePage
from helpers.resume_helper import fill_and_submit_resume_form, fill_and_submit_required_resume_fields


@pytest.fixture(scope="function")
def open_create_resume_page(auth_page: Page):
    """Прекондишн: переход в список резюме с обработкой стабильности страницы."""
    resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"
    resume_page = ResumePage(auth_page)

    clean_url = resume_list_url.replace(" ", "")
    if auth_page.url != clean_url:
        auth_page.goto(clean_url)
        auth_page.wait_for_load_state("load")

    try:
        resume_page.create_resume_button.wait_for(state="visible", timeout=3000)
    except Exception:
        auth_page.reload()
        auth_page.wait_for_load_state("load")
        resume_page.create_resume_button.wait_for(state="visible", timeout=10000)

    resume_page.create_resume_button.click()
    auth_page.wait_for_load_state("load")

    return auth_page


@pytest.fixture(scope="function")
def prepare_resume_for_publication(auth_page: Page):
    """Прекондишн: создает черновик резюме со всеми заполненными полями через хелпер."""
    resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"
    resume = ResumePage(auth_page)

    clean_url = resume_list_url.replace(" ", "")
    if auth_page.url != clean_url:
        auth_page.goto(clean_url)
        auth_page.wait_for_load_state("load")

    try:
        resume.create_resume_button.wait_for(state="visible", timeout=3000)
    except Exception:
        auth_page.reload()
        auth_page.wait_for_load_state("load")
        resume.create_resume_button.wait_for(state="visible", timeout=10000)

    resume.create_resume_button.click()
    auth_page.wait_for_load_state("load")

    fill_and_submit_resume_form(auth_page)

    auth_page.goto(clean_url)
    auth_page.wait_for_load_state("load")

    return auth_page


@pytest.fixture(scope="function")
def prepare_maximum_published_resumes(auth_page: Page):
    """Прекондишн: гарантирует, что на аккаунте соискателя опубликовано ровно 3 резюме."""
    resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"
    resume = ResumePage(auth_page)

    clean_url = resume_list_url.replace(" ", "")
    if auth_page.url != clean_url:
        auth_page.goto(clean_url)
        auth_page.wait_for_load_state("load")

    while resume.all_unpublish_links.count() > 3:
        resume.all_unpublish_links.first.click()
        auth_page.wait_for_load_state("load")
        resume.all_delete_buttons.first.click()
        resume.popup_confirm_delete_btn.click()
        auth_page.wait_for_load_state("load")

    while resume.all_unpublish_links.count() < 3:
        # Даем DOM-дереву секунду на стабилизацию перед подсчетом динамических кнопок
        auth_page.wait_for_timeout(1000)

        if resume.all_publish_buttons.count() == 0:
            resume.create_resume_button.click()
            auth_page.wait_for_load_state("load")
            fill_and_submit_required_resume_fields(auth_page)
            auth_page.goto(clean_url)
            auth_page.wait_for_load_state("load")

        resume.all_publish_buttons.first.click()
        resume.modal_publish_submit.wait_for(state="visible", timeout=5000)
        resume.modal_publish_submit.click()
        auth_page.wait_for_load_state("load")

    return auth_page