import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_create_page import VacancyCreatePage
from helpers.network_helper import goto_with_retry

CREATE_VACANCY_URL = "https://gsz.gov.by/registration/employer/vacancy/create/"
BASE_URL = "https://gsz.gov.by"


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Валидация формы создания вакансии")
class TestVacancyValidationNegative:
    """Негативные сценарии: форма создания вакансии с невалидными/пустыми полями
    не должна отправляться на сервер."""

    @allure.title("Негатив: Пустая форма не отправляется (обязательные поля)")
    def test_empty_form_blocks_submit(self, open_create_vacancy_page: Page):
        """
        Бизнес-кейс: Негативный сценарий (пустая форма): отправка формы создания вакансии
        без заполнения обязательных полей блокируется серверной валидацией.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта форма создания вакансии.

    Шаги:
    1. Отправить пустую форму, не заполнив обязательные поля.

    Ожидаемый результат (ОР):
    - Пользователь остаётся на странице создания (нет редиректа).
    - В интерфейсе появляется сообщение об ошибке валидации.
    """
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        with allure.step("Шаг 1: Отправка пустой формы"):
            form.submit_button.click()
            page.wait_for_load_state("load")

        with allure.step("ОР 1: Нет редиректа (форма не отправлена)"):
            assert "/vacancy/create/" in page.url, (
                f"Ошибка: пустая форма была отправлена, URL: {page.url}"
            )

        with allure.step("ОР 2: В интерфейсе появилось сообщение об ошибке валидации"):
            error = page.locator(".invalid-feedback, .errorlist li").first
            expect(error).to_be_visible(timeout=5000)

    @allure.title("Негатив: Невалидная зарплата (не число) блокирует создание")
    def test_invalid_salary_blocks_submit(self, open_create_vacancy_page: Page):
        """
        Бизнес-кейс: Негативный сценарий (невалидный ввод): нечисловое значение в поле
        зарплаты не проходит серверную валидацию.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта форма создания вакансии.

    Шаги:
    1. Ввести нечисловое значение в поле зарплаты.
    2. Попробовать создать вакансию.

    Ожидаемый результат (ОР):
    - Пользователь остаётся на странице создания (нет редиректа).
    - В интерфейсе появляется сообщение об ошибке валидации.
    """
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        with allure.step("Шаг 1: Ввод нечислового значения в поле зарплаты"):
            form.salary_input.wait_for(state="visible", timeout=5000)
            form.salary_input.fill("abcнецифра")

        with allure.step("Шаг 2: Попытка создания вакансии"):
            form.submit_button.click()
            page.wait_for_load_state("load")

        with allure.step("ОР 1: Нет редиректа (форма не отправлена)"):
            assert "/vacancy/create/" in page.url, (
                f"Ошибка: невалидная форма была отправлена, URL: {page.url}"
            )

        with allure.step("ОР 2: В интерфейсе появилось сообщение об ошибке валидации"):
            error = page.locator(".invalid-feedback, .errorlist li").first
            expect(error).to_be_visible(timeout=5000)

    @allure.title("Негатив: Отрицательная зарплата блокирует создание")
    def test_negative_salary_blocks_submit(self, open_create_vacancy_page: Page):
        """
        Бизнес-кейс: Негативный сценарий (невалидный ввод): отрицательное значение в поле
        зарплаты не проходит серверную валидацию.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта форма создания вакансии.

    Шаги:
    1. Ввести отрицательное значение в поле зарплаты.
    2. Попробовать создать вакансию.

    Ожидаемый результат (ОР):
    - Пользователь остаётся на странице создания (нет редиректа).
    - В интерфейсе появляется сообщение об ошибке валидации.
    """
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        with allure.step("Шаг 1: Ввод отрицательного значения в поле зарплаты"):
            form.salary_input.wait_for(state="visible", timeout=5000)
            form.salary_input.fill("-1000")

        with allure.step("Шаг 2: Попытка создания вакансии"):
            form.submit_button.click()
            page.wait_for_load_state("load")

        with allure.step("ОР 1: Нет редиректа (форма не отправлена)"):
            assert "/vacancy/create/" in page.url, (
                f"Ошибка: невалидная форма была отправлена, URL: {page.url}"
            )

        with allure.step("ОР 2: В интерфейсе появилось сообщение об ошибке валидации"):
            error = page.locator(".invalid-feedback, .errorlist li").first
            expect(error).to_be_visible(timeout=5000)



@allure.epic("Безопасность")
@allure.feature("BOLA — чужие вакансии")
class TestVacancyBOLA:
    """BOLA (Broken Object Level Authorization) тесты:
    попытка открыть/изменить/удалить чужую вакансию должна быть отклонена."""

    @allure.title("Безопасность: Запрет открытия чужой вакансии (BOLA GET)")
    def test_bola_cannot_open_foreign_vacancy(self, auth_employer_page: Page):
        """
        Бизнес-кейс: BOLA (read): попытка открыть детальную страницу чужой вакансии

должна быть отклонена (403/404) или перенаправлена (302).

        Источник чужого ID: первая вакансия из публичного поиска.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    2. Существует чужая вакансия в публичном поиске.

    Шаги:
    1. Найти чужую вакансию через публичный поиск.
    2. Выполнить прямой GET на /employer/vacancy/{foreign_id}/detail/.

    Ожидаемый результат (ОР):
    - Сервер отклонил доступ (403/404) или перенаправил (302).
    """
        page = auth_employer_page

        with allure.step("Шаг 1: Поиск чужой вакансии через публичный поиск"):
            search_url = f"{BASE_URL}/registration/vacancy-search/"
            goto_with_retry(page, search_url, wait_until="load")
            page.wait_for_load_state("networkidle")

            first_card_link = page.locator("a.debounced-link").first
            first_card_link.wait_for(state="visible", timeout=10000)
            href = first_card_link.get_attribute("href")
            match = re.search(r"/vacancy/([\w-]+)/", href)
            assert match, f"Не удалось извлечь ID вакансии из href: {href}"
            foreign_id = match.group(1)
            allure.attach(foreign_id, name="Чужой ID вакансии")

        with allure.step(f"Шаг 2: Прямой GET на /employer/vacancy/{foreign_id}/detail/"):
            detail_url = f"{BASE_URL}/registration/employer/vacancy/{foreign_id}/detail/"
            response = page.request.get(detail_url)
            allure.attach(str(response.status), name="HTTP статус GET")

        with allure.step("ОР 1: Сервер отклонил доступ (403/404) или перенаправил (302)"):
            assert response.status in (302, 403, 404), (
                f"BOLA GET: ожидался 302/403/404, получен {response.status}. "
                f"Возможно, чужая вакансия была открыта!"
            )

    @allure.title("Безопасность: Запрет УДАЛЕНИЯ чужой вакансии (BOLA DELETE)")
    def test_bola_cannot_delete_foreign_vacancy(self, auth_employer_page: Page):
        """
        Бизнес-кейс: BOLA (delete): попытка удалить чужую вакансию должна быть отклонена (403/404),

вакансия должна остаться в публичном поиске.

        Источник чужого ID: первая вакансия из публичного поиска.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    2. Существует чужая вакансия в публичном поиске.

    Шаги:
    1. Найти чужую вакансию через публичный поиск.
    2. Выполнить прямой GET на /employer/vacancy/{foreign_id}/delete.
    3. Проверить, что чужая вакансия по-прежнему существует в публичном поиске.

    Ожидаемый результат (ОР):
    - Сервер отклонил удаление (403/404).
    - Чужая вакансия по-прежнему существует в публичном поиске.
    """
        page = auth_employer_page

        with allure.step("Шаг 1: Поиск чужой вакансии через публичный поиск"):
            search_url = f"{BASE_URL}/registration/vacancy-search/"
            goto_with_retry(page, search_url, wait_until="load")
            page.wait_for_load_state("networkidle")

            first_card_link = page.locator("a.debounced-link").first
            first_card_link.wait_for(state="visible", timeout=10000)
            href = first_card_link.get_attribute("href")
            match = re.search(r"/vacancy/([\w-]+)/", href)
            assert match, f"Не удалось извлечь ID вакансии из href: {href}"
            foreign_id = match.group(1)
            allure.attach(foreign_id, name="Чужой ID вакансии")

        with allure.step(f"Шаг 2: Прямой GET на /employer/vacancy/{foreign_id}/delete"):
            delete_url = f"{BASE_URL}/registration/employer/vacancy/{foreign_id}/delete"
            response = page.request.get(
                delete_url,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            allure.attach(str(response.status), name="HTTP статус DELETE")

        with allure.step("ОР 1: Сервер отклонил удаление (403/404)"):
            assert response.status in (403, 404), (
                f"BOLA DELETE: ожидался 403/404, получен {response.status}. "
                f"Возможно, чужая вакансия была удалена!"
            )

        with allure.step("ОР 2: Чужая вакансия по-прежнему существует в публичном поиске"):
            goto_with_retry(page, search_url, wait_until="load")
            page.wait_for_load_state("networkidle")
            still_exists = page.locator(f"a[href*='/vacancy/{foreign_id}/']")
            assert still_exists.count() > 0, (
                f"BOLA DELETE: вакансия {foreign_id} исчезла из публичного поиска — возможно, была удалена!"
            )

    @allure.title("Безопасность: Запрет ИЗМЕНЕНИЯ чужой вакансии (BOLA POST)")
    def test_bola_cannot_modify_foreign_vacancy(self, auth_employer_page: Page):
        """
        Бизнес-кейс: BOLA (write): попытка отправить форму обновления чужой вакансии

должна быть отклонена сервером (403/404), данные не должны измениться.

        Источник чужого ID: первая вакансия из публичного поиска.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    2. Существует чужая вакансия в публичном поиске.

    Шаги:
    1. Найти чужую вакансию через публичный поиск.
    2. Выполнить прямой POST на /employer/vacancy/{foreign_id}/update/ с изменённой зарплатой.

    Ожидаемый результат (ОР):
    - Сервер отклонил изменение (403/404).
    """
        page = auth_employer_page

        with allure.step("Шаг 1: Поиск чужой вакансии через публичный поиск"):
            search_url = f"{BASE_URL}/registration/vacancy-search/"
            goto_with_retry(page, search_url, wait_until="load")
            page.wait_for_load_state("networkidle")

            first_card_link = page.locator("a.debounced-link").first
            first_card_link.wait_for(state="visible", timeout=10000)
            href = first_card_link.get_attribute("href")
            match = re.search(r"/vacancy/([\w-]+)/", href)
            assert match, f"Не удалось извлечь ID вакансии из href: {href}"
            foreign_id = match.group(1)
            allure.attach(foreign_id, name="Чужой ID вакансии")

        with allure.step(f"Шаг 2: Прямой POST на /employer/vacancy/{foreign_id}/update/"):
            update_url = f"{BASE_URL}/registration/employer/vacancy/{foreign_id}/update/"
            response = page.request.post(
                update_url,
                data={"id_salary": "999999"},
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            allure.attach(str(response.status), name="HTTP статус POST")

        with allure.step("ОР 1: Сервер отклонил изменение (403/404)"):
            assert response.status in (403, 404), (
                f"BOLA POST: ожидался 403/404, получен {response.status}. "
                f"Возможно, чужая вакансия была изменена!"
            )
