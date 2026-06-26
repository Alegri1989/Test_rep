from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class ForeignPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/foreign-citizens-employment/public/list/"

        # Баннер-ссылка "Вакансии для иностранных граждан" (h4 с иконкой стрелки вправо)
        self.vacancies_banner = page.locator("a[href*='for_foreigner=on']").first

        # Переключатели разворачивающихся аккордеон-блоков (Bootstrap collapse)
        # :not(.navbar-toggler) — исключает скрытую кнопку-бургер навигации,
        # которая тоже имеет data-toggle='collapse' и всегда hidden на десктопе
        self.accordion_toggles = page.locator(
            "[data-toggle='collapse']:not(.navbar-toggler), "
            "[data-bs-toggle='collapse']:not(.navbar-toggler)"
        )

        # Кнопки "Перейти" внутри раскрытых блоков (ведут на /public-view/)
        self.go_to_buttons = page.locator(
            "a[href*='/foreign-citizens-employment/'][href*='/public-view/']"
        )

        # Кнопки "Скачать" на странице списка (стиль btn-outline-primary)
        self.download_buttons_list = page.locator(
            "a.btn-outline-primary[href*='/public-download/']"
        )

        # Кнопка "Скачать" на детальной странице /public-view/ (стиль btn-primary)
        self.download_button_detail = page.locator(
            "a.btn-primary[href*='/public-download/']"
        )

    def navigate(self):
        """Переход на страницу занятости иностранных граждан с устойчивостью к медленной сети."""
        goto_with_retry(self.page, self.url, wait_until="load")

    def expand_first_accordion(self):
        """Разворачивает первый аккордеон-блок и ждёт появления его содержимого."""
        first_toggle = self.accordion_toggles.first
        first_toggle.scroll_into_view_if_needed()
        first_toggle.click()
        self.go_to_buttons.first.wait_for(state="visible", timeout=5000)
