from playwright.sync_api import Page, expect


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
        # Инпуты для проверки состояния (expect)
        self.gender_male_input = page.locator("#id_gender_0")
        self.gender_female_input = page.locator("#id_gender_1")

        # Текстовые надписи (лейблы) для выполнения клика
        self.gender_male_label = page.locator("label[for='id_gender_0']")
        self.gender_female_label = page.locator("label[for='id_gender_1']")

        # --- Кнопки и уведомления (Вернули на место) ---
        self.save_button = page.get_by_role("button", name="Сохранить")
        self.success_alert = page.locator("div.dj-message.alert-success")

        # Поле ввода даты рождения и элемент отображения возраста
        self.date_of_birth_input = page.locator("#id_date_of_birth")
        self.age_display = page.locator("#age-display")

        # Контейнер выпадающего списка образования
        self.education_dropdown = page.locator("#select2-id_education-container")

    def fill_field_safely(self, locator, text: str):
        """Очищает поле и вводит новый текст через клавиатуру."""
        locator.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        locator.press_sequentially(text, delay=30)

    def select_from_dropdown(self, dropdown_locator, option_text: str):
        """Выбор значения из Select2 с фиксацией фокуса и ожидания скриптов плагина."""
        dropdown_locator.click()
        self.search_popup.wait_for(state="visible", timeout=5000)

        # Вводим текст
        self.search_popup.press_sequentially(option_text, delay=50)

        # 🕒 ДАЕМ ВРЕМЯ СКРИПТУ: 500 мс, чтобы сайт успел отфильтровать список на экране
        self.page.wait_for_timeout(500)

        # Ищем отфильтрованную опцию Select2 по тегу li и её тексту
        target_option = self.page.locator("li.select2-results__option", has_text=option_text).first
        target_option.wait_for(state="visible", timeout=3000)

        # Наводим фокус и кликаем
        target_option.focus()
        target_option.click()

        # Даем плагину Select2 закрыть список и обновить HTML-форму
        self.page.wait_for_timeout(300)

    def select_gender(self, gender_code: str):
        """Выбирает пол на форме, кликая строго по тексту внутри лейбла."""
        if gender_code.lower() == "m":
            # Ищем текст "Мужской" внутри контейнера формы
            self.page.get_by_text("Мужской", exact=True).click()
        else:
            # Ищем текст "Женский" внутри контейнера формы
            self.page.get_by_text("Женский", exact=True).click()

        self.page.wait_for_timeout(500)

        # Стабилизируем анимацию переключения кастомного кружка на сайте перед сохранением
        self.page.wait_for_timeout(500)

    def save_changes(self):
        """Метод сохранения формы со встроенным ожиданием перезагрузки страницы."""
        with self.page.expect_navigation(wait_until="domcontentloaded"):
            self.save_button.click(force=True)

        expect(self.success_alert).to_be_visible(timeout=5000)
        # Защита от ошибки 503 на сервере
        self.page.wait_for_timeout(1500)

    def set_date_of_birth(self, date_str: str):
        """Заполняет дату рождения в формате ГГГГ-ММ-ДД."""
        self.date_of_birth_input.click()
        self.date_of_birth_input.fill(date_str)
        # Кликаем по тексту возраста, чтобы убрать фокус с даты и спровоцировать перерасчет
        self.age_display.click()

    def open_builtin_calendar(self):
        """Открывает встроенный браузерный календарь через горячие клавиши."""
        self.date_of_birth_input.click()
        # Посылаем комбинацию Alt+ArrowDown для открытия виджета календаря
        self.page.keyboard.press("Alt+ArrowDown")
        self.page.wait_for_timeout(500)
