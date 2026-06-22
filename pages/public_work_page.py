from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class PublicWorkPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/temporary-employment/public-works/"

        # Слайдер-переключатель вида временной занятости (Молодежь / Оплачиваемые работы)
        self.young_employment_link = page.locator("a[href='/registration/temporary-employment/young/']").first
        self.public_works_slider = page.locator(".slider.round.checked")

        # Фильтр территориально-административной иерархии (Область)
        self.region_dropdown = page.locator("span[aria-labelledby='select2-id_region-container']")
        self.region_selected_text = page.locator("#select2-id_region-container")

        # Фильтр по нанимателю (скрыт за спойлером по умолчанию)
        self.employer_filter_header = page.locator("#id_workplace__business_entity-header")
        self.employer_dropdown = page.locator("span[aria-labelledby='select2-id_workplace__business_entity-container']")
        self.employer_selected_text = page.locator("#select2-id_workplace__business_entity-container")

        # Общие элементы внутри активного раскрытого окна Select2
        self.select2_search_field = page.locator(".select2-container--open input.select2-search__field")
        self.select2_options = page.locator(".select2-container--open li.select2-results__option")

        # Кнопки панели фильтров
        self.submit_filter_btn = page.locator("button[type='submit']").first
        self.reset_filter_btn = page.locator("a:has-text('Сбросить фильтр')").first

        # Карточки результатов выдачи
        self.vacancy_cards = page.locator("div.inner-box")
        self.vacancy_title = page.locator("p.font-weight-bold")
        self.vacancy_address = page.locator("span.address")
        self.vacancy_employer = page.locator("li.pb-0")

        # Кнопка перехода к другим вакансиям того же нанимателя
        self.other_employer_vacancies_btn = page.locator("a:has-text('Другие вакансии нанимателя')")

        # Элементы пагинации
        self.paginate_by_select = page.locator("#paginate_by_select")
        self.active_page_number = page.locator("span.page-link").first
        self.page_2_link = page.locator("a.page-link[href*='page=2']").first
        self.forward_arrow_btn = page.locator("a.page-link").filter(has=page.locator("span.fa-caret-right")).first
        self.fast_forward_btn = page.locator("a.page-link").filter(has=page.locator("span.fa-forward")).first

    def navigate(self):
        """Чистый переход на страницу временных оплачиваемых работ с устойчивостью к медленной сети."""
        goto_with_retry(self.page, self.url, wait_until="load")

    def open_employer_filter_if_hidden(self):
        """Раскрывает спойлер фильтра 'Наниматель', если он свернут по умолчанию."""
        if not self.employer_dropdown.is_visible():
            self.employer_filter_header.scroll_into_view_if_needed()
            self.employer_filter_header.click()
            self.employer_dropdown.wait_for(state="visible", timeout=3000)

    def select_from_dropdown(self, dropdown_locator, item_name: str):
        """Выбор элемента из списка Select2 со встречным посимвольным вводом."""
        dropdown_locator.click()
        self.select2_search_field.wait_for(state="visible", timeout=3000)
        self.select2_search_field.press_sequentially(item_name, delay=60)
        self.page.wait_for_timeout(800)

        target_option = self.page.get_by_role("option", name=item_name, exact=True)
        target_option.wait_for(state="visible", timeout=3000)
        target_option.click()

    def apply_filter_and_wait(self):
        """Применяет установленные фильтры нажатием кнопки 'Поиск' и ждет обновления выдачи."""
        self.submit_filter_btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        self.submit_filter_btn.click(force=True)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
