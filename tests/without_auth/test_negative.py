import allure
import pytest
from urllib.parse import unquote
from playwright.sync_api import Page

from pages.vacancy_search_page import VacancySearchPage
from pages.future_work_page import FutureWorkPage


@pytest.mark.vacancy_search
@allure.title("Негатив: Поиск по несуществующей профессии возвращает пустую выдачу")
def test_guest_search_nonsense_returns_empty(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Негативный сценарий (пустая выдача): поиск по заведомо несуществующей
    профессии не должен вернуть ни одной карточки вакансии.

    Прекондишены:
    1. Пользователь не авторизован (гостевой сеанс).
    2. Открыта страница поиска вакансий.

    Ожидаемый результат (ОР):
    - В выдаче отсутствует хотя бы одна карточка вакансии (пустой список).
    """
    nonsense = "ksweghkew"

    with allure.step("Шаг 1: Ввод несуществующей профессии и отправка поиска"):
        vacancy_page.navigate()
        vacancy_page.search_input.wait_for(state="visible", timeout=5000)
        vacancy_page.search_input.click()
        vacancy_page.search_input.fill(nonsense)
        vacancy_page.search_button.click()
        guest_page.wait_for_load_state("networkidle")

    with allure.step("ОР: карточки вакансий в выдаче отсутствуют"):
        assert f"profession={nonsense}" in unquote(guest_page.url), (
            f"Ошибка: поисковый запрос не применён, URL: {guest_page.url}"
        )
        count = vacancy_page.vacancy_title_link.count()
        assert count == 0, (
            f"Ошибка: поиск по '{nonsense}' вернул {count} карточек, ожидалось 0"
        )


@pytest.mark.future_work
@allure.title("Негатив: Невозможный фильтр по зарплате возвращает пустую выдачу")
def test_guest_impossible_salary_filter_returns_empty(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Негативный сценарий (пустая выдача): фильтр «Зарплата от» с порогом,
    превышающим любые реальные значения, не должен вернуть ни одного места.

    Прекондишены:
    1. Пользователь не авторизован (гостевой сеанс).
    2. Открыта страница перспективных рабочих мест.

    Ожидаемый результат (ОР):
    - В выдаче отсутствует хотя бы одна карточка (пустой список).
    """
    with allure.step("Шаг 1: Установка нереально высокого порога зарплаты"):
        future_work_page.navigate()
        future_work_page.salary_min_input.wait_for(state="visible", timeout=5000)
        future_work_page.salary_min_input.fill("10000000")

    with allure.step("Шаг 2: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР: карточки в выдаче отсутствуют"):
        count = future_work_page.vacancy_cards.count()
        assert count == 0, (
            f"Ошибка: невозможный фильтр по зарплате вернул {count} карточек, ожидалось 0"
        )
