from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class OpfrPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/opfr_organisations/public-list/"

        # Кнопка переключения вида (организации ↔ документы)
        self.toggle_view_btn = page.locator("#toggle-view-btn")

        # Кнопки "Скачать" в режиме документов (target="_blank", файлы из /media/)
        self.download_btn = page.locator("a.btn-sm.btn-primary[href*='/media/']")

        # Карточки и элементы навигации по организациям
        self.org_cards = page.locator("div.inner-box")
        self.org_title_link = page.locator("div.inner-box a[href*='/opfr_organisations/']:not(.btn)")
        self.detail_btn = page.locator("a.btn-primary.mt-3[href*='/opfr_organisations/']")

        # Фильтр "Наименование организации" (текстовый ввод)
        self.name_filter_input = page.locator("#id_name")

        # Фильтр "Регион" (Select2)
        self.region_select2_container = page.locator("#select2-id_region-container")

        # Кнопки управления фильтрами
        self.submit_filter_btn = page.locator("button[type='submit']").first
        self.reset_filter_btn = page.locator("a.btn-outline-primary[href*='?']").first

    def navigate(self):
        goto_with_retry(self.page, self.url, wait_until="load")

    def select_region(self, region_name: str):
        """Выбирает регион в Select2-виджете по точному наименованию."""
        self.region_select2_container.click()
        search_field = self.page.locator(".select2-search__field")
        search_field.wait_for(state="visible", timeout=3000)
        search_field.fill(region_name)
        option = self.page.locator(f".select2-results__option:has-text('{region_name}')").first
        option.wait_for(state="visible", timeout=3000)
        option.click()

    def apply_filter_and_wait(self):
        """Применяет фильтры нажатием кнопки 'Поиск' и ждёт обновления выдачи."""
        self.submit_filter_btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        self.submit_filter_btn.click()
        self.page.wait_for_load_state("load")
