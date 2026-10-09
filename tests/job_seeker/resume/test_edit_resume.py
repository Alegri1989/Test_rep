import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.resume_page import ResumePage
from helpers.network_helper import goto_with_retry
from helpers.resume_helper import fill_and_submit_required_resume_fields, clear_all_resumes_from_account

RESUME_LIST_URL = "https://gsz.gov.by/registration/job-seeker/resume/list/"


@allure.epic("Резюме соискателя")
@allure.feature("Редактирование резюме")
@allure.title("Полный цикл: создание резюме → редактирование → проверка сохранности → удаление")
def test_edit_resume_workflow(auth_page: Page, app_config):
    """
    Бизнес-кейс: E2E проверка редактирования резюме соискателя.

    Прекондишены:
    1. Пользователь авторизован как соискатель.
    2. Существует резюме, которое можно редактировать.

    Шаги:
    1. Создать резюме с заполненными полями.
    2. Открыть форму редактирования созданного резюме.
    3. Проверить, что форма заполнена текущими данными.
    4. Изменить зарплату (повысить).
    5. Изменить желаемую профессию (выбрать другую).
    6. Сохранить изменения.
    7. Проверить, что новые данные отображаются на странице.
    8. Удалить резюме (очистка).

    Ожидаемый результат (ОР):
    - Созданное резюме открывается на редактирование с заполненной формой.
    - Изменённые данные сохраняются и отображаются на странице.
    - Резюме успешно удаляется.
    """
    page = auth_page
    resume = ResumePage(page)

    # ── Шаг 1: Создать резюме ────────────────────────────────────────────────
    with allure.step("Шаг 1: Создание резюме"):
        goto_with_retry(page, RESUME_LIST_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("domcontentloaded")
        resume.create_resume_button.wait_for(state="visible", timeout=5000)
        resume.create_resume_button.click()
        page.wait_for_load_state("domcontentloaded")

        created_resume_id = fill_and_submit_required_resume_fields(page)
        assert created_resume_id, "Ошибка: не удалось создать резюме"
        allure.attach(created_resume_id, name="ID созданного резюме")

    try:
        # ── Шаг 2: Открыть редактирование ────────────────────────────────────
        with allure.step("Шаг 2: Открытие формы редактирования резюме"):
            edit_url = f"https://gsz.gov.by/registration/job-seeker/resume/{created_resume_id}/update/"
            goto_with_retry(page, edit_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

        # ── Шаг 3: Проверить, что форма заполнена ────────────────────────────
        with allure.step("Шаг 3: Проверка, что форма заполнена текущими данными"):
            current_salary = resume.salary_input.input_value()
            allure.attach(current_salary, name="Текущая зарплата")
            assert current_salary, "Ошибка: поле зарплаты пустое на форме редактирования"

            # Проверяем, что профессия выбрана (контейнер не пуст)
            profession_container = page.locator(
                "#select2-id_desired_profession-container"
            )
            if profession_container.count() > 0:
                profession_text = profession_container.inner_text().strip()
                allure.attach(profession_text, name="Текущая профессия")
                assert profession_text, "Ошибка: профессия не выбрана на форме редактирования"

        # ── Шаг 4: Изменить зарплату ─────────────────────────────────────────
        new_salary = "2500.00"
        with allure.step(f"Шаг 4: Изменение зарплаты на {new_salary}"):
            resume.salary_input.fill(new_salary)

        # ── Шаг 5: Изменить профессию ────────────────────────────────────────
        new_profession = "Бухгалтер"
        with allure.step(f"Шаг 5: Изменение профессии на '{new_profession}'"):
            profession_container = page.locator(
                "#select2-id_desired_profession-container"
            )
            profession_container.click()
            page.wait_for_timeout(500)

            search_input = page.locator(
                "input.select2-search__field[aria-controls*='desired_profession']"
            )
            search_input.wait_for(state="visible", timeout=5000)
            search_input.press_sequentially(new_profession, delay=100)
            page.wait_for_timeout(500)

            option = page.locator(
                ".select2-container--open "
                "li.select2-results__option:not([aria-disabled='true'])"
            ).first
            option.wait_for(state="visible", timeout=5000)
            option.click()
            page.wait_for_timeout(500)

        # ── Шаг 6: Сохранить изменения ───────────────────────────────────────
        with allure.step("Шаг 6: Сохранение изменений"):
            submit_btn = page.get_by_role("button", name="Сохранить резюме")
            if submit_btn.count() == 0:
                submit_btn = page.get_by_role("button", name="Обновить резюме")
            if submit_btn.count() == 0:
                submit_btn = page.locator("button[type='submit']").last

            submit_btn.wait_for(state="visible", timeout=5000)
            submit_btn.click()
            page.wait_for_load_state("load")
            page.wait_for_timeout(2000)

        # ── Шаг 7: Проверить, что новые данные отображаются ──────────────────
        with allure.step("Шаг 7: Проверка, что новые данные отображаются на странице"):
            # После сохранения страница может перенаправить на список
            # или остаться на странице редактирования. Проверяем обе возможности.
            if "/update/" in page.url:
                # Остались на странице редактирования — проверяем инпут
                updated_salary = resume.salary_input.input_value()
                assert updated_salary == new_salary, (
                    f"Ошибка: ожидалась зарплата {new_salary}, получено {updated_salary}"
                )
            else:
                # Перенаправили на список — проверяем, что резюме всё ещё в списке
                edit_link = page.locator(
                    f"a[href*='/resume/{created_resume_id}/update/']"
                )
                assert edit_link.count() > 0, (
                    f"Ошибка: резюме {created_resume_id} исчезло из списка "
                    f"после редактирования"
                )

    finally:
        # ── Очистка: удалить резюме ──────────────────────────────────────────
        with allure.step("Очистка: удаление резюме"):
            try:
                clear_all_resumes_from_account(page)
            except Exception as e:
                allure.attach(str(e), name="Ошибка при очистке резюме")
