import re
import pytest
import allure
from playwright.sync_api import Page, expect
from pages.resume_page import ResumePage


@allure.epic("Личный кабинет соискателя")
@allure.feature("Создание резюме")
class TestResumeIntegration:

    @allure.title("Сквозное создание резюме с проверкой сохраненных данных и авто-удалением")
    def test_create_full_resume_workflow(self, open_create_resume_page: Page, app_config):
        resume = ResumePage(open_create_resume_page)

        # Тестовые данные
        test_profession = "Авербандщик"
        test_salary = "2000.00"
        test_phone = "375294445566"
        test_org = "ООО Тестовая Организация"
        test_edu = "БГУИР"
        test_info = "Автоматический E2E тест создания резюме. Проверка Flake8."
        expected_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"
        default_email = app_config["default_profile"]["email_sent"]

        with allure.step("Шаг 1: Заполнение блока 'Пожелания к работе'"):
            resume.profession_container.wait_for(state="visible", timeout=5000)
            resume.profession_container.click()

            resume.select2_search_input.press_sequentially(test_profession, delay=100)
            open_create_resume_page.wait_for_timeout(500)
            resume.select2_first_option.click()

            resume.derivative_dropdown.select_option("1")
            resume.salary_input.fill(test_salary)
            resume.employment_nature_dropdown.select_option("1")
            resume.work_mode_dropdown.select_option("1")

        with allure.step("Шаг 2: Активация чек-боксов"):
            resume.relocate_checkbox.dispatch_event("click")
            resume.housing_checkbox.dispatch_event("click")

        with allure.step("Шаг 3: Заполнение блока 'Контактная информация'"):
            expect(resume.email_input_0).to_have_value(default_email)
            resume.add_phone_button.click()
            open_create_resume_page.wait_for_timeout(300)
            resume.phone_input_0.fill(test_phone)

        with allure.step("Шаг 4: Заполнение блока 'Опыт работы'"):
            resume.add_experience_button.click()
            open_create_resume_page.wait_for_timeout(300)
            resume.exp_org_input.fill(test_org)

        with allure.step("Шаг 5: Заполнение блока 'Образование'"):
            resume.add_education_button.click()
            open_create_resume_page.wait_for_timeout(300)
            resume.edu_name_input.fill(test_edu)

        with allure.step("Шаг 6: Заполнение блока 'Владение языками'"):
            resume.language_dropdown.select_option("4")
            resume.lang_level_dropdown.select_option("10")

        with allure.step("Шаг 7: Заполнение блока 'Дополнительная информация'"):
            resume.additional_info_textarea.fill(test_info)

        with allure.step("Шаг 8: Нажатие кнопки 'Создать резюме' и отправка формы"):
            resume.submit_resume_button.click()
            open_create_resume_page.wait_for_url(expected_list_url, timeout=15000)
            open_create_resume_page.wait_for_load_state("domcontentloaded")

        try:
            with allure.step("Шаг 9: Переход на форму редактирования созданного резюме"):
                # Кликаем по кнопке 'Редактировать' самого нижнего (последнего) резюме в списке
                open_create_resume_page.locator(
                    "a[href*='/registration/job-seeker/resume/'][href$='/update/']"
                ).last.click()
                open_create_resume_page.wait_for_load_state("domcontentloaded")

            with allure.step("ОР: Вся введенная информация успешно сохранилась в базе и UI"):
                update_profession_container = open_create_resume_page.locator(
                    "#select2-id_desired_profession-container"
                )
                update_profession_container.wait_for(state="visible", timeout=5000)

                expect(update_profession_container).to_have_text(re.compile(test_profession))
                expect(resume.derivative_update_dropdown).to_have_value("1")
                expect(resume.salary_input).to_have_value(test_salary)
                expect(resume.employment_nature_dropdown).to_have_value("1")
                expect(resume.work_mode_dropdown).to_have_value("1")

                expect(resume.relocate_checkbox).to_be_checked()
                expect(resume.housing_checkbox).to_be_checked()

                expect(resume.email_input_0).to_have_value(default_email)
                expect(resume.phone_input_0).not_to_have_value("")

                expect(resume.exp_org_input).to_have_value(test_org)
                expect(resume.edu_name_input).to_have_value(test_edu)
                expect(resume.language_dropdown).to_have_value("4")
                expect(resume.lang_level_dropdown).to_have_value("10")
                expect(resume.additional_info_textarea).to_have_value(test_info)



        finally:

            with allure.step("Шаг 10: Гарантированная очистка данных (удаление резюме)"):

                current_url = open_create_resume_page.url

                match = re.search(r"/resume/(\d+)/", current_url)

                created_id = match.group(1) if match else None

                # Даем серверу небольшую передышку перед редиректом

                open_create_resume_page.wait_for_timeout(1000)

                if "/update/" in current_url:
                    open_create_resume_page.goto(expected_list_url)

                    open_create_resume_page.wait_for_load_state("domcontentloaded")

                if not created_id:
                    last_link = open_create_resume_page.locator(

                        "a[href*='/registration/job-seeker/resume/'][href$='/update/']"

                    ).last

                    href_value = last_link.get_attribute("href")

                    match = re.search(r"/resume/(\d+)/", href_value)

                    created_id = match.group(1) if match else None

                # Делаем паузу перед вызовом модалки удаления

                open_create_resume_page.wait_for_timeout(1000)

                resume.last_resume_delete_btn.click()

                # Даем модалке стабильно отрисоваться и разгрузить сеть

                open_create_resume_page.wait_for_timeout(1000)

                resume.popup_confirm_delete_btn.click()

                open_create_resume_page.wait_for_load_state("networkidle")

            with allure.step("ОР 3: Удаленное резюме полностью исчезло из списка"):

                # Небольшая пауза после удаления перед финальной проверкой DOM

                open_create_resume_page.wait_for_timeout(1000)

                deleted_resume_link = open_create_resume_page.locator(

                    f"a[href*='/registration/job-seeker/resume/{created_id}/update/']"

                )

                expect(deleted_resume_link).not_to_be_visible(timeout=5000)