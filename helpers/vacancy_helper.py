import re
import logging
from playwright.sync_api import Page
from pages.vacancy_create_page import VacancyCreatePage
from helpers.network_helper import goto_with_retry

CREATE_VACANCY_URL = "https://gsz.gov.by/registration/employer/vacancy/create/"
DRAFT_LIST_URL = "https://gsz.gov.by/registration/employer/vacancy/list/draft/"
PUBLISHED_LIST_URL = "https://gsz.gov.by/registration/employer/vacancy/list/published/"
ARCHIVE_LIST_URL = "https://gsz.gov.by/registration/employer/vacancy/list/archive/"


def _send_vacancy(page: Page, vacancy_id: str, workplace_id: int):
    """Нажимает 'Отправить' на странице черновиков и подтверждает в модалке.

    Если вакансия с той же профессией уже опубликована, появляется вторая
    модалка «Аналогичная вакансия уже опубликована», где «Отправить» — это
    якорь <a href=".../send-duplicate/?id=...">, а не кнопка.
    """
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
    page.wait_for_timeout(2500)

    duplicate_confirm = page.locator("#vacancy_already_published_error a:has-text('Отправить')")
    if duplicate_confirm.count() == 0:
        duplicate_confirm = page.locator(".modal.show a:has-text('Отправить')")
    if duplicate_confirm.count() > 0:
        duplicate_confirm.first.wait_for(state="visible", timeout=5000)
        duplicate_confirm.first.click()
        page.wait_for_timeout(2000)

    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        page.wait_for_timeout(2000)
    page.wait_for_timeout(1000)


def _delete_all_drafts(page: Page, workplace_id: int):
    """Удаляет все черновики (остатки предыдущих прогонов)."""
    goto_with_retry(page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    for _ in range(20):
        delete_btn = page.locator("button[onclick*='open_delete_vacancy']")
        if delete_btn.count() == 0:
            break
        delete_btn.first.click()
        page.wait_for_timeout(1000)
        confirm_btn = page.locator(
            ".modal.show button:has-text('Да'), "
            ".modal.show button[type='submit'], "
            "button.delete_vacancy__button"
        ).first
        confirm_btn.wait_for(state="visible", timeout=5000)
        confirm_btn.click()
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            page.wait_for_timeout(1500)
        page.wait_for_timeout(1000)


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


def _delete_vacancy_from_archive(page: Page, vacancy_id: str, workplace_id: int):
    """Удаляет вакансию из архива (через 'Копировать в черновик' → удалить из черновиков)."""
    goto_with_retry(page, f"{ARCHIVE_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    copy_btn = page.locator(f"button[onclick*='open_copy_to_draft_confirm({vacancy_id})']")
    if copy_btn.count() > 0:
        copy_btn.wait_for(state="visible", timeout=5000)
        copy_btn.click()
        modal = page.locator(".modal.show").first
        modal.wait_for(state="visible", timeout=5000)
        confirm_btn = modal.locator("#copy_to_draft_vacancy, button:has-text('Да')").first
        confirm_btn.click()
        # Копирование асинхронное (лоадер): ждём закрытия модалки
        try:
            page.locator(".modal.show").first.wait_for(state="hidden", timeout=20000)
        except Exception:
            pass
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)

    goto_with_retry(page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)

    delete_btn = page.locator(f"button[onclick*='open_delete_vacancy({vacancy_id})']")
    if delete_btn.count() > 0:
        delete_btn.wait_for(state="visible", timeout=5000)
        delete_btn.click()
        modal = page.locator(".modal.show").first
        modal.wait_for(state="visible", timeout=5000)
        confirm_btn = modal.locator(
            "#delete_vacancy, button:has-text('Да'), button[type='submit']"
        ).first
        confirm_btn.click()
        try:
            page.locator(".modal.show").first.wait_for(state="hidden", timeout=20000)
        except Exception:
            pass
        page.wait_for_load_state("load")


def _is_in_published(page: Page, vacancy_id: str, workplace_id: int) -> bool:
    """Проверяет, есть ли вакансия в списке опубликованных."""
    goto_with_retry(page, f"{PUBLISHED_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    return page.locator(f"button[onclick*='open_unpublish_confirm({vacancy_id})']").count() > 0


def create_and_publish_vacancy(page: Page, app_config: dict, displayed_profession: str | None = None) -> str:
    """Создаёт черновик и публикует вакансию. Возвращает vacancy_id.

    Используется как пре-кондишн для тестов, которым нужна своя опубликованная
    вакансия (BOLA, отклики соискателя).
    """
    employer_cfg = app_config["employer"]
    vacancy_cfg = employer_cfg["test_vacancy"]
    workplace_id = employer_cfg["permanent_workplace_id"]
    workplace_name = employer_cfg["permanent_workplace_name"]
    if displayed_profession is None:
        displayed_profession = vacancy_cfg["displayed_profession"]

    logging.debug("Действие: создание и публикация вакансии")
    _delete_all_drafts(page, workplace_id)

    goto_with_retry(page, CREATE_VACANCY_URL, wait_until="load")
    page.wait_for_load_state("load")
    form = VacancyCreatePage(page)

    form.contact_person_select.select_option(label=vacancy_cfg["contact_person_label"])
    page.wait_for_timeout(500)
    form.data_correct_checkbox.check(force=True)
    form.select_profession(vacancy_cfg["profession"])
    page.wait_for_timeout(500)
    form.displayed_profession_input.fill(displayed_profession)
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
    first_nature = form.employment_nature_select.locator("option:not([value=''])").first.get_attribute("value")
    form.employment_nature_select.select_option(value=first_nature)
    form.work_mode_select.select_option(label="Одна смена")
    first_edu_val = form.education_select.locator("option:not([value=''])").first.get_attribute("value")
    form.education_select.select_option(value=first_edu_val)
    form.experience_input.fill(vacancy_cfg["experience"])
    form.language_select_0.select_option(value=vacancy_cfg["language_1_value"], force=True)
    form.lang_level_select_0.select_option(value=vacancy_cfg["language_level_value"], force=True)
    form.select_workplace(workplace_name)
    page.wait_for_load_state("networkidle", timeout=15000)

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
        goto_with_retry(page, f"{DRAFT_LIST_URL}?workplace_id={workplace_id}", wait_until="load")
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)
        send_btn = page.locator("button[onclick*='open_send_confirm']").first
        send_btn.wait_for(state="visible", timeout=5000)
        oc = send_btn.get_attribute("onclick")
        m = re.search(r"open_send_confirm\((\d+)\)", oc)
        vacancy_id = m.group(1) if m else None

    assert vacancy_id, f"Ошибка: не удалось создать черновик вакансии. URL: {page.url}"
    logging.debug(f"Действие: отправка вакансии {vacancy_id}")
    _send_vacancy(page, vacancy_id, workplace_id)
    assert _is_in_published(page, vacancy_id, workplace_id), (
        f"Ошибка: вакансия {vacancy_id} не найдена в списке опубликованных после отправки"
    )
    return vacancy_id


def cleanup_vacancy(page: Page, vacancy_id: str | None, app_config: dict) -> None:
    """Снимает вакансию с публикации (если опубликована).

    Портал не даёт удалить вакансию из архива (только «Копировать в черновик»,
    что создаёт копию), поэтому максимум очистки — снять с публикации.
    """
    if not vacancy_id:
        return
    employer_cfg = app_config["employer"]
    workplace_id = employer_cfg["permanent_workplace_id"]
    try:
        if _is_in_published(page, vacancy_id, workplace_id):
            _unpublish_vacancy(page, vacancy_id, workplace_id)
    except Exception as e:
        logging.warning(f"Очистка: не удалось снять с публикации {vacancy_id}: {e}")
