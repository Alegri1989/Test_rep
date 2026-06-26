import re
import pytest
import allure
from playwright.sync_api import Page, expect
from pages.resume_page import ResumePage


@allure.epic("Резюме соискателя")
@allure.feature("Создание резюме")
class TestResumeIntegration:

    @allure.title("Сквозное создание резюме с проверкой сохраненных данных и авто-удалением")
    def test_create_full_resume_workflow(self, open_create_resume_page: Page, app_config):
        """
        Бизнес-кейс: Интеграционный сквозной E2E сценарий заполнения всех блоков формы резюме с последующей валидацией в режиме редактирования и гарантированной очисткой.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта пустая форма создания нового резюме.

        Шаги:
        1. Полностью заполнить блок "Пожелания к работе" (профессия в Select2, производная должность, зарплата, условия труда).
        2. Активировать чекбоксы согласия на переезд и потребности в жилье.
        3. Добавить динамическую строку и заполнить номер телефона, сверив дефолтный Email.
        4. Инициализировать блоки опыта работы и образования, заполнив их текстовыми названиями организаций.
        5. Выбрать параметры владения иностранными языками.
        6. Ввести блок сопроводительной дополнительной информации.
        7. Отправить заполненную форму на сервер кликом по кнопке "Создать резюме" и дождаться редиректа на страницу списка.
        8. Нажать кнопку редактирования созданного резюме для перехода на форму апдейта.
        9. Проверить сохранность каждого введенного параметра на форме редактирования.
        10. В блоке 'finally' выполнить гарантированное удаление резюме из общего списка для очистки базы данных.

        Ожидаемый результат (ОР):
        - Форма успешно отправляется, бэкенд без ошибок валидации регистрирует резюме и переводит пользователя на URL списка.
        - Все до единого сохраненные параметры (включая динамические формсеты и селекты) корректно подгружаются из базы на UI формы редактирования.
        - После удаления резюме полностью пропадает из интерфейса личного кабинета.
        """
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
            universal_profession_container = open_create_resume_page.locator(
                "[id^='select2-id_desired_profession'][id$='container']"
            )
            universal_profession_container.wait_for(state="visible", timeout=5000)
            universal_profession_container.click()

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
            resume.select_language("Английский")
            resume.select_language_level("Продвинутый")

        with allure.step("Шаг 7: Заполнение блока 'Дополнительная информация'"):
            resume.additional_info_textarea.fill(test_info)

        with allure.step("Шаг 8: Нажатие кнопки 'Создать резюме' и отправка формы"):
            resume.submit_resume_button.click()
            open_create_resume_page.wait_for_url(expected_list_url, timeout=30000)
            open_create_resume_page.wait_for_load_state("domcontentloaded")

        try:
            with allure.step("Шаг 9: Переход на форму редактирования созданного резюме"):
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
                expect(resume.derivative_update_dropdown).to_have_value("1", timeout=5000)
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
                open_create_resume_page.wait_for_timeout(1500)

                current_url = open_create_resume_page.url
                match = re.search(r"/resume/(\d+)/", current_url)
                created_id = match.group(1) if match else None

                open_create_resume_page.wait_for_timeout(1000)

                if "/update/" in current_url:
                    # Исправлено зависание: принудительно снижаем строгость ожидания главной страницы
                    open_create_resume_page.goto(expected_list_url, wait_until="domcontentloaded")
                    open_create_resume_page.wait_for_load_state("domcontentloaded")

                if not created_id:
                    last_link = open_create_resume_page.locator(
                        "a[href*='/registration/job-seeker/resume/'][href$='/update/']"
                    ).last
                    href_value = last_link.get_attribute("href")
                    match = re.search(r"/resume/(\d+)/", href_value)
                    created_id = match.group(1) if match else None

                open_create_resume_page.wait_for_timeout(1000)
                resume.last_resume_delete_btn.click()

                open_create_resume_page.wait_for_timeout(1000)
                resume.popup_confirm_delete_btn.click()
                open_create_resume_page.wait_for_load_state("networkidle")

            with allure.step("ОР 3: Удаленное резюме полностью исчезло из списка"):
                open_create_resume_page.wait_for_timeout(1000)
                deleted_resume_link = open_create_resume_page.locator(
                    f"a[href*='/registration/job-seeker/resume/{created_id}/update/']"
                )
                expect(deleted_resume_link).not_to_be_visible(timeout=5000)