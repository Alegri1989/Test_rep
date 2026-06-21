from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class HelpPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/directory/information/help/#pills-home"

        # Вкладки соискателя и нанимателя
        self.download_seeker_guide_link = page.get_by_role(
            "link", name="Руководство пользователя (соискателя)"
        )
        self.download_employer_guide_link = page.get_by_role(
            "link", name="Руководство пользователя (администратора нанимателя)"
        )
        self.employer_tab = page.locator("#pills-profile-tab")

        # Кнопки "Скачать" по жестким английским уникальным частям из вашего HTML
        self.download_seeker_guide_btn = page.locator("a[href*='rukovodstvo_job_seeker.pdf']")
        self.download_employer_guide_btn = page.locator("a[href*='5xUt70I.pdf']")
        self.download_vacancy_order_btn = page.locator("a[href*='V4LdVFg.pdf']")
        self.download_login_instruction_btn = page.locator("a[href*='2025_1.pdf']")
        self.download_chrome_instruction_btn = page.locator("a[href*='Chrome.pdf']")
        self.download_gossuok_instruction_btn = page.locator("a[href*='GosSUOK.pdf']")
        self.download_legal_entity_template_btn = page.locator("a[href*='ec0ozce.docx']")

    def navigate(self):
        """Открывает страницу Помощь и поддержка с устойчивостью к медленной сети."""
        goto_with_retry(self.page, self.url, wait_until="load")