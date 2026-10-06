import re
import allure
import pytest
from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry

BASE_URL = "https://gsz.gov.by"
PUBLISHED_LIST_URL = f"{BASE_URL}/registration/employer/vacancy/list/published/"


def _get_own_published_vacancy_id(page: Page, workplace_id: int) -> str | None:
    """Возвращает ID своей опубликованной вакансии."""
    goto_with_retry(page, f"{PUBLISHED_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    edit_btn = page.locator("a.edit-published-vacancy-btn").first
    if edit_btn.count() > 0:
        href = edit_btn.get_attribute("href")
        match = re.search(r"/vacancy-published/(\d+)/", href)
        if match:
            return match.group(1)

    unpublish_btn = page.locator("button[onclick*='open_unpublish_confirm']").first
    if unpublish_btn.count() > 0:
        onclick = unpublish_btn.get_attribute("onclick")
        match = re.search(r"open_unpublish_confirm\((\d+)\)", onclick)
        if match:
            return match.group(1)

    return None


def _count_form_fields(page: Page) -> int:
    """Считает количество полей формы на странице."""
    return page.locator("input[name], select[name], textarea[name]").count()


@allure.epic("Безопасность")
@allure.feature("BOLA — чужие опубликованные вакансии")
class TestPublishedVacancyBOLA:
    """BOLA тесты для опубликованных вакансий:
    попытка открыть/изменить чужую опубликованную вакансию
    через /vacancy-published/{id}/edit/ должна быть отклонена."""

    @allure.title("BOLA: Запрет редактирования чужой опубликованной вакансии")
    def test_bola_cannot_edit_foreign_published_vacancy(self, auth_employer_page: Page, app_config):
        """
        BOLA (read+write): открытие страницы редактирования чужой опубликованной
        вакансии через /vacancy-published/{id}/edit/ должно быть отклонено.

        Баг: при изменении числового ID в URL пользователь попадает на страницу
        редактирования чужой вакансии с заполненной формой.

        Ожидаемый результат (ОР):
        - Страница редактирования чужой вакансии НЕ открывается.
        - Показывается "Не найдено" или ошибка доступа.
        """
        page = auth_employer_page
        employer_cfg = app_config["employer"]
        workplace_id = employer_cfg["permanent_workplace_id"]

        with allure.step("Шаг 1: Получить ID своей опубликованной вакансии"):
            own_id = _get_own_published_vacancy_id(page, workplace_id)
            assert own_id, (
                f"Ошибка: не найдена своя опубликованная вакансия "
                f"для workplace_id={workplace_id}"
            )
            allure.attach(own_id, name="Свой ID вакансии")

        with allure.step(f"Шаг 2: Проверить, что своя вакансия {own_id} открывается"):
            own_url = f"{BASE_URL}/registration/employer/vacancy-published/{own_id}/edit/"
            page.goto(own_url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            own_fields = _count_form_fields(page)
            allure.attach(str(own_fields), name="Количество полей своей вакансии")
            assert own_fields > 0, (
                f"Ошибка: своя вакансия {own_id} не открывается (0 полей)"
            )

        with allure.step(f"Шаг 3: Попытка открыть чужую вакансию {own_id}-1"):
            foreign_id = str(int(own_id) - 1)
            foreign_url = f"{BASE_URL}/registration/employer/vacancy-published/{foreign_id}/edit/"
            page.goto(foreign_url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            foreign_fields = _count_form_fields(page)
            body_text = page.evaluate("() => document.body.innerText")[:300]
            allure.attach(foreign_id, name="Чужой ID вакансии")
            allure.attach(str(foreign_fields), name="Количество полей чужой вакансии")
            allure.attach(body_text, name="Текст страницы чужой вакансии")

        with allure.step("ОР 1: Чужая вакансия НЕ открывается (нет формы редактирования)"):
            assert foreign_fields == 0, (
                f"BOLA: чужая вакансия {foreign_id} открыта с формой редактирования "
                f"({foreign_fields} полей)! Должна быть недоступна."
            )


