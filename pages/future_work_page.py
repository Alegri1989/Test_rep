from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class FutureWorkPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/future-vacancy/future-works/"

        # Основной блок поиска по профессии (аналогичен главной странице)
        self.search_input = page.locator("#id_profession")
        self.search_button = page.locator("button:has(.btn-title:has-text('Найти'))")

        # Фильтр территориально-административной иерархии (Область)
        self.region_dropdown = page.locator("span[aria-labelledby='select2-id_region-container']")
        self.region_selected_text = page.locator("#select2-id_region-container")

        # Заработная плата
        self.salary_min_input = page.locator("#id_salary_min")

        # Спойлеры фильтров Select2 (скрыты по умолчанию)
        self.work_time_mode_filter_title = "Режим рабочего времени"
        self.work_time_mode_search_field = page.locator("#id_work_mode-collapse input.select2-search__field")

        self.employer_filter_title = "Наниматель"
        self.employer_search_field = page.locator("#id_business_entity-collapse input.select2-search__field")

        self.work_nature_filter_title = "Характер работы"
        self.work_nature_search_field = page.locator("#id_employment_nature-collapse input.select2-search__field")

        self.education_filter_title = "Образование"
        self.education_search_field = page.locator("#id_education-collapse input.select2-search__field")

        self.activity_sphere_filter_title = "Сфера деятельности"
        self.activity_sphere_search_field = page.locator("#id_activity_area-collapse input.select2-search__field")

        # Планируемая дата образования вакансии (скрыта за спойлером)
        self.planned_date_filter_title = "Планируемая дата образования вакансии"
        self.works_starts_input = page.locator("#id_works_starts")

        # Предоставляется жилье (чекбокс, скрыт за спойлером)
        self.housing_filter_title = "Предоставляется жилье"
        self.housing_checkbox = page.locator("#id_housing")
        self.housing_label = page.locator("label[for='id_housing']")

        # Общие элементы внутри активного раскрытого окна Select2
        self.select2_options = page.locator(".select2-container--open li.select2-results__option")

        # Кнопки панели фильтров
        self.submit_filter_btn = page.locator("button[type='submit']").filter(has_text="Поиск").first
        self.reset_filter_btn = page.locator("a:has-text('Сбросить фильтр')").first

        # Карточки результатов выдачи
        self.vacancy_cards = page.locator("div.inner-box")
        self.vacancy_title_link = page.locator("h4.job-title a")
        self.detail_btn = page.locator("a:has-text('Подробнее')")
        self.organization_link = page.locator("li.org a")
        self.salary_value = page.locator("span.salary")
        self.address_value = page.locator("span.address")

        # Сортировка и количество элементов на странице
        self.paginate_by_select = page.locator("#paginate_by_select")
        self.sort_by_select = page.locator("#sort_by")

        # Элементы пагинации
        self.active_page_number = page.locator("span.page-link").first
        self.page_2_link = page.locator("a.page-link[href*='page=2']").first
        self.back_arrow_btn = page.locator("a.page-link").filter(has=page.locator("span.fa-caret-left")).first
        self.forward_arrow_btn = page.locator("a.page-link").filter(has=page.locator("span.fa-caret-right")).first

    def navigate(self):
        """Чистый переход на страницу перспективных рабочих мест с устойчивостью к медленной сети."""
        goto_with_retry(self.page, self.url, wait_until="load")

    def open_spoiler_if_hidden(self, title_text: str, target_locator):
        """Проверяет видимость поля фильтра и кликает по его заголовку h4 для раскрытия спойлера."""
        if not target_locator.is_visible():
            spoiler_title = self.page.locator(f"xpath=//h4[contains(text(), '{title_text}')]").first
            spoiler_title.scroll_into_view_if_needed()
            spoiler_title.click()
            target_locator.wait_for(state="visible", timeout=3000)

    def select_from_dropdown(self, search_field_locator, item_name: str):
        """Выбор элемента из списка Select2 со встречным посимвольным вводом."""
        search_field_locator.click()
        search_field_locator.press_sequentially(item_name, delay=60)
        self.page.wait_for_timeout(800)

        target_option = self.page.get_by_role("option", name=item_name, exact=True)
        target_option.wait_for(state="visible", timeout=3000)
        target_option.click()

    def apply_filter_and_wait(self):
        """Применяет установленные фильтры нажатием кнопки 'Поиск' и ждет обновления выдачи."""
        self.submit_filter_btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        self.submit_filter_btn.click(force=True)
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1500)
