'''
import pytest
import allure
from playwright.sync_api import Page
from pages.job_seeker_responses_page import JobSeekerResponsesPage
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


@allure.epic("Отклики и приглашения")
@allure.feature("Отклик соискателя на вакансию")
@allure.title("Часть 1: соискатель откликается на вакансию → счётчик нанимателя растёт")
def test_job_seeker_respond_to_vacancy(
    auth_page: Page, call_in_employer_browser, app_config
):
    """
    E2E тест проверки системы откликов:
    1. Авторизованный соискатель находит вакансию по УНП нанимателя
    2. Отправляет отклик с выбранным резюме и сопроводительным письмом
    3. Проверяет, что счётчик непрочитанных откликов у нанимателя увеличился

    Прекондишены:
    1. Соискатель авторизован (auth_page)
    2. Наниматель авторизован в другом браузере (call_in_employer_browser)
    3. Существует активная вакансия и резюме из конфига
    """
    page = auth_page
    responses_page = JobSeekerResponsesPage(page)
    cfg = app_config["test_response"]
    
    with allure.step("Получить начальное значение счётчика откликов"):
        count_before = call_in_employer_browser(_get_unread_count)
        allure.attach(str(count_before), "Счётчик ДО")

    with allure.step("Шаг 1: Поиск вакансии по УНП нанимателя"):
        responses_page.navigate_to_vacancy_search()
        responses_page.filter_by_employer_unp(cfg["employer_unp"])

    with allure.step("Шаг 2: Отправка отклика на вакансию"):
        responses_page.apply_for_vacancy(cfg["vacancy_id"])
        responses_page.select_resume(cfg["resume_id"])
        responses_page.fill_cover_letter(cfg["cover_letter_text"])
        responses_page.submit_application()
        responses_page.verify_success()

    with allure.step("Проверить увеличение счётчика откликов"):
        count_after = call_in_employer_browser(_get_unread_count)
        allure.attach(str(count_after), "Счётчик ПОСЛЕ")
        assert count_after == count_before + 1, f"Ожидали {count_before+1}, получили {count_after}"
        '''
