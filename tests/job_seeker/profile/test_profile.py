from datetime import datetime
import allure
from playwright.sync_api import Page, expect
from pages.profile_page import ProfilePage
from utils.helpers import calculate_expected_age, generate_test_date, format_phone_to_mask


@allure.epic("Личный кабинет соискателя")
@allure.feature("Редактирование профиля")
class TestProfilePart1:

    @allure.title("Проверка дефолтных ФИО соискателя из конфигурации")
    def test_check_profile_default_values(self, open_profile_page: Page, app_config):
        profile = ProfilePage(open_profile_page)

        with allure.step("Загрузка дефолтных данных из конфига"):
            profile_data = app_config["default_profile"]

        with allure.step("Проверка совпадения ФИО на странице с конфигом"):
            expect(profile.last_name_input).to_have_value(profile_data["last_name"])
            expect(profile.first_name_input).to_have_value(profile_data["first_name"])
            expect(profile.middle_name_input).to_have_value(profile_data["middle_name"])

    @allure.title("Изменение ФИО соискателя с последующим восстановлением")
    def test_edit_fio_block(self, open_profile_page: Page, app_config):
        profile = ProfilePage(open_profile_page)
        profile_data = app_config["default_profile"]
        test_fio = app_config["profile_test_data"]["edit_fio"]

        with allure.step("Шаг 1: Изменение ФИО на тестовые значения"):
            profile.fill_field_safely(profile.last_name_input, test_fio["last_name"])
            profile.fill_field_safely(profile.first_name_input, test_fio["first_name"])
            profile.fill_field_safely(profile.middle_name_input, test_fio["middle_name"])
            profile.save_changes()

        with allure.step("ОР 1: Проверка, что на странице отображаются тестовые ФИО"):
            expect(profile.last_name_input).to_have_value(test_fio["last_name"])
            expect(profile.first_name_input).to_have_value(test_fio["first_name"])
            expect(profile.middle_name_input).to_have_value(test_fio["middle_name"])

        with allure.step("Шаг 2: Восстановление исходных ФИО"):
            profile.fill_field_safely(profile.last_name_input, profile_data["last_name"])
            profile.fill_field_safely(profile.first_name_input, profile_data["first_name"])
            profile.fill_field_safely(profile.middle_name_input, profile_data["middle_name"])
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата ФИО к дефолтным значениям"):
            expect(profile.last_name_input).to_have_value(profile_data["last_name"])
            expect(profile.first_name_input).to_have_value(profile_data["first_name"])
            expect(profile.middle_name_input).to_have_value(profile_data["middle_name"])

    @allure.title("Параметризованное изменение статуса соискателя: {test_status}")
    def test_edit_status_dropdown(self, open_profile_page: Page, test_status):
        profile = ProfilePage(open_profile_page)
        default_status = "Рассматриваю предложения"

        with allure.step(f"Шаг 1: Выбор тестового статуса: '{test_status}'"):
            profile.select_from_dropdown(profile.status_dropdown, test_status)
            profile.save_changes()

        with allure.step("ОР 1: Проверка отображения нового статуса"):
            expect(profile.status_dropdown).to_have_text(test_status)

        with allure.step("Шаг 2: Восстановление дефолтного статуса"):
            profile.select_from_dropdown(profile.status_dropdown, default_status)
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата статуса в исходное состояние"):
            expect(profile.status_dropdown).to_have_text(default_status)

    @allure.title("Динамическое изменение пола соискателя")
    def test_edit_gender_radio(self, open_profile_page: Page):
        profile = ProfilePage(open_profile_page)

        with allure.step("Определение текущего выбранного пола на странице"):
            if profile.gender_male_input.is_checked():
                initial_gender, test_gender = "M", "F"
            else:
                initial_gender, test_gender = "F", "M"

        with allure.step(f"Шаг 1: Смена пола на противоположный ({test_gender})"):
            profile.select_gender(test_gender)
            profile.save_changes()

        with allure.step("ОР 1: Проверка активации нужной радиокнопки"):
            if test_gender == "M":
                expect(profile.gender_male_input).to_be_checked()
            else:
                expect(profile.gender_female_input).to_be_checked()

        with allure.step(f"Шаг 2: Восстановление исходного пола ({initial_gender})"):
            profile.select_gender(initial_gender)
            profile.save_changes()

        with allure.step("ОР 2: Проверка успешного возврата к исходному полу"):
            if initial_gender == "M":
                expect(profile.gender_male_input).to_be_checked()
            else:
                expect(profile.gender_female_input).to_be_checked()

    @allure.title("Ручной ввод даты рождения и динамический пересчет возраста")
    def test_edit_date_of_birth_manual(self, open_profile_page: Page, app_config):
        profile = ProfilePage(open_profile_page)

        with allure.step("Подготовка тестовых дат и расчет ожидаемого возраста"):
            default_date = app_config["default_profile"]["date_of_birth"]
            expected_default_age = calculate_expected_age(default_date)
            test_date = generate_test_date(default_date, years_diff=-5)
            expected_test_age = calculate_expected_age(test_date)

            test_date_iso = "-".join(test_date.split(".")[::-1])
            default_date_iso = "-".join(default_date.split(".")[::-1])

        with allure.step(f"Шаг 1: Очистка поля и ввод тестовой даты: {test_date}"):
            profile.date_of_birth_input.click()
            open_profile_page.keyboard.press("Control+A")
            open_profile_page.keyboard.press("Backspace")
            profile.date_of_birth_input.press_sequentially(test_date, delay=50)
            profile.age_display.click()
            profile.save_changes()

        with allure.step("ОР 1: Проверка даты в формате ISO и нового возраста"):
            expect(profile.date_of_birth_input).to_have_value(test_date_iso)
            expect(profile.age_display).to_have_text(expected_test_age)

        with allure.step(f"Шаг 2: Восстановление дефолтной даты: {default_date}"):
            profile.date_of_birth_input.click()
            open_profile_page.keyboard.press("Control+A")
            open_profile_page.keyboard.press("Backspace")
            profile.date_of_birth_input.press_sequentially(default_date, delay=50)
            profile.age_display.click()
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата к дефолтной дате в ISO и старому возрасту"):
            expect(profile.date_of_birth_input).to_have_value(default_date_iso)
            expect(profile.age_display).to_have_text(expected_default_age)

    @allure.epic("Личный кабинет соискателя")
    @allure.feature("Редактирование профиля")
    class TestProfilePart2:

        @allure.title("Изменение даты рождения через интерфейс календаря")
        def test_edit_date_of_birth_via_calendar_ui(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)

            with allure.step("Подготовка ожидаемой даты в формате ISO"):
                default_date_str = app_config["default_profile"]["date_of_birth"]
                default_date_obj = datetime.strptime(default_date_str, "%d.%m.%Y")
                default_date_iso = default_date_obj.strftime("%Y-%m-%d")

            with allure.step("Шаг 1: Открытие календаря и выбор дня стрелками"):
                profile.date_of_birth_input.click()
                open_profile_page.keyboard.press("Alt+ArrowDown")
                open_profile_page.wait_for_timeout(500)
                open_profile_page.keyboard.press("ArrowLeft")
                open_profile_page.wait_for_timeout(300)
                open_profile_page.keyboard.press("Enter")
                open_profile_page.wait_for_timeout(500)
                open_profile_page.keyboard.press("Tab")
                open_profile_page.wait_for_timeout(500)
                profile.save_changes()

            with allure.step(f"Шаг 2: Восстановление исходной даты ручным вводом: {default_date_str}"):
                profile.date_of_birth_input.click()
                open_profile_page.keyboard.press("Control+A")
                open_profile_page.keyboard.press("Backspace")
                profile.date_of_birth_input.press_sequentially(default_date_str, delay=50)
                profile.age_display.click()
                profile.save_changes()

            with allure.step("ОР: Проверка успешного возвращения к исходной дате"):
                expect(profile.date_of_birth_input).to_have_value(default_date_iso)

        @allure.title("Параметризованное изменение уровня образования: {test_education}")
        def test_edit_education_dropdown(self, open_profile_page: Page, app_config, test_education):
            profile = ProfilePage(open_profile_page)
            default_education = app_config["default_profile"]["education"]

            with allure.step(f"Шаг 1: Выбор тестового образования: '{test_education}'"):
                profile.select_from_dropdown(profile.education_dropdown, test_education)
                profile.save_changes()

            with allure.step("ОР 1: Проверка нового значения на странице"):
                expect(profile.education_dropdown).to_have_text(test_education)

            with allure.step("Шаг 2: Возврат дефолтного значения обратно"):
                profile.select_from_dropdown(profile.education_dropdown, default_education)
                profile.save_changes()

            with allure.step("ОР 2: Проверка возврата образования в исходное состояние"):
                expect(profile.education_dropdown).to_have_text(default_education)

        @allure.title("Каскадное изменение полного адреса проживания")
        def test_edit_full_address_cascade(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)
            default = app_config["default_profile"]
            test_addr = app_config["profile_test_data"]["edit_address"]

            with allure.step("Шаг 1: Последовательная установка тестового региона, района и города"):
                profile.select_from_dropdown(profile.region_dropdown, test_addr["region"])
                expect(profile.region_dropdown).to_have_text(test_addr["region"])
                open_profile_page.wait_for_timeout(1000)

                profile.select_from_dropdown(profile.district_dropdown, test_addr["district"])
                expect(profile.district_dropdown).to_have_text(test_addr["district"])
                open_profile_page.wait_for_timeout(1000)

                profile.select_from_dropdown(profile.address_dropdown, test_addr["address"])
                profile.save_changes()

            with allure.step("ОР 1: Проверка отображения полного тестового адреса"):
                expect(profile.region_dropdown).to_have_text(test_addr["region"])
                expect(profile.district_dropdown).to_have_text(test_addr["district"])
                expect(profile.address_dropdown).to_have_text(test_addr["address"])

            with allure.step("Шаг 2: Восстановление дефолтных значений адреса"):
                profile.select_from_dropdown(profile.region_dropdown, default["region"])
                expect(profile.region_dropdown).to_have_text(default["region"])
                open_profile_page.wait_for_timeout(1000)

                profile.select_from_dropdown(profile.district_dropdown, default["district"])
                expect(profile.district_dropdown).to_have_text(default["district"])
                open_profile_page.wait_for_timeout(1000)

                profile.select_from_dropdown(profile.address_dropdown, default["address"])
                profile.save_changes()

            with allure.step("ОР 2: Проверка возврата адреса к исходным значениям"):
                expect(profile.region_dropdown).to_have_text(default["region"])
                expect(profile.district_dropdown).to_have_text(default["district"])
                expect(profile.address_dropdown).to_have_text(default["address"])

        @allure.title("Изменение email для рассылок")
        def test_edit_email_message(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)
            default_email = app_config["default_profile"]["email_sent"]
            test_email = app_config["profile_test_data"]["edit_contacts"]["test_email"]

            with allure.step(f"Шаг 1: Изменение email на тестовый: {test_email}"):
                profile.fill_field_safely(profile.email_message_input, test_email)
                profile.save_changes()

            with allure.step("ОР 1: Проверка сохранения нового email"):
                expect(profile.email_message_input).to_have_value(test_email)

            with allure.step(f"Шаг 2: Возврат к дефолтному email: {default_email}"):
                profile.fill_field_safely(profile.email_message_input, default_email)
                profile.save_changes()

            with allure.step("ОР 2: Проверка возврата email к дефолтному значению"):
                expect(profile.email_message_input).to_have_value(default_email)

        @allure.title("Негативный тест: Попытка изменения email на уже занятый")
        def test_edit_email_already_taken_negative(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)
            default_email = app_config["default_profile"]["email_sent"]
            taken_email = app_config["profile_test_data"]["negative_contacts"]["already_taken_email"]

            with allure.step(f"Шаг 1: Ввод занятого email: {taken_email}"):
                profile.fill_field_safely(profile.email_message_input, taken_email)
                profile.save_changes()

            with allure.step("ОР: Отображение красной плашки и ошибки 'Email занят' под полем"):
                expect(profile.error_alert).to_be_visible()
                expect(profile.email_error_message).to_have_text("Email занят")

            with allure.step("Шаг 2: Восстановление дефолтного email"):
                profile.fill_field_safely(profile.email_message_input, default_email)
                profile.save_changes()
                expect(profile.email_message_input).to_have_value(default_email)

    @allure.epic("Личный кабинет соискателя")
    @allure.feature("Редактирование профиля")
    class TestProfilePart3:

        @allure.title("Изменение основного телефона с проверкой маски")
        def test_edit_main_phone(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)
            test_phone = app_config["profile_test_data"]["edit_contacts"]["test_main_phone"]

            with allure.step("Считывание текущего телефона и форматирование маски"):
                initial_phone = profile.main_phone_input.input_value()
                expected_test_phone = format_phone_to_mask(test_phone)

            with allure.step(f"Шаг 1: Ввод нового основного номера: {test_phone}"):
                profile.fill_field_safely(profile.main_phone_input, test_phone)
                profile.save_changes()

            with allure.step("ОР 1: Проверка сохранения телефона с применением маски"):
                expect(profile.main_phone_input).to_have_value(expected_test_phone)

            with allure.step("Шаг 2: Восстановление первоначального номера"):
                profile.fill_field_safely(profile.main_phone_input, initial_phone)
                profile.save_changes()

            with allure.step("ОР 2: Проверка возврата номера в исходное состояние"):
                expect(profile.main_phone_input).to_have_value(initial_phone)

        @allure.title("Добавление и последующее удаление дополнительного номера телефона")
        def test_add_and_delete_additional_phone(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)
            contacts = app_config["profile_test_data"]["edit_contacts"]
            mask_phone_2 = format_phone_to_mask(contacts["additional_phone_2"])

            with allure.step("Шаг 1: Удаление пустого дефолтного поля"):
                profile.delete_phone_button_0.click()
                open_profile_page.wait_for_timeout(300)

            with allure.step("Шаг 2: Создание чистого поля через кнопку добавления"):
                profile.add_phone_button.click()
                expect(profile.additional_phone_0).to_be_visible(timeout=3000)

            with allure.step(f"Шаг 3: Ввод телефона {contacts['additional_phone_2']} и сохранение"):
                profile.fill_field_safely(profile.additional_phone_0, contacts["additional_phone_2"])
                profile.save_changes()

            with allure.step("ОР: Проверка успешного сохранения дополнительного телефона"):
                expect(profile.additional_phone_0).to_have_value(mask_phone_2)

            with allure.step("Шаг 4: Возврат формы в исходный вид (удаление номера крестиком)"):
                profile.delete_phone_button_0.click()
                profile.save_changes()

            with allure.step("Проверка полного очищения поля"):
                expect(profile.additional_phone_0).to_have_value("")

        @allure.title("Негативный тест: Попытка изменения телефона на уже занятый")
        def test_edit_phone_already_taken_negative(self, open_profile_page: Page, app_config):
            profile = ProfilePage(open_profile_page)
            taken_phone = app_config["profile_test_data"]["negative_contacts"]["already_taken_phone"]
            expected_error = "На указанный номер телефона уже зарегистрирован другой личный кабинет. Введите другой номер или войдите в существующий кабинет."

            with allure.step("Фиксация текущего телефона профиля перед тестом"):
                initial_phone = profile.main_phone_input.input_value()

            with allure.step(f"Шаг 1: Ввод занятого телефона: {taken_phone}"):
                profile.fill_field_safely(profile.main_phone_input, taken_phone)
                profile.save_changes()

            with allure.step("ОР: Отображение красной плашки и развернутого текста ошибки под полем"):
                expect(profile.error_alert).to_be_visible()
                expect(profile.phone_error_message).to_have_text(expected_error)

            with allure.step("Шаг 2: Восстановление исходного телефона"):
                profile.fill_field_safely(profile.main_phone_input, initial_phone)
                profile.save_changes()

            with allure.step("Проверка успешного восстановления номера"):
                expect(profile.main_phone_input).to_have_value(initial_phone)

        @allure.title("Проверка кликабельности чек-бокса скрытия ФИО")
        def test_click_privacy_checkbox(self, open_profile_page: Page):
            profile = ProfilePage(open_profile_page)

            with allure.step("Шаг 1: Активация чек-бокса 'Скрыть ФИО'"):
                profile.privacy_checkbox.dispatch_event("click")
                profile.save_changes()

            with allure.step("ОР 1: Чек-бокс успешно активен"):
                expect(profile.privacy_checkbox).to_be_checked()

            with allure.step("Шаг 2: Деактивация чек-бокса (возврат в исходное состояние)"):
                profile.privacy_checkbox.dispatch_event("click")
                profile.save_changes()

            with allure.step("ОР 2: Чек-бокс успешно снят"):
                expect(profile.privacy_checkbox).not_to_be_checked()

