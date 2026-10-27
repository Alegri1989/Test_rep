"""XSS: отражённый (reflected) и сохраняемый (stored) скрипты.

Цель — убедиться, что пользовательский ввод экранируется при отражении в HTML
(поиск) и при повторном чтении сохранённых данных (резюме).
"""
import re
import allure
import pytest
from playwright.sync_api import Page

from helpers.network_helper import goto_with_retry
from pages.resume_page import ResumePage

BASE_URL = "https://gsz.gov.by"
# Маркер-пейлоад: если он отобразится в HTML без экранирования — XSS.
PAYLOAD = "<script>alert('xss_sec_scan')</script>"
PAYLOAD_ESCAPED = "&lt;script&gt;"


def _contains_unescaped(body: str) -> bool:
    """True, если в теле ответа есть НЕЭКРАНИРОВАННЫЙ пейлоад."""
    return PAYLOAD in body


def _stable_content(page: Page) -> str:
    """Возвращает HTML страницы после завершения навигации.

    Защита от флейка «Page.content: Unable to retrieve content because the page
    is navigating»: дожидаемся load и короткой стабилизации, при ошибке
    навигации повторяем чтение.
    """
    try:
        page.wait_for_load_state("load", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(500)
    for _ in range(3):
        try:
            return page.content()
        except Exception:
            page.wait_for_timeout(1000)
            try:
                page.wait_for_load_state("load", timeout=20000)
            except Exception:
                pass
    return page.content()


@allure.epic("Безопасность")
@allure.feature("XSS — отражённый (reflected)")
class TestReflectedXSS:
    """Проверка экранирования пользовательского ввода в результатах поиска."""

    @allure.title("Безопасность: Reflected XSS в поиске вакансий (поле «Профессия»)")
    def test_reflected_xss_vacancy_search(self, guest_page: Page):
        """
        Бизнес-кейс: значение из поля поиска не должно отражаться в HTML
        без экранирования — иначе выполняется произвольный JS в контексте портала.

        Ожидаемый результат (ОР): пейлоад в ответе либо отсутствует, либо экранирован.
        """
        search_url = f"{BASE_URL}/registration/vacancy-search/"
        with allure.step("Шаг 1: Заполнение поля «Профессия» XSS-пейлоадом и отправка"):
            goto_with_retry(guest_page, search_url, wait_until="load")
            guest_page.wait_for_load_state("networkidle")
            try:
                cookie_btn = guest_page.locator("a.cookie-panel__info_button").first
                cookie_btn.wait_for(state="visible", timeout=3000)
                cookie_btn.click()
            except Exception:
                pass
            prof = guest_page.locator("#id_profession")
            prof.wait_for(state="visible", timeout=10000)
            prof.fill(PAYLOAD)
            guest_page.locator("button[type='submit']").first.click()
            guest_page.wait_for_load_state("load", timeout=20000)
            guest_page.wait_for_timeout(800)

        with allure.step("Шаг 2: Анализ HTML ответа на неэкринированный пейлоад"):
            body = _stable_content(guest_page)
            allure.attach(
                f"URL: {guest_page.url}\nПейлоад найден без экранирования: {_contains_unescaped(body)}",
                name="Результат reflected XSS",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert not _contains_unescaped(body), (
                "Уязвимость (Reflected XSS): пейлоад отражается в HTML без экранирования. "
                "Возможно выполнение произвольного JavaScript."
            )

    @allure.title("Безопасность: Reflected XSS в публичном поиске резюме")
    def test_reflected_xss_resume_search(self, guest_page: Page):
        """
        Бизнес-кейс: то же, но для публичного поиска резюме (поле «Профессия»).

        Ожидаемый результат (ОР): пейлоад не отражается без экранирования.
        """
        search_url = f"{BASE_URL}/registration/resume-search/"
        with allure.step("Шаг 1: Ввод пейлоада в поле поиска резюме и отправка"):
            goto_with_retry(guest_page, search_url, wait_until="load")
            guest_page.wait_for_load_state("networkidle")
            try:
                cookie_btn = guest_page.locator("a.cookie-panel__info_button").first
                cookie_btn.wait_for(state="visible", timeout=3000)
                cookie_btn.click()
            except Exception:
                pass
            prof = guest_page.locator("#id_resume_profession")
            prof.wait_for(state="visible", timeout=10000)
            prof.fill(PAYLOAD)
            guest_page.locator("button.theme-btn.btn-style-one").first.click()
            guest_page.wait_for_load_state("load", timeout=20000)
            guest_page.wait_for_timeout(800)

        with allure.step("Шаг 2: Анализ HTML ответа"):
            body = _stable_content(guest_page)
            assert not _contains_unescaped(body), (
                "Уязвимость (Reflected XSS): пейлоад отражается в HTML публичного "
                "поиска резюме без экранирования."
            )


@allure.epic("Безопасность")
@allure.feature("XSS — сохраняемый (stored)")
class TestStoredXSS:
    """Проверка экранирования данных, сохраняемых в профиле/резюме."""

    @allure.title("Безопасность: Stored XSS в поле «Пожелания» резюме")
    def test_stored_xss_resume_wishes(self, job_seeker_page: Page):
        """
        Бизнес-кейс: текст из свободного поля резюме (пожелания) должен быть
        экранирован при сохранении и повторном чтении — иначе любой посетитель
        детальной страницы резюме получит выполнение чужого JS.

        Ожидаемый результат (ОР): сохранённый пейлоад отображается экранированным.
        """
        page = job_seeker_page
        created_id = None
        try:
            with allure.step("Шаг 0: Независимость теста — очистка аккаунта от старых резюме"):
                from helpers.resume_helper import clear_all_resumes_from_account
                clear_all_resumes_from_account(page)

            with allure.step("Шаг 1: Создание резюме с XSS-пейлоадом в поле «Пожелания»"):
                list_url = f"{BASE_URL}/registration/job-seeker/resume/list/"
                goto_with_retry(page, list_url, wait_until="load")
                page.wait_for_load_state("networkidle")
                resume = ResumePage(page)
                # Ждём появления кнопки создания, затем кликаем (защита от гонок в полной суите)
                resume.create_resume_button.wait_for(state="visible", timeout=20000)
                resume.create_resume_button.click()
                page.wait_for_load_state("load")

                resume.profession_container.wait_for(state="visible", timeout=8000)
                resume.profession_container.click()
                resume.select2_search_input.press_sequentially("Авербандщик", delay=80)
                page.wait_for_timeout(600)
                resume.select2_first_option.click()

                resume.salary_input.fill("2000")
                resume.language_dropdown.select_option(label="Английский", force=True)
                resume.lang_level_dropdown.select_option(label="средний", force=True)

                # Поле пожеланий — туда кладём пейлоад
                wishes = page.locator("#id_wishes")
                if wishes.count() > 0:
                    wishes.fill(PAYLOAD)

                resume.submit_resume_button.click()
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                page.wait_for_timeout(1500)

            with allure.step("Шаг 2: Чтение сохранённого значения и проверка экранирования"):
                # Возвращаемся к списку и ищем созданные резюме
                goto_with_retry(page, list_url, wait_until="load")
                page.wait_for_load_state("load")
                edit_link = page.locator(
                    "a[href*='/registration/job-seeker/resume/'][href$='/update/']"
                ).first
                edit_link.wait_for(state="visible", timeout=8000)
                href = edit_link.get_attribute("href")
                match = re.search(r"/resume/(\d+)/", href) if href else None
                created_id = match.group(1) if match else None

                # Открываем форму редактирования и смотрим сохранённое значение
                goto_with_retry(page, f"{BASE_URL}/registration/job-seeker/resume/{created_id}/update/", wait_until="load")
                page.wait_for_load_state("load")
                wishes_val = page.locator("#id_wishes").first.input_value(timeout=8000)
                body = page.content()
                allure.attach(
                    f"Значение поля wishes: {wishes_val!r}\n"
                    f"Пейлоад без экранирования в HTML: {_contains_unescaped(body)}",
                    name="Результат stored XSS",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # Если значение вернулось как «чистый» пейлоад — это нормально для input_value
                # (это data-значение). Критично — чтобы в HTML-разметке он был экранирован.
                assert not _contains_unescaped(body), (
                    "Уязвимость (Stored XSS): сохранённый пейлоад отображается в HTML "
                    "без экранирования — будет выполнен у любого читателя."
                )
        finally:
            with allure.step("Посткондишн: удаление созданного резюме"):
                if created_id:
                    try:
                        from helpers.resume_helper import clear_resume_by_id
                        clear_resume_by_id(page, created_id)
                    except Exception as e:
                        allure.attach(str(e), name="Ошибка очистки", attachment_type=allure.attachment_type.TEXT)
