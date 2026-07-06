import re
from playwright.sync_api import Page, Locator, expect


class JobSeekerVacancySearchPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/vacancy-search/"

        # Основные элементы
        self.favorite_btns = page.locator("button.favorite_btn")
        self.show_favorites_checkbox = page.locator("input#id_tag")
        self.show_favorites_label = page.locator("label[for='id_tag']")
        self.print_favorites_btn = page.locator("button[formaction*='print-vacancy-list']")
        self.clear_favorites_btn = page.locator("button#clear-favorites-btn")
        self.paginate_by_select = page.locator("select#paginate_by_select")
        self.sort_select = page.locator("select[name='sort']")
        self.vacancy_cards = page.locator(".job-block")

    def navigate(self):
        """Переход на страницу и базовые проверки."""
        self.page.goto(self.url)
        self.page.wait_for_selector("#id_profession", state="visible", timeout=60000)
        self.page.wait_for_load_state("networkidle")

    def get_favorite_button(self, vacancy_index: int) -> Locator:
        """Получение кнопки избранного для конкретной вакансии."""
        return self.favorite_btns.nth(vacancy_index)

    def search_vacancy(self, profession: str):
        """Поиск вакансий по профессии."""
        search_input = self.page.locator("#id_profession")
        search_input.wait_for(state="visible", timeout=30000)
        search_input.fill(profession)
        self.page.click("button:has-text('Найти')")
        self.page.wait_for_load_state("networkidle")

    def select_region(self, region_name: str):
        """Выбор региона через Select2."""
        self.page.click("#select2-id_region-container")
        self.page.fill(".select2-search__field", region_name)
        self.page.click(f"li:has-text('{region_name}')")

    def set_salary_filter(self, min_salary: str, max_salary: str = ""):
        """Установка фильтра по зарплате."""
        self.page.fill("#id_salary_min", min_salary)
        if max_salary:
            self.page.fill("#id_salary_max", max_salary)

    def get_favorite_state(self, vacancy_index: int) -> bool:
        """Возвращает True, если вакансия в избранном.

        Избранное отмечено сплошной звездой (класс `fas`), не избранное —
        контурной (`far`). Обе иконки содержат `fa-star`, поэтому состояние
        определяется именно по `fas`.
        """
        btn = self.get_favorite_button(vacancy_index)
        btn.wait_for(state="visible", timeout=30000)
        class_list = btn.locator("i").first.get_attribute("class") or ""
        return "fas" in class_list.split()

    def toggle_favorite(self, vacancy_index: int):
        """Переключает избранное для вакансии и ждёт обновления иконки.

        AJAX-обработчик звезды навешивается уже после загрузки списка, поэтому
        слишком ранний клик (например, сразу после перезагрузки страницы) может
        не переключить состояние. Повторяем клик, если иконка не сменила класс.
        """
        btn = self.get_favorite_button(vacancy_index)
        btn.wait_for(state="visible", timeout=120000)
        btn.scroll_into_view_if_needed()

        before = self.get_favorite_state(vacancy_index)
        expected = "far" if before else "fas"
        icon = btn.locator("i").first

        for attempt in range(3):
            btn.click()
            try:
                expect(icon).to_have_class(re.compile(rf"\b{expected}\b"), timeout=7000)
                return
            except AssertionError:
                # Обработчик мог ещё не подключиться — даём паузу и кликаем снова
                self.page.wait_for_timeout(1000)

        # Финальная проверка с полным таймаутом, чтобы дать читаемую ошибку
        expect(icon).to_have_class(re.compile(rf"\b{expected}\b"), timeout=7000)

    def count_favorited(self) -> int:
        """Считает количество вакансий, отмеченных как избранные, на странице."""
        total = self.favorite_btns.count()
        return sum(
            1 for i in range(total)
            if "fas" in (self.favorite_btns.nth(i).locator("i").first.get_attribute("class") or "").split()
        )

    def add_favorites(self, quantity: int):
        """Добавляет в избранное указанное количество ещё не избранных вакансий."""
        added = 0
        total = self.favorite_btns.count()
        for i in range(total):
            if added >= quantity:
                break
            if not self.get_favorite_state(i):
                self.toggle_favorite(i)
                added += 1
        return added

    def check_show_favorites(self):
        """Включает фильтр «Показать только избранное» (перезагружает список)."""
        self.show_favorites_checkbox.wait_for(state="attached", timeout=30000)
        if self.show_favorites_checkbox.is_checked():
            return
        with self.page.expect_navigation(wait_until="load"):
            self.show_favorites_label.click()
        self.page.wait_for_load_state("networkidle")

    def uncheck_show_favorites(self):
        """Выключает фильтр «Показать только избранное» (перезагружает список)."""
        self.show_favorites_checkbox.wait_for(state="attached", timeout=30000)
        if not self.show_favorites_checkbox.is_checked():
            return
        with self.page.expect_navigation(wait_until="load"):
            self.show_favorites_label.click()
        self.page.wait_for_load_state("networkidle")

    def click_print_favorites(self, timeout=30000):
        """Инициирует печать списка избранного и возвращает ответ сервера.

        Кнопка отправляет GET-форму на /registration/print-vacancy-list/ в
        отдельную вкладку (formtarget=to_print) и возвращает HTML-страницу для
        печати, а не файл-загрузку. Дожидаемся именно этого ответа.
        """
        self.print_favorites_btn.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(
            lambda r: "print-vacancy-list" in r.url, timeout=timeout
        ) as response_info:
            self.print_favorites_btn.click()
        return response_info.value

    def clear_all_favorites(self):
        """Очищает всё избранное на аккаунте: подтверждает JS-диалог и ждёт стабилизации.

        Кнопка присутствует всегда. При непустом избранном подтверждение
        диалога перезагружает список, при пустом — навигации нет. Поэтому не
        используем expect_navigation (он бы завис на пустом избранном), а ждём
        load/networkidle: при перезагрузке дождёмся её, иначе вернёмся сразу.
        """
        self.clear_favorites_btn.wait_for(state="visible", timeout=30000)
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.clear_favorites_btn.click()
        self.page.wait_for_load_state("load")
        self.page.wait_for_load_state("networkidle")

    def set_paginate_by(self, value: str):
        self.paginate_by_select.select_option(value)

    def set_sort_by(self, value: str):
        self.sort_select.select_option(value)

    def get_vacancy_count(self) -> int:
        return self.vacancy_cards.count()
