from playwright.sync_api import Page
from pages.vacancy_search_page import VacancySearchPage


def apply_vacancy_filter_and_wait(page: Page, vacancy_page: VacancySearchPage):
    """Общий хелпер для отправки формы фильтров."""
    vacancy_page.submit_filter_btn.scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    # Кликаем по кнопке Поиск
    vacancy_page.submit_filter_btn.click(force=True)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)