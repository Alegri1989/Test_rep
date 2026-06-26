from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class DepartmentsPage:
    def __init__(self, page: Page):
        self._page = page
        self.url = "https://gsz.gov.by/directory/information/employment-departments/"

        self.department_cards = page.locator("h4.job-title")
        self.detail_buttons = page.locator("a.btn.btn-primary[href*='detail']")
        self.site_buttons = page.locator("a.btn.btn-outline-primary[href^='http']")

        self.region_container = page.locator("#select2-id_region-container")
        self.search_btn = page.locator("button[type='submit'].btn.btn-primary")
        self.reset_filter_btn = page.locator("a[href*='employment-departments/?']")

        self.map_toggle_btn = page.locator("#toggle-view-btn")
        self.map_element = page.locator("#map")

    def navigate(self):
        goto_with_retry(self._page, self.url, wait_until="load")
        self.department_cards.first.wait_for(state="visible", timeout=10000)

    def select_region(self, region_name: str):
        # Устанавливаем значение нативного select напрямую без jQuery trigger —
        # $(sel).trigger('change') сбрасывает значение (Select2 перехватывает событие).
        self._page.wait_for_selector('select[name="region"]', state="attached", timeout=5000)
        self._page.evaluate(f"""
            () => {{
                const sel = document.querySelector('select[name="region"]');
                if (!sel) return;
                const opt = [...sel.options].find(o => o.text.trim().includes('{region_name}'));
                if (opt) sel.value = opt.value;
            }}
        """)

    def apply_filter_and_wait(self):
        self.search_btn.click()
        self._page.wait_for_load_state("domcontentloaded")
