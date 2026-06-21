from playwright.sync_api import Page
import logging

class ProfilePage:
    def __init__(self, page: Page):
        self.page = page

        # --- ФИО (текстовые поля) ---
        self.last_name_input = page.locator("#id_last_name")
        self.first_name_input = page.locator("#id_first_name")
        self.middle_name_input = page.locator("#id_patronymic")

        # --- Выпадающие списки Select2 ---
        self.status_dropdown = page.locator("#select2-id_status-container")
        self.address_input = page.locator("#id_address")
        self.search_popup = page.get_by_role("searchbox")

        # --- Радиокнопки выбора пола ---
        self.gender_male_input = page.locator("#id_gender_0")
        self.gender_female_input = page.locator("#id_gender_1")
        self.gender_male_label = page.locator("label[for='id_gender_0']")
        self.gender_female_label = page.locator("label[for='id_gender_1']")

        # --- Кнопки и уведомления ---
        self.save_button = page.get_by_role("button", name="Сохранить")
        self.success_alert = page.locator("div.dj-message.alert-success")
        self.error_alert = page.locator("div.dj-message.alert-danger")

        # Поле ввода даты рождения и элемент отображения возраста
        self.date_of_birth_input = page.locator("#id_date_of_birth")
        self.age_display = page.locator("#age-display")

        # Контейнер выпадающего списка образования
        self.education_dropdown = page.locator("#select2-id_education-container")

        # --- Адресные выпадающие списки Select2 ---
        self.region_dropdown = page.locator("#select2-id_region-container")
        self.district_dropdown = page.locator("#select2-id_district-container")
        self.address_dropdown = page.locator("#select2-id_village_council-container")

        # --- Блок контактной информации ---
        self.email_message_input = page.locator("#id_email_for_message")
        self.main_phone_input = page.locator("#id_phone")

        # Кнопка добавления и существующее первое дополнительное поле
        self.add_phone_button = page.locator("button[data-formset-add]")
        self.additional_phone_0 = page.locator("input[id^='id_phone-'][id$='-number']").filter(visible=True).first

        # Красный крестик удаления (берем первый, так как он привязан к нулевому полю)
        self.delete_phone_button_0 = page.locator("button[data-formset-delete-button]").first

        # --- Локаторы ошибок валидации ---
        self.email_error_message = page.locator(".form-group:has(#id_email_for_message) div.invalid-feedback")
        self.phone_error_message = page.locator(".form-group:has(#id_phone) div.invalid-feedback")

        self.privacy_checkbox = self.page.get_by_label("Скрыть ФИО")

    def fill_field_safely(self, locator, text: str):
        """Очищает поле и вводит новый текст через клавиатуру."""
        logging.debug(f"Действие: Заполнение поля текстом '{text}'")
        locator.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        locator.press_sequentially(text, delay=30)

    def select_from_dropdown(self, dropdown_locator, option_text: str):
        """Выбор значения из Select2 с фиксацией фокуса и ожидания скриптов плагина."""
        logging.debug(f"Действие: Выбор опции '{option_text}' из выпадающего списка")
        dropdown_locator.click()
        self.search_popup.wait_for(state="visible", timeout=5000)
        self.search_popup.press_sequentially(option_text, delay=100)
        self.page.wait_for_timeout(1000)

        target_option = self.page.locator("li.select2-results__option", has_text=option_text).first
        target_option.wait_for(state="visible", timeout=3500)
        target_option.focus()
        target_option.click()
        self.page.wait_for_timeout(600)

    def select_gender(self, gender_code: str):
        """Выбирает пол на форме, кликая строго по тексту внутри лейбла."""
        logging.debug(f"Действие: Переключение пола на код '{gender_code}'")
        if gender_code.lower() == "m":
            self.page.get_by_text("Мужской", exact=True).click()
        else:
            self.page.get_by_text("Женский", exact=True).click()
        self.page.wait_for_timeout(500)
        self.page.wait_for_timeout(500)

    def save_changes(self):
        """Сбрасывает фокус, дает бэкенду сайта время переварить AJAX-валидацию и сохраняет форму."""
        logging.debug("Действие: Нажатие кнопки 'Сохранить' изменения профиля")
        self.page.locator("h1, h2, label").first.click(force=True)
        self.page.wait_for_timeout(1000)
        self.save_button.click()
        final_alert = self.page.locator("div.dj-message.alert-success, div.dj-message.alert-danger")
        final_alert.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)

    def set_date_of_birth(self, date_str: str):
        """Заполняет дату рождения в формате ГГГГ-ММ-ДД."""
        logging.debug(f"Действие: Установка даты рождения '{date_str}'")
        self.date_of_birth_input.click()
        self.date_of_birth_input.fill(date_str)
        self.age_display.click()

    def open_builtin_calendar(self):
        """Открывает встроенный браузерный календарь через горячие клавиши."""
        logging.debug("Действие: Раскрытие встроенного виджета календаря")
        self.date_of_birth_input.click()
        self.page.keyboard.press("Alt+ArrowDown")
        self.page.wait_for_timeout(500)
