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
        self.page.goto(self.url)
        self.page.wait_for_load_state("networkidle")

    def get_favorite_button(self, vacancy_index: int) -> Locator:
        return self.favorite_btns.nth(vacancy_index)

    def toggle_favorite(self, vacancy_index: int):
        btn = self.get_favorite_button(vacancy_index)
        btn.click()
        self.page.wait_for_timeout(500)  # Даем время на обновление состояния

    def check_show_favorites(self):
        self.show_favorites_checkbox.check()

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
