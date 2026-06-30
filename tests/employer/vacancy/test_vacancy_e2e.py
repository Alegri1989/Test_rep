import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_create_page import VacancyCreatePage
from pages.employer_info_page import EmployerInfoPage
from helpers.network_helper import goto_with_retry

EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"
DRAFT_LIST_URL = "https://gsz.gov.by/registration/employer/vacancy/list/draft/"
CREATE_VACANCY_URL = "https://gsz.gov.by/registration/employer/vacancy/create/"


def _get_draft_count_for_workplace(page: Page, workplace_id: int) -> int:
    """Возвращает текущее количество черновиков для указанного workplace_id."""
    goto_with_retry(page, EMPLOYER_INFO_URL, wait_until="load")
    page.wait_for_load_state("load")
    draft_link = page.locator(f"a[href*='/employer/vacancy/list/draft/?workplace_id={workplace_id}']")
    draft_link.wait_for(state="visible", timeout=5000)
    text = draft_link.inner_text()
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def _delete_vacancy_by_id(page: Page, vacancy_id: str):
    """Удаляет вакансию по ID на странице черновиков."""
    delete_btn = page.locator(f"button[onclick*='open_delete_vacancy({vacancy_id})']")
    delete_btn.wait_for(state="visible", timeout=5000)
    delete_btn.click()
    confirm_btn = page.locator(
        ".modal.show button:has-text('Удалить'), "
        ".modal.show button:has-text('Да'), "
        "[id*='delete'] button[type='submit']"
    ).first
    confirm_btn.wait_for(state="visible", timeout=5000)
    confirm_btn.click()
    page.wait_for_load_state("load")


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Вакансии")
@allure.title("Полный цикл: создание вакансии со всеми полями → проверка счётчика → удаление")
def test_create_full_vacancy_workflow(open_create_vacancy_page: Page, app_config):
    """
    Бизнес-кейс: E2E создание вакансии с заполнением всех полей формы.
    После сохранения проверяем, что счётчик черновиков на карточке рабочего места
    вырос на +1, затем удаляем вакансию.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    2. Существует контактное лицо «Тест Тест».
    3. Существует рабочее место «Филиал тест» с известным workplace_id.

    Шаги:
    1. Запомнить начальный счётчик черновиков для «Филиал тест».
    2. Заполнить все поля формы создания вакансии и сохранить.
    3. Убедиться, что страница перешла на список вакансий (редирект прошёл).
    4. Открыть страницу сведений о ЮЛ и проверить, что счётчик черновиков вырос на +1.
    5. Удалить созданную вакансию со страницы черновиков.
    """
    page = open_create_vacancy_page
    vacancy_cfg = app_config["employer"]["test_vacancy"]
    employer_cfg = app_config["employer"]
    workplace_id = employer_cfg["permanent_workplace_id"]
    workplace_name = employer_cfg["permanent_workplace_name"]

    # ── Шаг 1: Запомнить начальный счётчик черновиков ────────────────────────
    with allure.step(f"Шаг 1: Получить начальный счётчик черновиков для '{workplace_name}'"):
        initial_draft_count = _get_draft_count_for_workplace(page, workplace_id)
        goto_with_retry(page, CREATE_VACANCY_URL, wait_until="load")
        page.wait_for_load_state("load")

    form = VacancyCreatePage(page)
    vacancy_id = None

    try:
        # ── Шаг 2: Заполнение блока «Контактное лицо» ────────────────────────
        with allure.step("Шаг 2: Выбор контактного лица и подтверждение данных"):
            form.contact_person_select.wait_for(state="visible", timeout=5000)
            # select_option по label может завершить поиск частичным совпадением;
            # используем value первой опции, чья метка содержит нужное имя
            all_options = form.contact_person_select.locator("option").all()
            target_value = None
            for opt in all_options:
                if vacancy_cfg["contact_person_label"] in (opt.inner_text() or ""):
                    target_value = opt.get_attribute("value")
                    break
            if target_value:
                form.contact_person_select.select_option(value=target_value)
            else:
                form.contact_person_select.select_option(label=vacancy_cfg["contact_person_label"])
            page.wait_for_timeout(1000)

            form.fio_input.wait_for(state="visible", timeout=3000)

            form.data_correct_checkbox.check(force=True)
            expect(form.data_correct_checkbox).to_be_checked()

            form.need_assistance_checkbox.check(force=True)
            expect(form.need_assistance_checkbox).to_be_checked()

        # ── Шаг 3: Блок «Профессия» ───────────────────────────────────────────
        with allure.step(f"Шаг 3: Выбор профессии '{vacancy_cfg['profession']}'"):
            form.select_profession(vacancy_cfg["profession"])
            page.wait_for_timeout(500)

            # Производная и квалификация — выбираем первый доступный вариант
            derivative_options = form.derivative_select.locator("option:not([value=''])")
            if derivative_options.count() > 0:
                first_val = derivative_options.first.get_attribute("value")
                form.derivative_select.select_option(value=first_val)

            qualification_options = form.qualification_select.locator("option:not([value=''])")
            if qualification_options.count() > 0:
                first_val = qualification_options.first.get_attribute("value")
                form.qualification_select.select_option(value=first_val)

        # ── Шаг 4: Сфера деятельности и группа занятий ───────────────────────
        with allure.step("Шаг 4: Выбор сферы деятельности и группы занятий"):
            form.select_activity_area_first()
            form.select_okz_group(vacancy_cfg["okz_group"])

        # ── Шаг 5: Количество мест и поля «из них» ───────────────────────────
        with allure.step(f"Шаг 5: Заполнение количества мест ({vacancy_cfg['available_places']})"):
            form.available_places_input.fill(vacancy_cfg["available_places"])
            # Поля «из них» — вводим 0 в каждое
            form.budget_places_input.fill("0")
            form.public_works_input.fill("0")
            form.for_students_input.fill("0")
            form.invalid_quote_input.fill("0")
            form.reservation_input.fill("0")

        # ── Шаг 6: Зарплата и ставка ──────────────────────────────────────────
        with allure.step("Шаг 6: Заполнение ставки и зарплаты"):
            form.wage_rate_input.fill(vacancy_cfg["wage_rate"])
            form.salary_input.fill(vacancy_cfg["salary"])
            form.salary_limit_input.fill(vacancy_cfg["salary_limit"])
            form.additional_info_textarea.fill(vacancy_cfg["additional_info"])

        # ── Шаг 8: Условия работы и чек-боксы ────────────────────────────────
        with allure.step("Шаг 8: Режим работы и чек-боксы условий"):
            first_nature = form.employment_nature_select.locator(
                "option:not([value=''])"
            ).first.get_attribute("value")
            form.employment_nature_select.select_option(value=first_nature)
            form.work_mode_select.select_option(label="Одна смена")

            form.for_foreigner_checkbox.check(force=True)

            form.housing_checkbox.check(force=True)
            page.wait_for_timeout(500)
            # Условные чекбоксы типов жилья (появляются после активации housing)
            form.avaliable_housing_0.check(force=True)
            form.avaliable_housing_1.check(force=True)
            form.avaliable_housing_2.check(force=True)

            form.temporary_for_students_checkbox.check(force=True)

            form.career_start_checkbox.check(force=True)
            page.wait_for_timeout(500)
            # Условные чекбоксы возрастных групп (появляются после активации career_start)
            form.age_choices_0.check(force=True)
            form.age_choices_1.check(force=True)
            form.age_choices_2.check(force=True)

        # ── Шаг 9: Требования к кандидату ────────────────────────────────────
        with allure.step("Шаг 9: Образование и опыт работы"):
            first_edu_val = form.education_select.locator(
                "option:not([value=''])"
            ).first.get_attribute("value")
            form.education_select.select_option(value=first_edu_val)
            form.experience_input.fill(vacancy_cfg["experience"])

        # ── Шаг 10: Языки ─────────────────────────────────────────────────────
        with allure.step("Шаг 10: Заполнение двух строк языков (строки 0 и 1)"):
            # Строка 0 уже видима при загрузке формы
            form.language_select_0.wait_for(state="visible", timeout=5000)
            form.language_select_0.select_option(
                value=vacancy_cfg["language_1_value"], force=True
            )
            form.lang_level_select_0.select_option(
                value=vacancy_cfg["language_level_value"], force=True
            )

            # Одно нажатие «+» добавляет строку 1
            form.add_language_button.click()
            form.language_select_1.wait_for(state="visible", timeout=5000)
            form.language_select_1.select_option(
                value=vacancy_cfg["language_2_value"], force=True
            )
            form.lang_level_select_1.select_option(
                value=vacancy_cfg["language_level_value"], force=True
            )

        # ── Шаг 11: Наличие авто и пожелания ─────────────────────────────────
        with allure.step("Шаг 11: Чек-бокс авто и пожелания"):
            form.car_needed_checkbox.check(force=True)
            form.wishes_textarea.fill(vacancy_cfg["wishes"])

        # ── Шаг 11б: Адрес рабочего места (последним — после всех AJAX) ──────
        with allure.step(f"Шаг 11б: Выбор адреса рабочего места '{workplace_name}'"):
            form.select_workplace(workplace_name)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(500)

        # ── Шаг 12: Сохранение формы ──────────────────────────────────────────
        with allure.step("Шаг 12: Нажатие 'Сохранить вакансию'"):
            # JS-обработчик Select2 заполняет region/district/address из данных workplace,
            # но оставляет их disabled (только для отображения). Снимаем disabled
            # перед сабмитом, чтобы Django получил их как обязательные поля.
            page.evaluate("""
                ['id_region', 'id_district', 'id_address'].forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.disabled = false;
                });
            """)
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                form.submit_button.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(500)

        # ── Шаг 13: Проверка редиректа ────────────────────────────────────────
        with allure.step("ОР 1: Форма успешно сохранена (редирект на список вакансий)"):
            if "/vacancy/create/" in page.url:
                error_details = page.evaluate("""
                    () => {
                        const items = document.querySelectorAll(
                            '.errorlist li, .alert-danger li, .alert-danger, '
                            + '.text-danger, [class*="error"] li, .invalid-feedback'
                        );
                        return Array.from(items).map(el => {
                            const group = el.closest(
                                '.form-group, .form-row, .col-12, .col-md-12'
                            );
                            const lbl = group
                                ? (group.querySelector('label') || {}).innerText || '?'
                                : '?';
                            return lbl.trim() + ': ' + el.innerText.trim();
                        }).filter(t => t.trim() !== ': ');
                    }
                """)
                page_text = page.evaluate(
                    "() => document.querySelector('main, .container, body').innerText"
                )
                raise AssertionError(
                    f"Форма не отправилась, осталась на {page.url}.\n"
                    f"Ошибки валидации: {error_details}\n"
                    f"Текст страницы (первые 1000 симв): {page_text[:1000]}"
                )
            expect(page).not_to_have_url(re.compile(r"/vacancy/create/"))

        # ── Шаг 14: Получить ID созданной вакансии ────────────────────────────
        with allure.step("Шаг 14: Извлечение ID созданной вакансии"):
            url_match = re.search(r"/vacancy/(\d+)/", page.url)
            if url_match:
                vacancy_id = url_match.group(1)
            else:
                goto_with_retry(
                    page,
                    f"{DRAFT_LIST_URL}?workplace_id={workplace_id}",
                    wait_until="load"
                )
                first_delete_btn = page.locator("button[onclick*='open_delete_vacancy']").first
                first_delete_btn.wait_for(state="visible", timeout=5000)
                onclick = first_delete_btn.get_attribute("onclick")
                id_match = re.search(r"open_delete_vacancy\((\d+)\)", onclick)
                vacancy_id = id_match.group(1) if id_match else None

        # ── Шаг 15: Проверка счётчика черновиков ─────────────────────────────
        with allure.step(
            f"ОР 2: Счётчик черновиков для '{workplace_name}' вырос на +1"
        ):
            new_draft_count = _get_draft_count_for_workplace(page, workplace_id)
            assert new_draft_count == initial_draft_count + 1, (
                f"Ожидался счётчик {initial_draft_count + 1}, "
                f"но получили {new_draft_count}"
            )

    finally:
        # ── Шаг 16: Удаление созданной вакансии (гарантированная очистка) ────
        with allure.step("Шаг 16: Удаление тестовой вакансии"):
            if vacancy_id:
                goto_with_retry(
                    page,
                    f"{DRAFT_LIST_URL}?workplace_id={workplace_id}",
                    wait_until="load"
                )
                _delete_vacancy_by_id(page, vacancy_id)

                with allure.step("ОР 3: Вакансия удалена — кнопки удаления с этим ID нет"):
                    deleted_btn = page.locator(
                        f"button[onclick*='open_delete_vacancy({vacancy_id})']"
                    )
                    expect(deleted_btn).not_to_be_visible()
