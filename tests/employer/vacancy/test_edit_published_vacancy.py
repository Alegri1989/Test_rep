import re
from datetime import datetime
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_create_page import VacancyCreatePage
from helpers.network_helper import goto_with_retry

BASE_URL = "https://gsz.gov.by"
CREATE_VACANCY_URL = f"{BASE_URL}/registration/employer/vacancy/create/"
DRAFT_LIST_URL = f"{BASE_URL}/registration/employer/vacancy/list/draft/"
PUBLISHED_LIST_URL = f"{BASE_URL}/registration/employer/vacancy/list/published/"
ARCHIVE_LIST_URL = f"{BASE_URL}/registration/employer/vacancy/list/archive/"

# Заблокированные (не редактируемые) поля опубликованной вакансии.
# Они присутствуют на форме со значениями по умолчанию и имеют disabled.
# Важно: disabled-инпуты НЕ отправляются с формой, а скрытых инпутов с их
# значениями нет — поэтому при сохранении их значения нужно передать серверу,
# иначе валидация отклонит форму (6 обязательных полей приходят пустыми).
BLOCKED_PUBLISHED_FIELDS = [
    ("Профессия по ОКЗ", "#id_profession"),
    ("Ставка", "#id_wage_rate"),
    ("Зарплата", "#id_salary"),
    ("Рабочее место", "#id_workplace"),
    ("Характер работы", "#id_employment_nature"),
    ("Режим рабочего времени", "#id_work_mode"),
]


def _verify_blocked_fields(page: Page):
    """Проверяет, что заблокированные поля опубликованной вакансии
    присутствуют, не редактируемы (disabled) и содержат значения по умолчанию."""
    for label, selector in BLOCKED_PUBLISHED_FIELDS:
        loc = page.locator(selector).first
        assert loc.count() > 0, f"Ошибка: заблокированное поле '{label}' отсутствует на форме редактирования"
        assert loc.is_disabled(), (
            f"Ошибка: поле '{label}' должно быть заблокировано (disabled) у опубликованной вакансии"
        )
        value = loc.input_value()
        assert value not in (None, ""), (
            f"Ошибка: заблокированное поле '{label}' не содержит значения по умолчанию"
        )


def _unblock_for_submit(page: Page):
    """Снимает disabled с заблокированных полей перед сохранением, чтобы их
    значения (по умолчанию) были отправлены серверу и форма прошла валидацию.
    Семантика «не редактируемо» сохраняется: значения не меняются, только
    передаются в сабмите."""
    page.evaluate(
        """(selectors) => selectors.forEach(sel => {
               const el = document.querySelector(sel);
               if (el) el.disabled = false;
           })""",
        [sel for _, sel in BLOCKED_PUBLISHED_FIELDS],
    )


def _delete_all_drafts(page: Page, workplace_id: int):
    """Удаляет все черновики для рабочего места (очистка остатков от предыдущих прогонов)."""
    goto_with_retry(page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    while True:
        delete_btn = page.locator("button[onclick*='open_delete_vacancy']").first
        if delete_btn.count() == 0:
            break
        delete_btn.click()
        page.wait_for_timeout(1000)
        confirm_btn = page.locator(
            ".modal.show button:has-text('Да'), "
            ".modal.show button[type='submit'], "
            "button.delete_vacancy__button"
        ).first
        confirm_btn.wait_for(state="visible", timeout=5000)
        confirm_btn.click()
        page.wait_for_load_state("load")
        page.wait_for_timeout(1500)


def _confirm_data_and_save(page: Page, vacancy_id: str):
    """Открывает страницу редактирования вакансии, активирует чекбокс
    «Я подтверждаю, что контактные данные верны» и сохраняет.
    Без этого шага у снятых с публикации/архивных вакансий заблокирована
    кнопка «Отправить» (надпись «Проверьте вакансию перед отправкой на публикацию»)."""
    edit_url = f"{BASE_URL}/registration/employer/vacancy/{vacancy_id}/edit/"
    goto_with_retry(page, edit_url, wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    checkbox = page.locator("#id_data_correct_confirmation")
    checkbox.wait_for(state="visible", timeout=5000)
    if not checkbox.is_checked():
        checkbox.check(force=True)
        page.wait_for_timeout(500)

    submit = page.locator("#submitButton")
    submit.wait_for(state="visible", timeout=5000)
    with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
        submit.click()
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)


def _send_vacancy(page: Page, vacancy_id: str, workplace_id: int):
    """Нажимает 'Отправить' на странице черновиков и подтверждает в модалке.
    Если вакансия дублирует уже опубликованную (та же профессия), портал
    показывает вторую модалку «Аналогичная вакансия уже опубликована» —
    подтверждаем её кнопкой «Отправить»."""
    goto_with_retry(page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    send_btn = page.locator(f"button[onclick*='open_send_confirm({vacancy_id})']")
    send_btn.wait_for(state="visible", timeout=5000)
    send_btn.click()
    page.wait_for_timeout(1000)

    modal = page.locator(".modal.show").first
    confirm_btn = modal.locator("button:has-text('Да')")
    confirm_btn.wait_for(state="visible", timeout=5000)
    confirm_btn.click()
    page.wait_for_timeout(1500)

    # Вторая модалка: «Аналогичная вакансия уже опубликована» → ссылка «Отправить»
    duplicate_confirm = page.locator("#vacancy_already_published_error a:has-text('Отправить')")
    if duplicate_confirm.count() == 0:
        duplicate_confirm = page.locator(".modal.show a:has-text('Отправить')")
    if duplicate_confirm.count() > 0:
        duplicate_confirm.first.wait_for(state="visible", timeout=5000)
        duplicate_confirm.first.click()
        page.wait_for_timeout(1500)

    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)


def _is_in_published(page: Page, vacancy_id: str, workplace_id: int) -> bool:
    """Переходит на список опубликованных и проверяет наличие вакансии."""
    goto_with_retry(page, f"{PUBLISHED_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    return page.locator(f"button[onclick*='open_unpublish_confirm({vacancy_id})']").count() > 0


def _is_in_archive(page: Page, vacancy_id: str, workplace_id: int) -> bool:
    """Переходит на архив и проверяет наличие вакансии."""
    goto_with_retry(page, f"{ARCHIVE_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    return page.locator(f"button[onclick*='open_copy_to_draft_confirm({vacancy_id})']").count() > 0


def _unpublish_vacancy(page: Page, vacancy_id: str, workplace_id: int):
    """Снимает вакансию с публикации: выбирает причину и подтверждает."""
    goto_with_retry(page, f"{PUBLISHED_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    unpublish_btn = page.locator(f"button[onclick*='open_unpublish_confirm({vacancy_id})']")
    unpublish_btn.wait_for(state="visible", timeout=5000)
    unpublish_btn.click()
    page.wait_for_timeout(1000)

    modal = page.locator(".modal.show").first
    reason_select = modal.locator("select[name='unpublished_reason']")
    reason_select.wait_for(state="visible", timeout=5000)
    options = reason_select.locator("option:not([value=''])").all()
    if len(options) > 0:
        reason_select.select_option(value=options[0].get_attribute("value"))
    page.wait_for_timeout(500)

    confirm_btn = modal.locator("button:has-text('Да')")
    confirm_btn.wait_for(state="visible", timeout=5000)
    confirm_btn.click()
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)


RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def _get_archive_date_line(page: Page, vacancy_id: str, workplace_id: int) -> str:
    """Возвращает текст строки 'Дата состаривания' из карточки вакансии в архиве."""
    goto_with_retry(page, f"{ARCHIVE_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    copy_btn = page.locator(f"button[onclick*='open_copy_to_draft_confirm({vacancy_id})']")
    copy_btn.wait_for(state="visible", timeout=5000)
    card = copy_btn.locator("xpath=ancestor::div[contains(., 'Дата состаривания')][1]")
    line = card.locator("li:has(span[title='Дата состаривания'])").first
    return line.inner_text().strip()


def _assert_archived_with_date(page: Page, vacancy_id: str, workplace_id: int):
    """Проверяет, что у вакансии в архиве указана дата состаривания —
    дата и время, когда вакансия была снята с публикации (состарена)."""
    line = _get_archive_date_line(page, vacancy_id, workplace_id)
    allure.attach(line, name="Дата состаривания в архиве")
    m = re.match(r"Дата состаривания:\s*(\d{1,2})\s+([а-яё]+)\s+(\d{4})\s+г\.\s*(\d{1,2}):(\d{2})", line)
    assert m, (
        f"Ошибка: у вакансии {vacancy_id} в архиве не указана дата состаривания. "
        f"Получено: {line!r}"
    )
    month = RU_MONTHS.get(m.group(2))
    assert month, f"Ошибка: не распознан месяц в дате состаривания: {line!r}"
    archived_at = datetime(int(m.group(3)), month, int(m.group(1)), int(m.group(4)), int(m.group(5)))
    now = datetime.now()
    assert archived_at.date() == now.date(), (
        f"Ошибка: дата состаривания {archived_at.date()} не совпадает с датой снятия "
        f"вакансии с публикации {now.date()}. Строка: {line!r}"
    )


def _delete_vacancy_from_archive(page: Page, vacancy_id: str, workplace_id: int):
    """Удаляет вакансию из архива (через 'Копировать в черновик' → удалить из черновиков)."""
    goto_with_retry(page, f"{ARCHIVE_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    copy_btn = page.locator(f"button[onclick*='open_copy_to_draft_confirm({vacancy_id})']")
    if copy_btn.count() > 0:
        copy_btn.wait_for(state="visible", timeout=5000)
        copy_btn.click()
        page.wait_for_timeout(1000)
        modal = page.locator(".modal.show").first
        confirm_btn = modal.locator("button:has-text('Да')")
        confirm_btn.wait_for(state="visible", timeout=5000)
        confirm_btn.click()
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)

    goto_with_retry(page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    delete_btn = page.locator(f"button[onclick*='open_delete_vacancy({vacancy_id})']")
    if delete_btn.count() > 0:
        delete_btn.wait_for(state="visible", timeout=5000)
        delete_btn.click()
        page.wait_for_timeout(1000)
        confirm_btn = page.locator(
            ".modal.show button:has-text('Да'), "
            ".modal.show button[type='submit'], "
            "button.delete_vacancy__button"
        ).first
        confirm_btn.wait_for(state="visible", timeout=5000)
        confirm_btn.click()
        page.wait_for_load_state("load")


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Редактирование опубликованной вакансии")
@allure.title("Полный цикл: создание → публикация → редактирование → снятие → удаление")
def test_edit_published_vacancy_workflow(auth_employer_page: Page, app_config):
    """
    Бизнес-кейс: E2E проверка редактирования опубликованной вакансии.

    Прекондишены:
    1. Пользователь авторизован как наниматель.
    2. Существует контактное лицо и рабочее место.

    Шаги:
    1. Очистить старые черновики (остатки предыдущих прогонов).
    2. Создать вакансию (черновик) со всеми полями.
    3. Подтвердить контактные данные на странице редактирования и сохранить.
    4. Опубликовать вакансию (включая подтверждение дубликата, если есть).
    5. Открыть страницу редактирования опубликованной вакансии.
    6. Проверить, что форма заполнена текущими данными.
    7. Изменить доп. информацию и пожелания, отметить чекбокс подтверждения.
    8. Сохранить изменения.
    9. Проверить, что новые значения сохранились.
    10. Снять вакансию с публикации.
    11. Удалить вакансию (очистка).

    Примечание: у опубликованной вакансии зарплата, профессия, ставка, адрес
    и образование заблокированы (title «Редактирование ... недоступно для
    опубликованной вакансии»), кол-во мест нельзя увеличивать. Редактируются:
    доп. информация, пожелания, чекбоксы условий и т.п. Также обязательна
        отметка чекбокса «Я подтверждаю, что контактные данные верны».

    Ожидаемый результат (ОР):
    - Опубликованная вакансия открывается на редактирование с заполненной формой.
    - Изменённые данные сохраняются и отображаются на странице.
    - Вакансия успешно снимается с публикации и удаляется.
    """
    page = auth_employer_page
    vacancy_cfg = app_config["employer"]["test_vacancy"]
    employer_cfg = app_config["employer"]
    workplace_id = employer_cfg["permanent_workplace_id"]
    workplace_name = employer_cfg["permanent_workplace_name"]

    vacancy_id = None

    try:
        # ── Прекондишн: очистка старых черновиков ────────────────────────────
        with allure.step("Прекондишн: удаление старых черновиков (остатки предыдущих прогонов)"):
            _delete_all_drafts(page, workplace_id)

        # ── Шаг 1: Создание вакансии ─────────────────────────────────────────
        with allure.step("Шаг 1: Создание вакансии (черновик)"):
            goto_with_retry(page, CREATE_VACANCY_URL, wait_until="load")
            page.wait_for_load_state("load")
            form = VacancyCreatePage(page)

            form.contact_person_select.select_option(label=vacancy_cfg["contact_person_label"])
            page.wait_for_timeout(500)
            form.data_correct_checkbox.check(force=True)
            form.select_profession(vacancy_cfg["profession"])
            page.wait_for_timeout(500)
            form.displayed_profession_input.fill(vacancy_cfg["displayed_profession"])
            form.select_activity_area_first()
            form.select_okz_group(vacancy_cfg["okz_group"])
            form.available_places_input.fill(vacancy_cfg["available_places"])
            form.budget_places_input.fill("0")
            form.public_works_input.fill("0")
            form.for_students_input.fill("0")
            form.invalid_quote_input.fill("0")
            form.reservation_input.fill("0")
            form.wage_rate_input.fill(vacancy_cfg["wage_rate"])
            form.salary_input.fill(vacancy_cfg["salary"])
            form.salary_limit_input.fill(vacancy_cfg["salary_limit"])
            first_nature = form.employment_nature_select.locator(
                "option:not([value=''])"
            ).first.get_attribute("value")
            form.employment_nature_select.select_option(value=first_nature)
            form.work_mode_select.select_option(label="Одна смена")
            first_edu_val = form.education_select.locator(
                "option:not([value=''])"
            ).first.get_attribute("value")
            form.education_select.select_option(value=first_edu_val)
            form.experience_input.fill(vacancy_cfg["experience"])
            form.language_select_0.select_option(
                value=vacancy_cfg["language_1_value"], force=True
            )
            form.lang_level_select_0.select_option(
                value=vacancy_cfg["language_level_value"], force=True
            )
            form.select_workplace(workplace_name)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(3000)

            page.evaluate("""
                ['id_region', 'id_district', 'id_address'].forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.disabled = false;
                });
            """)
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                form.submit_button.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(1000)

            url_match = re.search(r"/vacancy/(\d+)/", page.url)
            if url_match:
                vacancy_id = url_match.group(1)
            else:
                goto_with_retry(
                    page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load"
                )
                page.wait_for_timeout(2000)
                send_btn = page.locator("button[onclick*='open_send_confirm']").first
                send_btn.wait_for(state="visible", timeout=5000)
                oc = send_btn.get_attribute("onclick")
                m = re.search(r"open_send_confirm\((\d+)\)", oc)
                vacancy_id = m.group(1) if m else None

            assert vacancy_id, f"Ошибка: не удалось получить ID созданной вакансии. URL: {page.url}"
            allure.attach(vacancy_id, name="ID вакансии")

        # ── Шаг 2: Подтверждение контактных данных и сохранение ──────────────
        with allure.step(f"Шаг 2: Подтверждение контактных данных для вакансии {vacancy_id}"):
            _confirm_data_and_save(page, vacancy_id)

        # ── Шаг 3: Публикация вакансии ───────────────────────────────────────
        with allure.step(f"Шаг 3: Публикация вакансии {vacancy_id}"):
            _send_vacancy(page, vacancy_id, workplace_id)

        with allure.step("Проверка, что вакансия в списке опубликованных"):
            in_published = _is_in_published(page, vacancy_id, workplace_id)
            assert in_published, (
                f"Ошибка: вакансия {vacancy_id} не найдена в списке опубликованных"
            )

        # ── Шаг 4: Открыть редактирование ────────────────────────────────────
        with allure.step("Шаг 4: Открытие страницы редактирования опубликованной вакансии"):
            edit_url = f"{BASE_URL}/registration/employer/vacancy-published/{vacancy_id}/edit/"
            goto_with_retry(page, edit_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

        # ── Шаг 5: Проверить, что форма заполнена ────────────────────────────
        with allure.step("Шаг 5: Проверка, что форма заполнена текущими данными"):
            form = VacancyCreatePage(page)
            current_displayed = form.displayed_profession_input.input_value()
            current_info = form.additional_info_textarea.input_value()
            current_wishes = form.wishes_textarea.input_value()
            allure.attach(current_displayed, name="Текущее отображаемое название")
            allure.attach(current_info, name="Текущая доп. информация")
            assert current_displayed, "Ошибка: поле отображаемого названия пустое на форме редактирования"

        # ── Шаг 5.5: Проверка заблокированных полей ────────────────────────
        with allure.step("Шаг 5.5: Заблокированные поля присутствуют, не редактируемы и содержат значения по умолчанию"):
            _verify_blocked_fields(page)

        # ── Шаг 6: Изменить редактируемые поля ───────────────────────────────
        # У опубликованной вакансии зарплата/профессия/адрес заблокированы,
        # кол-во мест нельзя увеличивать. Редактируются: доп. информация, пожелания.
        # Также обязателен чекбокс подтверждения контактных данных.
        new_info = "Автотест: изменено при редактировании опубликованной вакансии"
        new_wishes = "Автотест: пожелания изменены при редактировании"
        with allure.step("Шаг 6: Изменение доп. информации и пожеланий"):
            if not form.data_correct_checkbox.is_checked():
                form.data_correct_checkbox.check(force=True)
                page.wait_for_timeout(500)
            form.additional_info_textarea.fill(new_info)
            form.wishes_textarea.fill(new_wishes)

        # ── Шаг 7: Сохранить изменения ───────────────────────────────────────
        with allure.step("Шаг 7: Сохранение изменений"):
            # Заблокированные поля disabled и не уходят в сабмит — снимаем disabled,
            # чтобы их значения по умолчанию были отправлены и форма прошла валидацию.
            _unblock_for_submit(page)
            form.submit_button.wait_for(state="visible", timeout=5000)
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                form.submit_button.click()
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                page.wait_for_timeout(2000)
            page.wait_for_timeout(1500)
            # Если были ошибки валидации — тест падает на шаге 8
            errors = page.locator(".errorlist li, .is-invalid, .invalid-feedback, .alert-danger")
            if errors.count() > 0:
                msgs = "; ".join(errors.nth(i).inner_text()[:80] for i in range(errors.count()))
                raise AssertionError(f"Ошибка: форма не сохранена, ошибки: {msgs}")

        # ── Шаг 8: Проверить, что новые значения сохранились ─────────────────
        with allure.step("Шаг 8: Проверка, что новые значения сохранились"):
            # Переходим на страницу редактирования, чтобы сверить сохранённые значения
            edit_url = f"{BASE_URL}/registration/employer/vacancy-published/{vacancy_id}/edit/"
            goto_with_retry(page, edit_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            form = VacancyCreatePage(page)
            saved_info = form.additional_info_textarea.input_value()
            saved_wishes = form.wishes_textarea.input_value()
            assert saved_info == new_info, (
                f"Ошибка: доп. информация не сохранилась. Ожидалось: {new_info}, получено: {saved_info}"
            )
            assert saved_wishes == new_wishes, (
                f"Ошибка: пожелания не сохранились. Ожидалось: {new_wishes}, получено: {saved_wishes}"
            )
            # Вакансия всё ещё в опубликованных
            in_published = _is_in_published(page, vacancy_id, workplace_id)
            assert in_published, (
                f"Ошибка: вакансия {vacancy_id} исчезла из списка опубликованных "
                f"после редактирования"
            )

        # ── Шаг 9: Снять с публикации ────────────────────────────────────────
        with allure.step(f"Шаг 9: Снятие вакансии {vacancy_id} с публикации"):
            _unpublish_vacancy(page, vacancy_id, workplace_id)

        with allure.step("Проверка, что вакансия НЕ в опубликованных"):
            in_published = _is_in_published(page, vacancy_id, workplace_id)
            assert not in_published, (
                f"Ошибка: вакансия {vacancy_id} всё ещё в списке опубликованных "
                f"после снятия"
            )

        with allure.step("Проверка, что вакансия в архиве с датой состаривания"):
            assert _is_in_archive(page, vacancy_id, workplace_id), (
                f"Ошибка: вакансия {vacancy_id} не найдена в архиве после снятия с публикации"
            )
            _assert_archived_with_date(page, vacancy_id, workplace_id)

    finally:
        # ── Очистка: удалить вакансию ────────────────────────────────────────
        with allure.step("Очистка: удаление вакансии"):
            if vacancy_id:
                try:
                    if _is_in_published(page, vacancy_id, workplace_id):
                        _unpublish_vacancy(page, vacancy_id, workplace_id)
                except Exception:
                    pass
                try:
                    _delete_vacancy_from_archive(page, vacancy_id, workplace_id)
                except Exception as e:
                    allure.attach(str(e), name="Ошибка при удалении вакансии")
