from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class ServicesPage:
    def __init__(self, page: Page):
        self._page = page
        self.url = "https://gsz.gov.by/registration/services/public/list/"

        self.service_headers = page.locator("h4:has(i)")
        self.view_buttons = page.locator("a.btn.btn-primary[href*='public-view']")
        self.back_button = page.locator("a.btn.btn-outline-primary[href*='services/public/list']")

    def navigate(self):
        goto_with_retry(self._page, self.url, wait_until="load")
        self.service_headers.first.wait_for(state="visible", timeout=10000)

    def expand_item(self, index: int = 0):
        self.service_headers.nth(index).click()
        self._page.wait_for_timeout(500)
