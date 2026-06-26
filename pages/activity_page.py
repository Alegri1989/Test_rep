from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class ActivityPage:
    def __init__(self, page: Page):
        self._page = page
        self.url = "https://gsz.gov.by/registration/activity/public/list/"

        self.region_select = page.locator("#id_activity_region")
        self.description_input = page.locator("#id_description")
        self.date_input = page.locator("#id_publication_date")
        self.search_btn = page.locator("#submitFilters")
        self.sort_select = page.locator("#sort_by")

        self.activity_links = page.locator("a.news__link")

    def navigate(self):
        goto_with_retry(self._page, self.url, wait_until="load")
        self.activity_links.first.wait_for(state="visible", timeout=10000)

    def set_publication_date(self, year_month: str):
        """Ставит значение readonly-поля даты напрямую через JS (формат YYYY-MM)."""
        self._page.evaluate(f"""
            () => {{
                const el = document.querySelector('#id_publication_date');
                if (el) el.value = '{year_month}';
            }}
        """)

    def apply_filter_and_wait(self):
        self.search_btn.click()
        self._page.wait_for_load_state("domcontentloaded")
