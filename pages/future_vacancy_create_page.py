from playwright.sync_api import Page
from pages.vacancy_create_page import VacancyCreatePage


class FutureVacancyCreatePage(VacancyCreatePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Рабочее место — обычный <select>, не Select2
        self.workplace_select = page.locator("#id_workplace")
        # Дата начала работ
        self.works_starts_input = page.locator("#id_works_starts")
        # Кнопка называется иначе, чем на форме обычной вакансии
        self.submit_button = page.get_by_role("button", name="Создать вакансию")
