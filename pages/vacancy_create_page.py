import logging
from playwright.sync_api import Page
from helpers.network_helper import retry_action


class VacancyCreatePage:
    def __init__(self, page: Page):
        self.page = page

        # Контактное лицо — select, опции которого содержат имя контактного лица
        self.contact_person_select = page.locator("select[id*='contact_person']")
        self.fio_input = page.locator("#id_fio")
        self.position_input = page.locator("#id_position")
        self.phone_input = page.locator("#id_phone_formset-0-phone")
        self.email_input = page.locator("#id_email")
        self.data_correct_checkbox = page.locator("#id_data_correct_confirmation")
        self.need_assistance_checkbox = page.locator("#id_need_assistance")

        # Профессия (Select2)
        self.profession_container = page.locator("#select2-id_profession-container")
        self.profession_search = page.locator(
            "input.select2-search__field[aria-controls*='profession']"
        )
        self.select2_first_option = page.locator(".select2-results__option").first
        self.derivative_select = page.locator("#id_derivative_post_or_profession")
        self.qualification_select = page.locator("#id_wage_or_qualification_category")

        # Сфера деятельности (Select2)
        self.activity_area_container = page.locator("#select2-id_activity_area-container")

        # Группа занятий (Select2)
        self.okz_group_container = page.locator("#select2-id_okz_group-container")

        # Количество мест
        self.available_places_input = page.locator("#id_available_places")
        self.budget_places_input = page.locator("#id_budget_places")
        self.public_works_input = page.locator("#id_public_works")
        self.for_students_input = page.locator("#id_for_students")
        self.invalid_quote_input = page.locator("#id_invalid_quote")
        self.reservation_input = page.locator("#id_reservation")

        # Зарплата и ставка
        self.wage_rate_input = page.locator("#id_wage_rate")
        self.salary_input = page.locator("#id_salary")
        self.salary_limit_input = page.locator("#id_salary_limit")
        self.additional_info_textarea = page.locator("#id_additional_info")

        # Адрес рабочего места (Select2)
        self.workplace_container = page.locator("#select2-id_workplace-container")

        # Условия работы
        self.work_mode_select = page.locator("#id_work_mode")
        self.for_foreigner_checkbox = page.locator("#id_for_foreigner")
        self.housing_checkbox = page.locator("#id_housing")
        # Условные чекбоксы жилья (появляются после активации housing)
        self.avaliable_housing_0 = page.locator("#id_avaliable_housing_0")
        self.avaliable_housing_1 = page.locator("#id_avaliable_housing_1")
        self.avaliable_housing_2 = page.locator("#id_avaliable_housing_2")
        self.temporary_for_students_checkbox = page.locator("#id_temporary_for_students")
        self.career_start_checkbox = page.locator("#id_career_start")
        # Условные чекбоксы возраста (появляются после активации career_start)
        self.age_choices_0 = page.locator("#id_age_choices_0")
        self.age_choices_1 = page.locator("#id_age_choices_1")
        self.age_choices_2 = page.locator("#id_age_choices_2")

        # Требования к кандидату
        self.education_select = page.locator("#id_education")
        self.experience_input = page.locator("#id_experience")

        # Языки (строка 0 уже видима при загрузке; «+» добавляет строку 1)
        self.language_select_0 = page.locator("#id_vacancy_languages-0-language")
        self.lang_level_select_0 = page.locator("#id_vacancy_languages-0-language_level")
        self.language_select_1 = page.locator("#id_vacancy_languages-1-language")
        self.lang_level_select_1 = page.locator("#id_vacancy_languages-1-language_level")
        self.add_language_button = page.get_by_role("button", name="Добавить язык")

        # Прочее
        self.car_needed_checkbox = page.locator("#id_car_needed")
        self.wishes_textarea = page.locator("#id_wishes")

        # Кнопка сохранения
        self.submit_button = page.get_by_role("button", name="Сохранить вакансию")

    def _select_s2(self, container_locator, search_text: str, label: str):
        """Выбор значения в Select2 с повтором при сбое."""
        def _pick():
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
            container_locator.scroll_into_view_if_needed()
            container_locator.click()
            s2_search = self.page.locator(
                ".select2-container--open input.select2-search__field"
            )
            s2_search.wait_for(state="visible", timeout=5000)
            s2_search.fill(search_text)
            # Ждём пока AJAX-индикатор загрузки исчезнет
            try:
                self.page.wait_for_function(
                    "!document.querySelector("
                    "'.select2-container--open .loading-results, "
                    ".select2-container--open .select2-results__option--loading')",
                    timeout=8000
                )
            except Exception:
                pass
            self.page.wait_for_timeout(500)
            option = self.page.locator(
                ".select2-container--open "
                "li.select2-results__option:not([aria-disabled='true'])"
            ).first
            option.wait_for(state="visible", timeout=8000)
            option.click()
            self.page.wait_for_timeout(700)

        retry_action(_pick, self.page, retries=3, label=f"выбор {label}='{search_text}'")

    def select_profession(self, profession_text: str):
        logging.debug(f"Действие: Выбор профессии '{profession_text}'")
        self._select_s2(self.profession_container, profession_text, "профессия")

    def select_activity_area_first(self):
        """Выбирает первый доступный вариант в дропдауне сферы деятельности."""
        logging.debug("Действие: Выбор первой сферы деятельности")
        self.page.keyboard.press("Escape")
        self.activity_area_container.click()
        first = self.page.locator(
            ".select2-container--open li.select2-results__option:not(.select2-results__option--disabled)"
        ).first
        first.wait_for(state="visible", timeout=5000)
        first.click()
        self.page.wait_for_timeout(300)

    def select_workplace(self, workplace_text: str):
        logging.debug(f"Действие: Выбор адреса рабочего места '{workplace_text}'")
        self._select_s2(self.workplace_container, workplace_text, "рабочее место")

    def set_workplace_by_id(self, workplace_id: int, workplace_text: str):
        """Устанавливает рабочее место через Select2 API (trigger select).
        Обновляет как скрытый <select>, так и внутреннее состояние Select2,
        чтобы pre-submit JS-хэндлер не обнулил значение."""
        logging.debug(f"Действие: Установка рабочего места id={workplace_id} через Select2 API")
        self.page.evaluate(f"""
            (function() {{
                // Canonical Select2 v4 approach: append option then trigger change.
                // This updates both the DOM <select> and Select2's internal state.
                var option = new Option('{workplace_text}', '{workplace_id}', true, true);
                jQuery('#id_workplace').append(option).trigger('change');
            }})();
        """)
        self.page.wait_for_timeout(800)
        # Верификация
        val = self.page.locator("#id_workplace").evaluate("el => el.value")
        if str(val) != str(workplace_id):
            raise AssertionError(
                f"set_workplace_by_id: ожидалось value='{workplace_id}', получили '{val}'"
            )

    def select_okz_group(self, group_text: str):
        """Выбирает группу занятий по тексту.
        Контейнер появляется в DOM только после выбора профессии (AJAX)."""
        logging.debug(f"Действие: Выбор группы занятий '{group_text}'")
        # Ждём появления контейнера в DOM (он рендерится после выбора профессии)
        self.page.wait_for_selector(
            "#select2-id_okz_group-container",
            state="visible",
            timeout=10000
        )
        self._select_s2(self.okz_group_container, group_text, "группа занятий")
