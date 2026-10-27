import time
import re
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


def _get_unread_ids(page) -> set:
    """Возвращает множество ID непрочитанных откликов.

    Непрочитанная карточка имеет класс 'unread-message' (у прочитанных его нет),
    внутри карточки — ссылка a.message_card_link с href /message/<id>/detail/.
    """
    page.wait_for_load_state("networkidle", timeout=15000)
    cards = page.locator(".system_message_card.unread-message")
    ids = set()
    for i in range(cards.count()):
        link = cards.nth(i).locator("a.message_card_link")
        if link.count() == 0:
            continue
        href = link.first.get_attribute("href") or ""
        m = re.search(r"/message/(\d+)/", href)
        if m:
            ids.add(m.group(1))
    return ids


def _open_response_by_id(page, msg_id: str) -> None:
    """Открывает карточку отклика с заданным ID (клик → портал пометит прочитанным)."""
    page.wait_for_load_state("networkidle", timeout=15000)
    card_link = page.locator(f"a.message_card_link[href*='/message/{msg_id}/']")
    card_link.first.wait_for(state="visible", timeout=10000)
    card_link.first.click()
    page.wait_for_load_state("load", timeout=30000)
    # Ждём, пока детальная страница загрузится и JS пометит отклик прочитанным
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(1500)
    assert f"/message/{msg_id}/detail/" in page.url, (
        f"Ошибка: не открылся отклик {msg_id}, URL: {page.url}"
    )


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
    2. Зафиксировать начальное значение счётчика и множество непрочитанных ID.
    3. Найти вакансию по УНП нанимателя и отправить отклик.
    4. Проверить, что счётчик непрочитанных откликов увеличился на 1.
    5. Найти в списке нанимателя только что созданный отклик (новый непрочитанный ID).
    6. Открыть именно этот отклик (прочитать).
    7. Проверить, что отклик получил статус прочитанного.
    8. Проверить, что счётчик непрочитанных откликов уменьшился на 1.

    Ожидаемый результат (ОР):
    - Отклик успешно отправлен, счётчик непрочитанных увеличился.
    - Наниматель видит созданный отклик в списке.
    - После прочтения именно этого отклика счётчик непрочитанных уменьшился.
    """
    page = auth_page
    responses_page = JobSeekerResponsesPage(page)
    cfg = app_config["test_response"]
    created_resume_id = None

    try:
        # ── Шаг 0: Независимость теста — чистим аккаунт от старых резюме ──────
        with allure.step("Очистка: удаление всех резюме соискателя"):
            clear_all_resumes_from_account(page)

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

        # ── Шаг 2: Начальное состояние (счётчик + множество непрочитанных ID) ─
        with allure.step("Фиксация начального счётчика и множества непрочитанных откликов"):
            count_before = call_in_employer_browser(_get_unread_count)
            unread_before = call_in_employer_browser(_get_unread_ids)
            allure.attach(str(count_before), name="Счётчик ДО отклика")
            allure.attach(str(sorted(unread_before)), name="Непрочитанные ID ДО")

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
            # Счётчик обновляется асинхронно — опрашиваем с таймаутом
            deadline = time.time() + 25
            count_after_apply = call_in_employer_browser(_get_unread_count)
            while count_after_apply < count_before + 1 and time.time() < deadline:
                time.sleep(2)
                count_after_apply = call_in_employer_browser(_get_unread_count)
            allure.attach(str(count_after_apply), name="Счётчик ПОСЛЕ отклика")
            assert count_after_apply >= count_before + 1, (
                f"Ожидалось счётчик >= {count_before + 1}, "
                f"получено {count_after_apply}"
            )

        # ── Шаг 5: Найти только что созданный отклик (новый непрочитанный ID) ─
        with allure.step("Поиск созданного отклика в списке нанимателя (новый непрочитанный ID)"):
            # Новый отклик — это непрочитанная карточка, которой не было до отправки.
            # Опрашиваем, пока он не появится в списке (асинхронное появление).
            deadline = time.time() + 25
            new_ids = set()
            while time.time() < deadline:
                unread_after = call_in_employer_browser(_get_unread_ids)
                new_ids = unread_after - unread_before
                if new_ids:
                    break
                time.sleep(2)
            allure.attach(str(sorted(new_ids)), name="Новые непрочитанные ID")
            assert new_ids, (
                "Ошибка: созданный отклик не появился в списке нанимателя "
                f"(до: {sorted(unread_before)})"
            )
            # Если почему-то появилось несколько — берём самый новый (максимальный ID)
            new_id = max(new_ids)
            allure.attach(new_id, name="ID открываемого отклика")

        # ── Шаг 6: Открыть именно этот отклик (прочитать) ────────────────────
        with allure.step(f"Открытие отклика {new_id} (переход на /message/{new_id}/detail/)"):
            call_in_employer_browser(lambda p: _open_response_by_id(p, new_id))

        # ── Шаг 7: Отклик получил статус прочитанного ────────────────────────
        # update-status — асинхронный XHR, который гоняется с навигацией на детальную
        # страницу: иногда не успевает/отменяется. Поэтому шаг самовосстанавливающийся:
        # если карточка всё ещё непрочитана — повторно открываем детальную страницу.
        with allure.step("Проверка, что отклик помечен прочитанным"):
            def _is_read(p):
                goto_with_retry(p, EMPLOYER_RESPONSES_URL, wait_until="domcontentloaded")
                p.wait_for_load_state("networkidle", timeout=15000)
                # Карточка перестала быть unread-message → прочитана
                unread_card = p.locator(
                    f".system_message_card.unread-message a.message_card_link[href*='/message/{new_id}/']"
                )
                return unread_card.count() == 0

            def _reopen_detail(p):
                # Повторно открываем детальную страницу — портал снова пометит прочитанным
                goto_with_retry(p, EMPLOYER_RESPONSES_URL, wait_until="domcontentloaded")
                p.wait_for_load_state("networkidle", timeout=15000)
                card_link = p.locator(f"a.message_card_link[href*='/message/{new_id}/']")
                card_link.first.wait_for(state="visible", timeout=10000)
                card_link.first.click()
                p.wait_for_load_state("load", timeout=30000)
                p.wait_for_timeout(2000)

            read_deadline = time.time() + 45
            is_read = call_in_employer_browser(_is_read)
            reopen_tick = 0
            while not is_read and time.time() < read_deadline:
                time.sleep(3)
                reopen_tick += 1
                if reopen_tick % 2 == 0:
                    # Каждые ~6 сек повторно открываем детальную страницу
                    call_in_employer_browser(_reopen_detail)
                is_read = call_in_employer_browser(_is_read)
            assert is_read, (
                f"Ошибка: отклик {new_id} не получил статус прочитанного"
            )

        # ── Шаг 8: Счётчик уменьшился ────────────────────────────────────────
        with allure.step("Проверка уменьшения счётчика непрочитанных откликов"):
            # Счётчик обновляется асинхронно — опрашиваем с таймаутом
            deadline = time.time() + 25
            count_after_read = call_in_employer_browser(_get_unread_count)
            while count_after_read >= count_after_apply and time.time() < deadline:
                time.sleep(2)
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
