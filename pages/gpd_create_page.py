import logging
from playwright.sync_api import Page
from helpers.network_helper import retry_action


class GpdCreatePage:
    def __init__(self, page: Page):
        self.page = page

        # Предмет ГПД (Select2)
        self.type_gpd_container = page.locator("#select2-id_type_gpd-container")

        # Наименование работы/услуги
        self.work_type_input = page.locator("#id_work_type")

        # Сфера деятельности (Select2)
        self.area_container = page.locator("#select2-id_area-container")

        # Численность граждан
        self.number_person_input = page.locator("#id_number_person")

        # Жильё
        self.housing_checkbox = page.locator("#id_housing")
        self.avaliable_housing_0 = page.locator("#id_avaliable_housing_0")
        self.avaliable_housing_1 = page.locator("#id_avaliable_housing_1")
        self.avaliable_housing_2 = page.locator("#id_avaliable_housing_2")

        # Сумма и примечание
        self.salary_input = page.locator("#id_salary")
        self.comments_textarea = page.locator("#id_comments")

        # Кнопка
        self.submit_button = page.get_by_role("button", name="Создать вакансию")

    def _select_s2(self, container_locator, search_text: str, label: str):
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

    def select_type_gpd(self, label: str):
        logging.debug(f"Действие: Выбор предмета ГПД '{label}'")
        self._select_s2(self.type_gpd_container, label, "предмет ГПД")

    def select_area(self, label: str):
        logging.debug(f"Действие: Выбор сферы деятельности '{label}'")
        self._select_s2(self.area_container, label, "сфера деятельности")
