import re
from playwright.sync_api import Page, Locator, expect, Error as PlaywrightError

from pages.vacancy_search_page import VacancySearchPage


class JobSeekerVacancySearchPage(VacancySearchPage):
    """Страница поиска вакансий для авторизованного соискателя.

    Наследует общий URL и базовые локаторы/методы VacancySearchPage
    (один URL — один базовый page object) и добавляет только функционал
    управления избранными вакансиями.
    """

    def __init__(self, page: Page):
        super().__init__(page)

        # Элементы управления избранными
        self.favorite_btns = page.locator("button.favorite_btn")
        self.show_favorites_checkbox = page.locator("input#id_tag")
        self.show_favorites_label = page.locator("label[for='id_tag']")
        self.print_favorites_btn = page.locator("button[formaction*='print-vacancy-list']")
        self.clear_favorites_btn = page.locator("button#clear-favorites-btn")
        self.vacancy_cards = page.locator(".job-block")

    def navigate(self):
        """Переход на страницу и ожидание готовности списка вакансий."""
        self.page.goto(self.url)
        self.page.wait_for_selector("#id_profession", state="visible", timeout=60000)
        self.page.wait_for_timeout(2000)

    def get_favorite_button(self, vacancy_index: int) -> Locator:
        """Получение кнопки избранного для конкретной вакансии."""
        return self.favorite_btns.nth(vacancy_index)

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
        self.page.wait_for_timeout(2000)

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
        """Очищает всё избранное на аккаунте: подтверждает JS-диалог и ждёт,
        пока на странице не исчезнут все «сплошные» звёзды избранного.

        Кнопка присутствует всегда. При непустом избранном подтверждение
        диалога перезагружает список, но момент перезагрузки относительно
        клика не гарантирован — поэтому ждём фактического обновления DOM
        (wait_for_function), а не load/networkidle. Если избранное всё же
        осталось (сервер ещё не зафиксировал очистку к моменту перезагрузки) —
        повторяем очистку.
        """
        self.clear_favorites_btn.wait_for(state="visible", timeout=30000)
        for attempt in range(3):
            self.page.once("dialog", lambda dialog: dialog.accept())
            self.clear_favorites_btn.click()
            try:
                self.page.wait_for_function(
                    """() => Array.from(document.querySelectorAll('button.favorite_btn i'))
                              .every(icon => !((icon.className || '').split(' ').includes('fas')))""",
                    timeout=20000,
                )
                return
            except PlaywrightError:
                self.page.wait_for_timeout(2000)
        # Три попытки не помогли — даём тесту упасть с понятной ошибкой
        raise AssertionError(
            f"Ошибка: не удалось очистить избранное, осталось избранных: {self.count_favorited()}"
        )

    def get_vacancy_count(self) -> int:
        return self.vacancy_cards.count()
