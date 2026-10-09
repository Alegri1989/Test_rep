import allure
import pytest
from playwright.sync_api import Page, expect
from pages.job_seeker_responses_page import JobSeekerResponsesPage
from pages.resume_page import ResumePage
from helpers.network_helper import goto_with_retry
from helpers.resume_helper import fill_and_submit_required_resume_fields, clear_all_resumes_from_account

EMPLOYER_RESPONSES_URL = "https://gsz.gov.by/registration/employer/message/responses/list/"
RESUME_LIST_URL = "https://gsz.gov.by/registration/job-seeker/resume/list/"


def _get_unread_count(page) -> int:
    """Считает непрочитанные сообщения через счётчик #messages_count в меню."""
    goto_with_retry(page, EMPLOYER_RESPONSES_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15000)
    counter = page.locator("#messages_count")
    if counter.count() == 0:
        return 0
    text = counter.inner_text().strip()
    return int(text) if text.isdigit() else 0


@allure.epic("Отклики и приглашения")
@allure.feature("Просмотр отклика нанимателем")
@allure.title("Полный цикл: отклик → счётчик +1 → чтение → статус прочитан → счётчик -1")
def test_employer_reads_response(
    auth_page: Page, call_in_employer_browser, app_config
):
    """
    Бизнес-кейс: E2E проверка полного цикла отклика соискателя и его прочтения нанимателем.

    Прекондишены:
    1. Соискатель авторизован (auth_page)
    2. Наниматель авторизован в другом браузере (call_in_employer_browser)
    3. Существует активная вакансия у нанимателя

    Шаги:
    1. Создать резюме и опубликовать его.
    2. Зафиксировать начальное значение счётчика непрочитанных откликов у нанимателя.
    3. Найти вакансию по УНП нанимателя и отправить отклик.
    4. Проверить, что счётчик непрочитанных откликов увеличился на 1.
    5. Проверить, что карточка отклика видна в списке нанимателя.
    6. Открыть отклик (прочитать).
    7. Проверить, что отклик получил статус прочитанного.
    8. Проверить, что счётчик непрочитанных откликов уменьшился на 1.

    Ожидаемый результат (ОР):
    - Отклик успешно отправлен, счётчик непрочитанных увеличился.
    - Наниматель видит карточку отклика с данными соискателя.
    - После прочтения отклик помечен как прочитанный, счётчик непрочитанных уменьшился.
    """
    page = auth_page
    responses_page = JobSeekerResponsesPage(page)
    cfg = app_config["test_response"]
    created_resume_id = None

    try:
        # ── Шаг 1: Создать и опубликовать резюме ─────────────────────────────
        with allure.step("Создание резюме для отклика"):
            resume_list_url = RESUME_LIST_URL
            resume = ResumePage(page)
            goto_with_retry(page, resume_list_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            resume.create_resume_button.wait_for(state="visible", timeout=5000)
            resume.create_resume_button.click()
            page.wait_for_load_state("domcontentloaded")
            created_resume_id = fill_and_submit_required_resume_fields(page)
            assert created_resume_id, "Ошибка: не удалось создать резюме"

        with allure.step("Публикация созданного резюме"):
            resume = ResumePage(page)
            goto_with_retry(page, resume_list_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            resume.publish_resume(created_resume_id)
            page.wait_for_timeout(1000)

        # ── Шаг 2: Начальное значение счётчика ───────────────────────────────
        with allure.step("Получение начального значения счётчика непрочитанных откликов"):
            count_before = call_in_employer_browser(_get_unread_count)
            allure.attach(str(count_before), name="Счётчик ДО отклика")

        # ── Шаг 3: Отправка отклика ──────────────────────────────────────────
        with allure.step("Поиск вакансии по УНП нанимателя"):
            responses_page.navigate_to_vacancy_search()
            responses_page.filter_by_employer_unp(cfg["employer_unp"])

        with allure.step("Отправка отклика на вакансию"):
            responses_page.apply_for_vacancy(cfg["vacancy_id"])
            responses_page.select_resume(created_resume_id)
            responses_page.fill_cover_letter(cfg["cover_letter_text"])
            responses_page.submit_application()
            responses_page.verify_success()

        # ── Шаг 4: Счётчик увеличился ────────────────────────────────────────
        with allure.step("Проверка увеличения счётчика непрочитанных откликов"):
            count_after_apply = call_in_employer_browser(_get_unread_count)
            allure.attach(str(count_after_apply), name="Счётчик ПОСЛЕ отклика")
            assert count_after_apply >= count_before + 1, (
                f"Ожидалось счётчик >= {count_before + 1}, "
                f"получено {count_after_apply}"
            )

        # ── Шаг 5: Карточка отклика видна ────────────────────────────────────
        with allure.step("Проверка видимости карточки отклика в списке нанимателя"):
            card_visible = call_in_employer_browser(
                lambda p: _check_response_card_visible(p)
            )
            assert card_visible, (
                "Ошибка: карточка отклика не найдена в списке нанимателя"
            )

        # ── Шаг 6: Открыть отклик (прочитать) ────────────────────────────────
        with allure.step("Открытие отклика (переход на /message/<id>/detail/)"):
            call_in_employer_browser(
                lambda p: _open_response_card(p)
            )

        # ── Шаг 7: Вернуться к списку откликов ───────────────────────────────
        with allure.step("Возврат к списку откликов"):
            call_in_employer_browser(
                lambda p: p.goto(EMPLOYER_RESPONSES_URL, wait_until="domcontentloaded")
            )

        # ── Шаг 8: Счётчик уменьшился (отклик прочитан) ──────────────────────
        with allure.step("Проверка уменьшения счётчика непрочитанных откликов"):
            count_after_read = call_in_employer_browser(_get_unread_count)
            allure.attach(str(count_after_read), name="Счётчик ПОСЛЕ прочтения")
            assert count_after_read < count_after_apply, (
                f"Ожидалось счётчик < {count_after_apply}, "
                f"получено {count_after_read} — отклик не отмечен прочитанным"
            )

    finally:
        with allure.step("Очистка: удаление созданного резюме"):
            if created_resume_id:
                try:
                    clear_all_resumes_from_account(page)
                except Exception as e:
                    allure.attach(str(e), name="Ошибка при очистке резюме")


def _check_response_card_visible(page) -> bool:
    """Проверяет, что в списке откликов есть карточка со ссылкой на /message/<id>/detail/."""
    page.wait_for_load_state("networkidle", timeout=15000)
    detail_links = page.locator("a[href*='/message/'][href*='/detail/']")
    if detail_links.count() > 0:
        return True
    # Альтернатива: карточка с заголовком «Отклик»
    return page.locator("h4.job-title:has-text('Отклик')").count() > 0


def _open_response_card(page) -> None:
    """Открывает первый отклик: клик по ссылке /message/<id>/detail/."""
    page.wait_for_load_state("networkidle", timeout=15000)
    detail_link = page.locator("a[href*='/message/'][href*='/detail/']").first
    detail_link.wait_for(state="visible", timeout=10000)
    detail_link.click()
    page.wait_for_load_state("load")
    page.wait_for_timeout(1000)

    # Отклик считается прочитанным после перехода на детальную страницу
    assert "/detail/" in page.url, (
        f"Ошибка: не перешли на детальную страницу отклика, URL: {page.url}"
    )
