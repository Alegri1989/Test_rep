from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class EducationPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/training-course/public/list/"

        # Фильтр "Регион обучения" (скрыт за спойлером по умолчанию, обычный select без Select2)
        self.region_filter_title = "Регион обучения"
        self.region_select = page.locator("#id_region")

        # Фильтр "Период обучения" (скрыт за спойлером по умолчанию)
        self.period_filter_title = "Период обучения"
        self.period_start_input = page.locator("#id_period_start")
        self.start_when_full_checkbox = page.locator("#id_start_when_full")
        self.start_when_full_label = page.locator("label[for='id_start_when_full']")

        # Кнопки панели фильтров
        self.submit_filter_btn = page.locator("button[type='submit']").first
        self.reset_filter_btn = page.locator("a:has-text('Сбросить фильтр')").first

        # Карточки результатов выдачи
        self.vacancy_cards = page.locator("div.inner-box")
        self.vacancy_title_link = page.locator("h4.job-title a")
        self.detail_btn = page.locator("a:has-text('Подробнее')")
        self.institution_value = page.locator("span.address")
        self.region_value = page.locator("li:has(span[title='Регион обучения']) span:not(.icon)")
        self.type_value = page.locator("li:has(span[title='Вид обучения']) span:not(.icon)")
        self.group_forming_value = page.locator(
            "li:has(span[title='Планируемое формирование группы']) span:not(.icon)"
        )
        self.contact_link = page.locator("a:has-text('Контактные данные службы занятости')")

        # Элементы пагинации
        self.active_page_number = page.locator("span.page-link").first
        self.page_2_link = page.locator("a.page-link[href*='page=2']").first
        self.back_arrow_btn = page.locator("a.page-link").filter(has=page.locator("span.fa-caret-left")).first
        self.forward_arrow_btn = page.locator("a.page-link").filter(has=page.locator("span.fa-caret-right")).first

    def navigate(self):
        """Чистый переход на страницу обучения с устойчивостью к медленной сети."""
        goto_with_retry(self.page, self.url, wait_until="load")

    def open_spoiler_if_hidden(self, title_text: str, target_locator):
        """Проверяет видимость поля фильтра и кликает по его заголовку h4 для раскрытия спойлера."""
        if not target_locator.is_visible():
            spoiler_title = self.page.locator(f"xpath=//h4[contains(text(), '{title_text}')]").first
            spoiler_title.scroll_into_view_if_needed()
            spoiler_title.click()
            target_locator.wait_for(state="visible", timeout=3000)

    def select_current_month_in_period_datepicker(self):
        """Открывает датапикер периода обучения (минимальный режим - месяцы) и выбирает текущий выделенный месяц."""
        self.period_start_input.click()
        current_month_cell = self.page.locator(".datepicker-months span.month.focused")
        current_month_cell.wait_for(state="visible", timeout=3000)
        current_month_cell.click()

    def apply_filter_and_wait(self):
        """Применяет установленные фильтры нажатием кнопки 'Поиск' и ждет обновления выдачи."""
        self.submit_filter_btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        self.submit_filter_btn.click(force=True)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
