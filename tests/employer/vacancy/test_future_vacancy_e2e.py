import re
import datetime
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.future_vacancy_create_page import FutureVacancyCreatePage
from helpers.network_helper import goto_with_retry
from tests.employer.vacancy.conftest import FUTURE_DRAFT_LIST_URL, CREATE_FUTURE_VACANCY_URL


def _delete_future_vacancy_by_id(page: Page, vacancy_id: str):
    delete_btn = page.locator(f"button[onclick*='open_delete_vacancy({vacancy_id})']")
    delete_btn.wait_for(state="visible", timeout=5000)
    delete_btn.click()
    confirm_btn = page.locator("button.delete_vacancy__button")
    confirm_btn.wait_for(state="visible", timeout=5000)
    confirm_btn.click()
    page.wait_for_load_state("load")


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Перспективные вакансии")
@allure.title("Полный цикл: создание перспективной вакансии со всеми полями → удаление")
def test_create_full_future_vacancy_workflow(
    open_create_future_vacancy_page: Page, app_config
):
    """
    E2E создание перспективной вакансии с заполнением всех полей формы.
    После сохранения проверяем редирект, затем удаляем вакансию.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    2. Существует контактное лицо «Тест Тест».
    3. Существует рабочее место «Филиал тест» с известным workplace_id.
    """
    page = open_create_future_vacancy_page
    vacancy_cfg = app_config["employer"]["test_vacancy"]
    employer_cfg = app_config["employer"]
    workplace_id = employer_cfg["permanent_workplace_id"]

    form = FutureVacancyCreatePage(page)
    vacancy_id = None

    try:
        # ── Шаг 1: Контактное лицо ───────────────────────────────────────────
        with allure.step("Шаг 1: Контактное лицо и подтверждение данных"):
            form.contact_person_select.select_option(
                label=vacancy_cfg["contact_person_label"]
            )
            form.data_correct_checkbox.check(force=True)

        # ── Шаг 2: Профессия, производная и категория ───────────────────────
        with allure.step(f"Шаг 2: Профессия, производная и квалификация"):
            form.select_profession(vacancy_cfg["profession"])
            form.derivative_select.select_option(value="1")
            form.qualification_select.select_option(value="1")

        # ── Шаг 3: Группа занятий (Select2, появляется после профессии) ──────
        with allure.step(f"Шаг 3: Выбор группы занятий '{vacancy_cfg['okz_group']}'"):
            form.select_okz_group(vacancy_cfg["okz_group"])

        # ── Шаг 4: Количество мест ───────────────────────────────────────────
        with allure.step("Шаг 4: Количество свободных рабочих мест"):
            form.available_places_input.fill(vacancy_cfg["available_places"])

        # ── Шаг 5: Зарплата ──────────────────────────────────────────────────
        with allure.step("Шаг 5: Зарплата от/до"):
            form.salary_input.fill(vacancy_cfg["salary"])
            form.salary_limit_input.fill(vacancy_cfg["salary_limit"])

        # ── Шаг 6: Рабочее место (обычный select, не Select2) ─────────────────
        with allure.step("Шаг 6: Выбор рабочего места"):
            form.workplace_select.select_option(value=str(workplace_id))

        # ── Шаг 7: Характер работы ───────────────────────────────────────────
        with allure.step("Шаг 7: Характер работы (первый вариант)"):
            first_nature = form.employment_nature_select.locator(
                "option:not([value=''])"
            ).first.get_attribute("value")
            form.employment_nature_select.select_option(value=first_nature)

        # ── Шаг 8: Режим работы и жильё ──────────────────────────────────────
        with allure.step("Шаг 8: Режим работы и чек-боксы условий"):
            form.work_mode_select.select_option(label="Одна смена")
            form.housing_checkbox.check(force=True)
            form.avaliable_housing_0.check(force=True)
            form.avaliable_housing_1.check(force=True)
            form.avaliable_housing_2.check(force=True)

        # ── Шаг 9: Образование ───────────────────────────────────────────────
        with allure.step("Шаг 9: Требование к образованию"):
            form.education_select.select_option(label="Высшее")

        # ── Шаг 10: Пожелания ────────────────────────────────────────────────
        with allure.step("Шаг 10: Пожелания к кандидату"):
            form.wishes_textarea.fill(vacancy_cfg["wishes"])

        # ── Шаг 11: Дата начала работ ────────────────────────────────────────
        with allure.step("Шаг 11: Дата начала работ — сегодня"):
            today = datetime.date.today().isoformat()
            form.works_starts_input.fill(today)

        # ── Шаг 12: Сохранение ───────────────────────────────────────────────
        with allure.step("Шаг 12: Нажать 'Создать вакансию'"):
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                form.submit_button.click()
            page.wait_for_load_state("networkidle", timeout=15000)

        # ── Шаг 13: Проверка редиректа ───────────────────────────────────────
        with allure.step("ОР 1: Форма успешно сохранена (редирект произошёл)"):
            if "/vacancy/create_future/" in page.url:
                error_details = page.evaluate("""
                    () => {
                        const items = document.querySelectorAll(
                            '.errorlist li, .invalid-feedback, .alert-danger'
                        );
                        return Array.from(items).map(el => el.innerText.trim())
                            .filter(t => t !== '');
                    }
                """)
                raise AssertionError(
                    f"Форма не отправилась, осталась на {page.url}.\n"
                    f"Ошибки: {error_details}"
                )
            expect(page).not_to_have_url(re.compile(r"/vacancy/create_future/"))

        # ── Шаг 14: Получить ID созданной вакансии ───────────────────────────
        with allure.step("Шаг 14: Извлечение ID перспективной вакансии"):
            url_match = re.search(r"/future-vacancy/(\d+)/", page.url)
            if url_match:
                vacancy_id = url_match.group(1)
            else:
                goto_with_retry(page, FUTURE_DRAFT_LIST_URL, wait_until="load")
                first_btn = page.locator(
                    "button[onclick*='open_delete_vacancy']"
                ).first
                first_btn.wait_for(state="visible", timeout=5000)
                onclick = first_btn.get_attribute("onclick")
                id_match = re.search(r"open_delete_vacancy\((\d+)\)", onclick)
                vacancy_id = id_match.group(1) if id_match else None

    finally:
        # ── Шаг 15: Удаление созданной вакансии ──────────────────────────────
        with allure.step("Шаг 15: Удаление тестовой перспективной вакансии"):
            if vacancy_id:
                goto_with_retry(page, FUTURE_DRAFT_LIST_URL, wait_until="load")
                _delete_future_vacancy_by_id(page, vacancy_id)

                with allure.step("ОР 2: Вакансия удалена"):
                    deleted_btn = page.locator(
                        f"button[onclick*='open_delete_vacancy({vacancy_id})']"
                    )
                    expect(deleted_btn).not_to_be_visible()
