import pytest
import allure
from playwright.sync_api import Page, expect
from pages.resume_page import ResumePage
from utils.helpers import calculate_expected_age
import re


@allure.epic("Личный кабинет соискателя")
@allure.feature("Создание резюме")
class TestResumeProfileBlock:

    @allure.title("Сверка автоматических данных профиля на форме резюме с конфигурацией")
    def test_verify_profile_data_in_resume(self, open_create_resume_page: Page, app_config):
        resume = ResumePage(open_create_resume_page)

        with allure.step("Загрузка ожидаемых дефолтных данных и расчет возраста"):
            default_data = app_config["default_profile"]
            expected_age_digits = calculate_expected_age(default_data["date_of_birth"]).split()[0]

        with allure.step("Проверка заблокированных текстовых полей ФИО и динамического возраста"):
            expect(resume.last_name_input).to_have_value(default_data["last_name"])
            expect(resume.first_name_input).to_have_value(default_data["first_name"])
            expect(resume.middle_name_input).to_have_value(default_data["middle_name"])
            expect(resume.age_input).to_have_value(expected_age_digits)

        with allure.step("Проверка выбранного уровня образования"):
            expect(resume.education_dropdown).to_have_value("2")

        with allure.step("Проверка отображения адреса проживания в контейнерах"):
            expect(resume.region_container).to_have_text(default_data["region"])
            expect(resume.district_container).to_have_text(default_data["district"])
            expect(resume.address_container).to_have_text(default_data["address"])

        with allure.step("Проверка начального состояния чек-бокса 'Скрыть ФИО'"):
            expect(resume.privacy_checkbox).not_to_be_checked()

    @allure.title("Проверка кликабельности чек-бокса согласия на переезд")
    def test_click_relocate_checkbox(self, open_create_resume_page: Page):
        resume = ResumePage(open_create_resume_page)

        with allure.step("Шаг 1: Активация чек-бокса согласия на переезд"):
            resume.relocate_checkbox.dispatch_event("click")

        with allure.step("ОР 1: Чек-бокс успешно активен"):
            expect(resume.relocate_checkbox).to_be_checked()

        with allure.step("Шаг 2: Деактивация чек-бокса (возврат в исходное состояние)"):
            resume.relocate_checkbox.dispatch_event("click")

        with allure.step("ОР 2: Чек-бокс успешно снят"):
            expect(resume.relocate_checkbox).not_to_be_checked()

    @allure.title("Проверка дефолтного Email и добавления дополнительного поля Email")
    def test_verify_email_and_add_field(self, open_create_resume_page: Page, app_config):
        resume = ResumePage(open_create_resume_page)
        default_email = app_config["default_profile"]["email_sent"]

        with allure.step("Шаг 1: Проверка, что первый Email совпадает с профилем"):
            expect(resume.email_input_0).to_have_value(default_email)

        with allure.step("Шаг 2: Клик по кнопке 'Добавить E-mail'"):
            resume.add_email_button.click()

        with allure.step("ОР: Появилось второе пустое поле для ввода Email"):
            # Локатор для второго поля формируется динамически с индексом 1
            second_email_input = open_create_resume_page.locator("#id_resume_emails-1-email")
            expect(second_email_input).to_be_visible(timeout=3000)
            expect(second_email_input).to_have_value("")

    @allure.title("Проверка добавления и удаления динамических полей контактов")
    def test_add_and_delete_dynamic_contacts(self, open_create_resume_page: Page):
        resume = ResumePage(open_create_resume_page)

        with allure.step("Шаг 1: Добавление поля телефона и второго Email"):
            resume.add_phone_button.click()
            resume.add_email_button.click()

        with allure.step("ОР 1: Поля успешно отображаются на форме"):
            expect(resume.phone_input_0).to_be_visible(timeout=3000)

            # Локатор для второго email, который мы уже проверяли
            second_email = open_create_resume_page.locator("#id_resume_emails-1-email")
            expect(second_email).to_be_visible(timeout=3000)

        with allure.step("Шаг 2: Удаление добавленных полей через крестики"):
            resume.delete_phone_button_0.click()
            resume.delete_email_button_1.click()

        with allure.step("ОР 2: Динамические поля исчезли из интерфейса"):
            expect(resume.phone_input_0).not_to_be_visible()
            expect(second_email).not_to_be_visible()

    @allure.epic("Личный кабинет соискателя")
    @allure.feature("Создание резюме")
    class TestResumeJobRequirements:

        @allure.title("Выбор желаемой профессии и производной должности")
        def test_select_profession_and_derivative(self, open_create_resume_page: Page):
            resume = ResumePage(open_create_resume_page)
            test_profession = "Авербандщик"

            with allure.step("Шаг 1: Проверка дефолтного текста-подсказки (плейсхолдера)"):
                expect(resume.profession_container).to_have_text(
                    "Введите наименование должности служащего, профессии рабочего"
                )

            with allure.step(f"Шаг 2: Клик по дропдауну и ввод текста для поиска: '{test_profession}'"):
                resume.profession_container.click()
                resume.select2_search_input.press_sequentially(test_profession, delay=100)
                open_create_resume_page.wait_for_timeout(500)

            with allure.step(f"Шаг 3: Выбор найденного варианта '{test_profession}'"):
                resume.select2_first_option.click()

            with allure.step("ОР 1: Выбранная профессия успешно отображается в контейнере"):
                expect(resume.profession_container).to_have_text(
                    re.compile(test_profession)
                )

            with allure.step("Шаг 4: Выбор производной должности 'Старший'"):
                # Выбираем по атрибуту value="1"
                resume.derivative_dropdown.select_option("1")

            with allure.step("ОР 2: Производная должность успешно выбрана"):
                expect(resume.derivative_dropdown).to_have_value("1")

        @allure.title("Ввод желаемой заработной платы в поле ввода")
        def test_enter_desired_salary(self, open_create_resume_page: Page):
            resume = ResumePage(open_create_resume_page)
            test_salary = "1500.50"

            with allure.step("Шаг 1: Проверка начального плейсхолдера"):
                expect(resume.salary_input).to_have_attribute(
                    "placeholder", "00000.00"
                )

            with allure.step(f"Шаг 2: Ввод тестовой суммы: {test_salary}"):
                resume.salary_input.fill(test_salary)

            with allure.step("ОР: Сумма успешно отображается в поле ввода"):
                expect(resume.salary_input).to_have_value(test_salary)

        @allure.title("Выбор характера работы и режима рабочего времени")
        def test_select_work_conditions(self, open_create_resume_page: Page):
            resume = ResumePage(open_create_resume_page)

            with allure.step("Шаг 1: Проверка дефолтных значений 'Любой'"):
                expect(resume.employment_nature_dropdown).to_have_value("")
                expect(resume.work_mode_dropdown).to_have_value("")

            with allure.step("Шаг 2: Выбор характера работы 'Постоянная'"):
                resume.employment_nature_dropdown.select_option("1")

            with allure.step("Шаг 3: Выбор режима рабочего времени 'Одна смена'"):
                resume.work_mode_dropdown.select_option("1")

            with allure.step("ОР: Новые условия работы успешно выбраны в списках"):
                expect(resume.employment_nature_dropdown).to_have_value("1")
                expect(resume.work_mode_dropdown).to_have_value("1")

        @allure.title("Проверка кликабельности чек-бокса требования жилья")
        def test_click_housing_checkbox(self, open_create_resume_page: Page):
            resume = ResumePage(open_create_resume_page)

            with allure.step("Шаг 1: Проверка начального состояния чек-бокса"):
                expect(resume.housing_checkbox).not_to_be_checked()

            with allure.step("Шаг 2: Активация чек-бокса 'Требуется жилье'"):
                resume.housing_checkbox.dispatch_event("click")

            with allure.step("ОР 1: Чек-бокс успешно активен"):
                expect(resume.housing_checkbox).to_be_checked()

            with allure.step("Шаг 3: Деактивация чек-бокса"):
                resume.housing_checkbox.dispatch_event("click")

            with allure.step("ОР 2: Чек-бокс успешно снят"):
                expect(resume.housing_checkbox).not_to_be_checked()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeExperience:

            @allure.title("Динамическое добавление и удаление блока опыта работы")
            def test_add_and_remove_experience_block(self, open_create_resume_page: Page):
                resume = ResumePage(open_create_resume_page)

                with allure.step("Шаг 1: Клик по кнопке 'Добавить место работы'"):
                    resume.add_experience_button.click()

                with allure.step("ОР 1: Все поля опыта работы стали видимы соискателю"):
                    expect(resume.exp_org_input).to_be_visible(timeout=3000)
                    expect(resume.exp_years_input).to_be_visible()
                    expect(resume.exp_months_input).to_be_visible()
                    expect(resume.exp_profession_input).to_be_visible()
                    expect(resume.exp_duties_input).to_be_visible()
                    expect(resume.exp_additional_textarea).to_be_visible()

                with allure.step("Шаг 2: Клик по кнопке-крестику удаления блока"):
                    resume.delete_experience_button_0.click()

                with allure.step("ОР 2: Блок опыта работы успешно исчез с формы"):
                    expect(resume.exp_org_input).not_to_be_visible()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeEducation:

            @allure.title("Динамическое добавление и удаление блока места обучения")
            def test_add_and_remove_education_block(self, open_create_resume_page: Page):
                resume = ResumePage(open_create_resume_page)

                with allure.step("Шаг 1: Клик по кнопке 'Добавить место обучения'"):
                    resume.add_education_button.click()

                with allure.step("ОР 1: Все поля образования стали видимы"):
                    expect(resume.edu_name_input).to_be_visible(timeout=3000)
                    expect(resume.edu_specialty_input).to_be_visible()
                    expect(resume.edu_ending_input).to_be_visible()
                    expect(resume.edu_info_textarea).to_be_visible()

                with allure.step("Шаг 2: Клик по кнопке-крестику удаления блока"):
                    resume.delete_education_button_0.click()

                with allure.step("ОР 2: Блок места обучения успешно исчез с формы"):
                    expect(resume.edu_name_input).not_to_be_visible()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeLanguages:

            @allure.title("Выбор языка, его уровня, добавление и удаление новой строки")
            def test_select_language_and_level(self, open_create_resume_page: Page):
                resume = ResumePage(open_create_resume_page)

                with allure.step("Шаг 1: Проверка дефолтных пустых значений списка"):
                    expect(resume.language_dropdown).to_have_value("")
                    expect(resume.lang_level_dropdown).to_have_value("")

                with allure.step("Шаг 2: Изменение языка на 'Английский' (value='4')"):
                    resume.language_dropdown.select_option("4")

                with allure.step("Шаг 3: Изменение уровня на 'Продвинутый' (value='10')"):
                    resume.lang_level_dropdown.select_option("10")

                with allure.step("ОР 1: Новые языковые параметры успешно применились"):
                    expect(resume.language_dropdown).to_have_value("4")
                    expect(resume.lang_level_dropdown).to_have_value("10")

                with allure.step("Шаг 4: Клик по кнопке 'Добавить язык'"):
                    resume.add_language_button.click()

                with allure.step("ОР 2: Появилась вторая пустая строка для ввода языка"):
                    second_lang = open_create_resume_page.locator(
                        "#id_resume_languages-1-language"
                    )
                    expect(second_lang).to_be_visible(timeout=3000)
                    expect(second_lang).to_have_value("")

                with allure.step("Шаг 5: Удаление второй строки через крестик"):
                    resume.delete_language_button_1.click()

                with allure.step("ОР 3: Вторая строка языков успешно исчезла"):
                    expect(second_lang).not_to_be_visible()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeSkills:

            @allure.title("Выбор нескольких гибких навыков и удаление одного из них")
            def test_select_and_remove_skills(self, open_create_resume_page: Page):
                resume = ResumePage(open_create_resume_page)
                skill_1 = "Деловая коммуникация"
                skill_2 = "Адаптивность и гибкость"

                with allure.step("Шаг 1: Активация поля гибких навыков через клик"):
                    resume.skills_container.dispatch_event("click")
                    open_create_resume_page.wait_for_timeout(300)

                with allure.step(f"Шаг 2: Поиск и выбор первого навыка: '{skill_1}'"):
                    resume.skills_search_input.press_sequentially(skill_1, delay=100)
                    open_create_resume_page.wait_for_timeout(500)
                    resume.get_skill_option_by_text(skill_1).click()

                with allure.step("Шаг 3: Повторная активация поля (открытие списка вариантов)"):
                    resume.skills_container.dispatch_event("click")
                    open_create_resume_page.wait_for_timeout(300)

                with allure.step(f"Шаг 4: Выбор второго навыка напрямую из списка: '{skill_2}'"):
                    # Из-за бага с вводом кликаем по тексту сразу в открывшемся списке
                    resume.get_skill_option_by_text(skill_2).click()

                with allure.step("Шаг 5: Клик в пустую область для закрытия списка"):
                    resume.skills_container.dispatch_event("click")
                    open_create_resume_page.wait_for_timeout(300)

                with allure.step("ОР 1: Оба навыка успешно отображаются в поле"):
                    expect(resume.skills_container).to_contain_text(skill_1)
                    expect(resume.skills_container).to_contain_text(skill_2)

                with allure.step("Шаг 6: Удаление первого навыка через крестик"):
                    resume.skills_first_remove_btn.click()

                with allure.step(f"ОР 2: Навык '{skill_1}' успешно удален из списка"):
                    expect(resume.skills_container).not_to_contain_text(skill_1)
                    expect(resume.skills_container).to_contain_text(skill_2)

            @allure.title("Ввод дополнительной информации о соискателе")
            def test_enter_additional_information(self, open_create_resume_page: Page):
                resume = ResumePage(open_create_resume_page)
                test_text = "Ответственный сотрудник, готов к обучению и командировкам."

                with allure.step("Шаг 1: Проверка, что поле изначально пустое"):
                    expect(resume.additional_info_textarea).to_have_value("")

                with allure.step(f"Шаг 2: Ввод тестового текста: '{test_text}'"):
                    resume.additional_info_textarea.fill(test_text)

                with allure.step("ОР: Текст успешно отображается в поле ввода"):
                    expect(resume.additional_info_textarea).to_have_value(test_text)

        