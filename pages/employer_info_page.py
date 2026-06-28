import logging
from playwright.sync_api import Page


class EmployerInfoPage:
    def __init__(self, page: Page):
        self.page = page

        self.edit_info_btn = page.locator("a.btn-edit")
        self.create_workplace_btn = page.locator("a[href*='create-workplace']")
        self.workplace_search_input = page.locator("#workplace-search")
        self.reset_search_btn = page.locator("#reset-search")

    def get_workplace_card(self, name: str):
        """Возвращает локатор карточки рабочего места по названию."""
        title = self.page.locator("h4.job-title", has_text=name)
        return self.page.locator("div", has=title).filter(
            has=self.page.locator("button.btn-delete")
        ).last

    def get_workplace_edit_btn(self, name: str):
        return self.get_workplace_card(name).locator("a.btn-primary").first

    def get_workplace_edit_coords_btn(self, name: str):
        return self.get_workplace_card(name).locator("a.btn-outline-primary").first

    def get_workplace_delete_btn(self, name: str):
        return self.get_workplace_card(name).locator("button.btn-delete")

    def search_workplace(self, text: str):
        logging.debug(f"Действие: Поиск рабочего места по тексту '{text}'")
        self.workplace_search_input.fill(text)
        self.page.wait_for_timeout(800)

    def reset_search(self):
        logging.debug("Действие: Сброс поиска рабочих мест")
        self.reset_search_btn.click()
        self.page.wait_for_timeout(500)

    def confirm_workplace_delete(self):
        """Подтверждает удаление рабочего места в модальном окне."""
        logging.debug("Действие: Подтверждение удаления рабочего места в модальном окне")
        modal = self.page.locator("#delete_workplace")
        modal.wait_for(state="visible", timeout=10000)
        confirm_btn = modal.locator(
            "button:has-text('Удалить'), button:has-text('Да'), button:has-text('OK')"
        ).first
        confirm_btn.click()
        self.page.wait_for_load_state("networkidle", timeout=10000)
