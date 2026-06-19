import allure
import pytest
from playwright.sync_api import Page, expect
from pages.resume_page import ResumePage
from helpers.resume_helper import fill_and_submit_required_resume_fields, clear_all_resumes_from_account


class TestResumePublication:

    @allure.epic("Резюме соискателя")
    @allure.title("Бизнес-кейс: Публикация созданного резюме и снятие с публикации")
    def test_publish_and_unpublish_resume_workflow(self, prepare_resume_for_publication: Page):
        page = prepare_resume_for_publication
        resume = ResumePage(page)

        try:
            with allure.step("Шаг 1: Клик по кнопке 'Опубликовать' на последнем созданном резюме"):
                resume.last_publish_button.wait_for(state="visible", timeout=5000)
                resume.last_publish_button.click()

            with allure.step("Шаг 2: Подтверждение публикации в модальном окне"):
                resume.modal_publish_submit.wait_for(state="visible", timeout=5000)
                resume.modal_publish_submit.click()
                page.wait_for_load_state("networkidle")

            with allure.step("ОР 1: Кнопка изменилась на 'Снять с публикации'"):
                expect(resume.last_unpublish_button).to_be_visible(timeout=5000)

        finally:
            with allure.step("Посткондишн: Снятие с публикации и удаление мусорного резюме"):
                clear_all_resumes_from_account(page)

    @allure.title("Бизнес-кейс: Ограничение на максимум 3 опубликованных резюме")
    def test_maximum_published_resumes_limit(self, prepare_maximum_published_resumes: Page):
        page = prepare_maximum_published_resumes
        resume = ResumePage(page)
        resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"

        try:
            with allure.step("Шаг 1: Создание 4-го резюме (черновика)"):
                resume.create_resume_button.click()
                page.wait_for_load_state("load")
                fill_and_submit_required_resume_fields(page)
                page.goto(resume_list_url)
                page.wait_for_load_state("networkidle")

            with allure.step("Шаг 2: Проверка блокировки кнопки публикации у 4-го резюме"):
                resume.disabled_publish_button.first.wait_for(state="visible", timeout=5000)
                expect(resume.disabled_publish_button.first).to_be_disabled()
                expect(resume.disabled_publish_button.first).to_have_attribute(
                    "title", "Опубликовано максимальное количество резюме"
                )

        finally:
            with allure.step("Посткондишн: Полная очистка всех резюме с аккаунта"):
                clear_all_resumes_from_account(page)

    @allure.title("Бизнес-кейс: Снятие опубликованного резюме с публикации")
    def test_unpublish_resume_workflow(self, open_create_resume_page: Page):
        page = open_create_resume_page
        resume = ResumePage(page)
        resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"

        try:
            with allure.step("Шаг 1: Быстрое создание резюме через хелпер"):
                fill_and_submit_required_resume_fields(page)
                page.goto(resume_list_url)
                page.wait_for_load_state("networkidle")

            with allure.step("Шаг 2: Публикация созданного резюме"):
                resume.last_publish_button.wait_for(state="visible", timeout=5000)
                resume.last_publish_button.click()
                resume.modal_publish_submit.wait_for(state="visible", timeout=5000)
                resume.modal_publish_submit.click()
                page.wait_for_load_state("networkidle")

            with allure.step("Шаг 3: Снятие резюме с публикации"):
                resume.last_unpublish_button.wait_for(state="visible", timeout=5000)
                resume.last_unpublish_button.click()
                page.wait_for_load_state("networkidle")

            with allure.step("ОР 1: Кнопка изменилась обратно на 'Опубликовать'"):
                expect(resume.last_publish_button).to_be_visible(timeout=5000)

        finally:
            with allure.step("Посткондишн: Гарантированная очистка аккаунта"):
                clear_all_resumes_from_account(page)