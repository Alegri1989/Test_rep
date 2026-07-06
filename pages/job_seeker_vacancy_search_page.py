from playwright.sync_api import Page, Locator
import re

class JobSeekerVacancySearchPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/vacancy-search/"

        # Основные элементы
        self.favorite_btns = page.locator("button.favorite_btn")
        self.show_favorites_checkbox = page.locator("input#id_tag")
        self.print_favorites_btn = page.locator("button[formaction*='print-vacancy-list']")
        self.clear_favorites_btn = page.locator("button#clear-favorites-btn")
        self.paginate_by_select = page.locator("select#paginate_by_select")
        self.sort_select = page.locator("select[name='sort']")
        self.vacancy_cards = page.locator(".job-block")

    def navigate(self):
        """Переход на страницу и базовые проверки"""
        self.page.goto(self.url)
        self.page.wait_for_selector("#id_profession", state="visible", timeout=60000)
        self.page.wait_for_load_state("networkidle")

    def get_favorite_button(self, vacancy_index: int) -> Locator:
        """Получение кнопки избранного для конкретной вакансии"""
        return self.favorite_btns.nth(vacancy_index)
    
    def search_vacancy(self, profession: str):
        """Поиск вакансий по профессии"""
        search_input = self.page.locator("#id_profession")
        search_input.wait_for(state="visible", timeout=30000)
        search_input.fill(profession)
        self.page.click("button:has-text('Найти')")
        self.page.wait_for_load_state("networkidle")
    
    def select_region(self, region_name: str):
        """Выбор региона через Select2"""
        self.page.click("#select2-id_region-container")
        self.page.fill(".select2-search__field", region_name)
        self.page.click(f"li:has-text('{region_name}')")
    
    def set_salary_filter(self, min_salary: str, max_salary: str = ""):
        """Установка фильтра по зарплате"""
        self.page.fill("#id_salary_min", min_salary)
        if max_salary:
            self.page.fill("#id_salary_max", max_salary)

    def toggle_favorite(self, vacancy_index: int):
        btn = self.get_favorite_button(vacancy_index)
        btn.wait_for(state="visible", timeout=120000)
        btn.scroll_into_view_if_needed()
        btn.click()
        self.page.wait_for_timeout(1000)  # Увеличено время ожидания обновления

    def check_show_favorites(self):
        self.show_favorites_checkbox.wait_for(state="visible", timeout=120000)
        self.page.wait_for_timeout(1000)  # Дополнительная пауза для стабилизации
        self.show_favorites_checkbox.check()
        self.page.wait_for_timeout(1000)  # Ожидание применения фильтра

    def uncheck_show_favorites(self):
        self.show_favorites_checkbox.uncheck()

    def click_print_favorites(self):
        self.print_favorites_btn.wait_for(state="visible")
        self.print_favorites_btn.click()

    def click_clear_favorites(self):
        self.clear_favorites_btn.click()

    def confirm_clear_favorites(self):
        self.clear_favorites_btn.wait_for(state="visible")
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.click_clear_favorites()
        self.page.wait_for_timeout(500)

    def set_paginate_by(self, value: str):
        self.paginate_by_select.select_option(value)

    def set_sort_by(self, value: str):
        self.sort_select.select_option(value)

    def get_vacancy_count(self) -> int:
        return self.vacancy_cards.count()

    def get_favorite_state(self, vacancy_index: int) -> bool:
        btn = self.get_favorite_button(vacancy_index)
        btn.wait_for(state="visible")
        class_list = btn.locator("i").get_attribute("class")
        return "fas fa-star" in class_list
