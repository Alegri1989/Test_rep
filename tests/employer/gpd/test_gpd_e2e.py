import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.gpd_create_page import GpdCreatePage
from helpers.network_helper import goto_with_retry
from tests.employer.gpd.conftest import GPD_ARCHIVE_URL, CREATE_GPD_URL


def _delete_gpd_by_id(page: Page, gpd_id: str):
    """Удаляет ГПД-вакансию по ID — подтверждения нет, просто ссылка."""
    delete_link = page.locator(f"a[href*='/vacancy/{gpd_id}/gpd_delete/']")
    delete_link.wait_for(state="visible", timeout=5000)
    delete_link.click()
    page.wait_for_load_state("load")


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Вакансии по ГПД")
@allure.title("Полный цикл: создание ГПД-вакансии со всеми полями → удаление")
def test_create_full_gpd_workflow(open_create_gpd_page: Page, app_config):
    """
    E2E создание вакансии по ГПД с заполнением всех полей формы.
    После сохранения проверяем редирект, затем удаляем запись.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    """
    page = open_create_gpd_page
    gpd_cfg = app_config["employer"]["test_gpd"]

    form = GpdCreatePage(page)
    gpd_id = None

    try:
        # ── Шаг 1: Предмет ГПД (Select2) ─────────────────────────────────────
        with allure.step(f"Шаг 1: Предмет ГПД '{gpd_cfg['type_gpd_label']}'"):
            form.select_type_gpd(gpd_cfg["type_gpd_label"])

        # ── Шаг 2: Наименование работы/услуги ────────────────────────────────
        with allure.step("Шаг 2: Наименование работы"):
            form.work_type_input.fill(gpd_cfg["work_type"])

        # ── Шаг 3: Сфера деятельности (Select2) ──────────────────────────────
        with allure.step(f"Шаг 3: Сфера деятельности '{gpd_cfg['area_label']}'"):
            form.select_area(gpd_cfg["area_label"])

        # ── Шаг 4: Численность граждан ───────────────────────────────────────
        with allure.step("Шаг 4: Численность граждан"):
            form.number_person_input.fill(gpd_cfg["number_person"])

        # ── Шаг 5: Жильё и варианты ──────────────────────────────────────────
        with allure.step("Шаг 5: Предоставление жилья и все варианты"):
            form.housing_checkbox.check(force=True)
            form.avaliable_housing_0.check(force=True)
            form.avaliable_housing_1.check(force=True)
            form.avaliable_housing_2.check(force=True)

        # ── Шаг 6: Сумма и примечание ────────────────────────────────────────
        with allure.step("Шаг 6: Сумма и примечание"):
            form.salary_input.fill(gpd_cfg["salary"])
            form.comments_textarea.fill(gpd_cfg["comments"])

        # ── Шаг 7: Создать вакансию ───────────────────────────────────────────
        with allure.step("Шаг 7: Нажать 'Создать вакансию'"):
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                form.submit_button.click()
            page.wait_for_load_state("networkidle", timeout=15000)

        # ── Шаг 8: Проверка редиректа ─────────────────────────────────────────
        with allure.step("ОР 1: Форма успешно сохранена (редирект произошёл)"):
            if "/gpd/create/" in page.url:
                error_details = page.evaluate("""
                    () => Array.from(document.querySelectorAll(
                        '.errorlist li, .invalid-feedback, .alert-danger'
                    )).map(el => el.innerText.trim()).filter(t => t !== '')
                """)
                raise AssertionError(
                    f"Форма не отправилась, осталась на {page.url}.\n"
                    f"Ошибки: {error_details}"
                )
            expect(page).not_to_have_url(re.compile(r"/gpd/create/"))

        # ── Шаг 9: Получить ID созданной записи ──────────────────────────────
        with allure.step("Шаг 9: Извлечение ID ГПД-вакансии"):
            goto_with_retry(page, GPD_ARCHIVE_URL, wait_until="load")
            first_link = page.locator("a[href*='/gpd_delete/']").first
            first_link.wait_for(state="visible", timeout=5000)
            href = first_link.get_attribute("href")
            id_match = re.search(r"/vacancy/(\d+)/gpd_delete/", href)
            gpd_id = id_match.group(1) if id_match else None

    finally:
        # ── Шаг 10: Удаление ─────────────────────────────────────────────────
        with allure.step("Шаг 10: Удаление тестовой ГПД-вакансии"):
            if gpd_id:
                goto_with_retry(page, GPD_ARCHIVE_URL, wait_until="load")
                _delete_gpd_by_id(page, gpd_id)

                with allure.step("ОР 2: Запись удалена"):
                    expect(
                        page.locator(f"a[href*='/vacancy/{gpd_id}/gpd_delete/']")
                    ).not_to_be_visible()
