"""CSRF: наличие токена в формах и отклонение кросс-доменных POST без токена."""
import re
import allure
import pytest
from playwright.sync_api import Page

from helpers.network_helper import goto_with_retry

BASE_URL = "https://gsz.gov.by"


def _page_has_csrf_token(page: Page) -> bool:
    return page.locator("input[name='csrfmiddlewaretoken']").count() > 0


@allure.epic("Безопасность")
@allure.feature("CSRF")
class TestCSRF:
    """Проверка защиты от межсайтовой подделки запросов."""

    @allure.title("Безопасность: Формы содержат CSRF-токен")
    def test_forms_contain_csrf_token(self, job_seeker_page: Page):
        """
        Бизнес-кейс: каждая изменяющая форма (POST) должна содержать скрытый
        CSRF-токен — иначе сторонний сайт может отправить запрос от имени пользователя.

        Ожидаемый результат (ОР): на странице профиля есть input[name='csrfmiddlewaretoken'].
        """
        profile_url = f"{BASE_URL}/registration/job-seeker/personal-info/"
        goto_with_retry(job_seeker_page, profile_url, wait_until="load")
        # Усиление: ждём загрузки страницы с retry
        for _ in range(3):
            try:
                job_seeker_page.wait_for_load_state("networkidle", timeout=10000)
                break
            except Exception:
                job_seeker_page.wait_for_timeout(1000)
                continue

        # Усиление: проверяем, что мы на правильной странице (не на логине)
        assert "login" not in job_seeker_page.url, (
            f"Ошибка: редирект на логин вместо страницы профиля: {job_seeker_page.url}"
        )

        # Усиление: ждём появления CSRF-токена с retry
        has_token = False
        for _ in range(3):
            has_token = _page_has_csrf_token(job_seeker_page)
            if has_token:
                break
            job_seeker_page.wait_for_timeout(1000)
            job_seeker_page.reload(wait_until="load")

        allure.attach(f"CSRF-токен на странице профиля: {has_token}", name="CSRF token",
                      attachment_type=allure.attachment_type.TEXT)
        assert has_token, (
            "Уязвимость (CSRF): на защищённой странице с формой отсутствует "
            "CSRF-токен (csrfmiddlewaretoken). Возможна межсайтовая подделка запросов."
        )

    @allure.title("Безопасность: POST без CSRF-токена отклонён (403)")
    def test_post_without_csrf_token_rejected(self, job_seeker_page: Page):
        """
        Бизнес-кейс: прямой POST на изменяющий эндпоинт без CSRF-токена
        (как делает сторонний сайт) должен быть отклонён сервером (403).

        Ожидаемый результат (ОР): ответ 403 Forbidden.
        """
        # Эндпоинт обновления профиля соискателя (изменяющий)
        update_url = f"{BASE_URL}/registration/job-seeker/personal-info/"
        response = job_seeker_page.request.post(
            update_url,
            data={"last_name": "Hacker"},
            headers={
                "Origin": "https://evil-attacker.example",
                "Referer": "https://evil-attacker.example/",
                "X-Requested-With": "XMLHttpRequest",
            },
            max_redirects=0,
        )
        allure.attach(f"Статус POST без CSRF-токена: {response.status}", name="Статус",
                      attachment_type=allure.attachment_type.TEXT)
        assert response.status == 403, (
            f"Уязвимость (CSRF): POST без CSRF-токена вернул {response.status} "
            "вместо 403. Запрос мог быть принят — возможна подделка от имени пользователя."
        )

    @allure.title("Безопасность: Кросс-доменный POST на смену пароля отклонён")
    def test_cross_origin_password_change_rejected(self, job_seeker_page: Page):
        """
        Бизнес-кейс: смена пароля — критичное действие. Кросс-доменный POST
        без валидного CSRF-токена должен быть отклонён.

        Ожидаемый результат (ОР): ответ 403 (или редирект, но не 200 с изменением).
        """
        # Частый путь сменy пароля в Django-приложениях
        candidates = [
            f"{BASE_URL}/user/password/",
            f"{BASE_URL}/user/password/change/",
            f"{BASE_URL}/registration/job-seeker/change-password/",
        ]
        any_200 = False
        details = []
        for url in candidates:
            try:
                resp = job_seeker_page.request.post(
                    url,
                    data={"new_password": "Hacked123!", "new_password2": "Hacked123!"},
                    headers={
                        "Origin": "https://evil-attacker.example",
                        "Referer": "https://evil-attacker.example/",
                    },
                    max_redirects=0,
                )
                details.append(f"{url} -> {resp.status}")
                if resp.status == 200:
                    any_200 = True
            except Exception as e:
                details.append(f"{url} -> error: {e}")

        allure.attach("\n".join(details), name="Ответы на смену пароля",
                      attachment_type=allure.attachment_type.TEXT)
        assert not any_200, (
            "Уязвимость (CSRF): кросс-доменный POST на смену пароля вернул 200 — "
            "пароль мог быть изменён без участия пользователя. " + "; ".join(details)
        )
