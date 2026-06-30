import re
import allure
from playwright.sync_api import Page, expect
from pages.vacancy_search_page import VacancySearchPage
from helpers.network_helper import goto_with_retry

EMPLOYER_RESPONSES_URL = "https://gsz.gov.by/registration/employer/message/responses/list/"


def _get_unread_count(page) -> int:
    """Считает непрочитанные сообщения через счётчик #messages_count в меню."""
    goto_with_retry(page, EMPLOYER_RESPONSES_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15000)
    counter = page.locator("#messages_count")
    if counter.count() == 0:
        return 0
    text = counter.inner_text().strip()
    return int(text) if text.isdigit() else 0


# @allure.epic("Отклики и приглашения")
# @allure.feature("Отклик соискателя на вакансию")
# @allure.title("Часть 1: соискатель откликается на вакансию → счётчик нанимателя растёт")
# def test_job_seeker_respond_to_vacancy(
#     auth_page: Page, call_in_employer_browser, app_config
# ):
#     """
#     E2E: соискатель ищет вакансию по УНП, выбирает резюме, отправляет
#     отклик. После этого у нанимателя счётчик непрочитанных откликов
#     увеличивается на 1.
#
#     Прекондишены:
#     1. Соискатель авторизован (auth_page).
#     2. Браузер нанимателя запущен через call_in_employer_browser.
#     3. Опубликована вакансия vacancy_id и резюме resume_id из конфига.
#     """
#     page = auth_page
#     cfg = app_config["test_response"]
#     unp = cfg["employer_unp"]
#     vacancy_id = cfg["vacancy_id"]
#     resume_id = cfg["resume_id"]
#     cover_letter_text = cfg["cover_letter_text"]
#
#     search = VacancySearchPage(page)
#
#     # ── Прекондишн: зафиксировать счётчик нанимателя ─────────────────────
#     with allure.step("Прекондишн: считать счётчик непрочитанных откликов"):
#         count_before = call_in_employer_browser(_get_unread_count)
#         allure.attach(
#             str(count_before),
#             name="Счётчик ДО отклика",
#             attachment_type=allure.attachment_type.TEXT,
#         )
#
#     # ── Шаг 1: Открыть поиск вакансий ────────────────────────────────────
#     with allure.step("Шаг 1: Перейти на страницу поиска вакансий"):
#         search.navigate()
#         page.wait_for_load_state("networkidle", timeout=15000)
#
#     # ── Шаг 2: Фильтр по УНП нанимателя ─────────────────────────────────
#     with allure.step(f"Шаг 2: Выбрать нанимателя по УНП '{unp}'"):
#         search.open_spoiler_if_hidden("Наниматель", search.employer_dropdown)
#         search.select_employer_by_unp(unp)
#
#     # ── Шаг 3: Запустить поиск ───────────────────────────────────────────
#     with allure.step("Шаг 3: Нажать 'Поиск'"):
#         search.submit_filter_btn.click()
#         page.wait_for_load_state("networkidle", timeout=15000)
#
#     # ── Шаг 4: Нажать «Откликнуться» на найденной вакансии ───────────────
#     with allure.step(f"Шаг 4: Нажать 'Откликнуться' на вакансии {vacancy_id}"):
#         apply_link = page.locator(
#             f"a[href*='/vacancy/{vacancy_id}/detail-public/#resume-form-anchor']"
#         )
#         apply_link.wait_for(state="visible", timeout=10000)
#         apply_link.click()
#         page.wait_for_load_state("domcontentloaded", timeout=20000)
#         page.wait_for_load_state("networkidle", timeout=15000)
#
#     # ── Шаг 5: Выбрать резюме ────────────────────────────────────────────
#     with allure.step(f"Шаг 5: Выбрать резюме {resume_id}"):
#         resume_select = page.locator("#id_resume")
#         resume_select.wait_for(state="visible", timeout=10000)
#         resume_select.select_option(value=resume_id)
#
#     # ── Шаг 6: Заполнить сопроводительное письмо ─────────────────────────
#     with allure.step("Шаг 6: Заполнить сопроводительное письмо"):
#         cover_letter = page.locator("#id_text")
#         cover_letter.wait_for(state="visible", timeout=10000)
#         cover_letter.fill(cover_letter_text)
#
#     # ── Шаг 7: Отправить отклик ──────────────────────────────────────────
#     with allure.step("Шаг 7: Нажать 'Откликнуться на вакансию'"):
#         submit_btn = page.locator("button.btn-outline-success[type='submit']")
#         submit_btn.wait_for(state="visible", timeout=5000)
#         with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
#             submit_btn.click()
#         page.wait_for_load_state("networkidle", timeout=15000)
#
#     # ── Шаг 8: Проверить успешную отправку ───────────────────────────────
#     with allure.step("ОР 1: отклик отправлен — редирект на страницу откликов соискателя"):
#         # После успешной отправки Django перенаправляет на список откликов соискателя
#         expect(page).to_have_url(re.compile(r"/job-seeker/message/"))
#         error_texts = page.evaluate("""
#             () => Array.from(document.querySelectorAll(
#                 '.alert-danger, .errorlist li'
#             )).map(el => el.innerText.trim()).filter(t => t)
#         """)
#         assert not error_texts, f"Обнаружены ошибки при отклике: {error_texts}"
#
#     # ── Шаг 9: Счётчик нанимателя вырос на 1 ────────────────────────────
#     with allure.step("ОР 2: счётчик непрочитанных откликов нанимателя увеличился на 1"):
#         count_after = call_in_employer_browser(_get_unread_count)
#         allure.attach(
#             str(count_after),
#             name="Счётчик ПОСЛЕ отклика",
#             attachment_type=allure.attachment_type.TEXT,
#         )
#         assert count_after == count_before + 1, (
#             f"Ожидали {count_before + 1}, получили {count_after}"
#         )
