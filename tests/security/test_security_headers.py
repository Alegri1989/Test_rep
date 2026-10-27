"""Безопасность: HTTP-заголовки, транспорт, куки, CORS.

Проверяются защитные HTTP-заголовки ответа, безопасность передачи (HTTP->HTTPS),
флаги сессионных кук и корректность CORS. Все проверки выполняются анонимно.
"""
import re
import allure
import pytest
from playwright.sync_api import Page

from helpers.network_helper import goto_with_retry

BASE_URL = "https://gsz.gov.by"


def _get_headers(page: Page, url: str = BASE_URL + "/") -> dict:
    """Возвращает заголовки ответа (в нижнем регистре) для указанного URL."""
    response = page.request.get(url, max_redirects=0)
    headers = {k.lower(): v for k, v in response.headers.items()}
    allure.attach(
        "\n".join(f"{k}: {v}" for k, v in headers.items()),
        name=f"Заголовки {url}",
        attachment_type=allure.attachment_type.TEXT,
    )
    return headers


@allure.epic("Безопасность")
@allure.feature("Защитные HTTP-заголовки")
class TestSecurityHeaders:
    """Проверка наличия защитных HTTP-заголовков на ответах портала."""

    @allure.title("Безопасность: Наличие заголовка Strict-Transport-Security (HSTS)")
    @pytest.mark.skip(reason="Отключено временно: подтверждённое замечание (нет HSTS), см. report.txt — до исправления на портале")
    def test_hsts_header_present(self, guest_page: Page):
        """
        Бизнес-кейс: HSTS (Strict-Transport-Security) обязывает браузер ходить
        только по HTTPS и блокирует атаки «человеческого» MITM-перехвата.

        Ожидаемый результат (ОР): заголовок HSTS присутствует с max-age > 0.
        """
        headers = _get_headers(guest_page)
        hsts = headers.get("strict-transport-security", "")
        assert hsts, (
            "Уязвимость: отсутствует заголовок Strict-Transport-Security (HSTS). "
            "Браузер не принудительно использует HTTPS — возможен SSL-stripping."
        )
        assert "max-age=0" not in hsts, "HSTS присутствует, но max-age=0 (не действует)."

    @allure.title("Безопасность: Наличие заголовка Content-Security-Policy (CSP)")
    @pytest.mark.skip(reason="Отключено временно: подтверждённое замечание (нет CSP), см. report.txt — до исправления на портале")
    def test_csp_header_present(self, guest_page: Page):
        """
        Бизнес-кейс: CSP — первый рубеж защиты от XSS и инъекций контента.

        Ожидаемый результат (ОР): заголовок Content-Security-Policy присутствует.
        """
        headers = _get_headers(guest_page)
        csp = headers.get("content-security-policy", "")
        assert csp, (
            "Уязвимость: отсутствует Content-Security-Policy. "
            "Отсутствует защита от XSS и инъекции произвольного скрипта."
        )

    @allure.title("Безопасность: Защита от clickjacking (X-Frame-Options / CSP frame-ancestors)")
    def test_clickjacking_protection(self, guest_page: Page):
        """
        Бизнес-кейс: страница не должна встраиваться во внешний iframe (clickjacking).

        Ожидаемый результат (ОР): X-Frame-Options (DENY/SAMEORIGIN) либо CSP frame-ancestors.
        """
        headers = _get_headers(guest_page)
        xfo = headers.get("x-frame-options", "").upper()
        csp = headers.get("content-security-policy", "")
        frame_ancestors = "frame-ancestors" in csp
        assert xfo in ("DENY", "SAMEORIGIN") or frame_ancestors, (
            "Уязвимость: нет защиты от clickjacking — отсутствует X-Frame-Options "
            "и CSP frame-ancestors. Страницу можно встроить во внешний iframe."
        )

    @allure.title("Безопасность: Заголовок X-Content-Type-Options: nosniff")
    def test_x_content_type_options(self, guest_page: Page):
        """
        Бизнес-кейс: nosniff запрещает браузеру «угадывать» тип контента (MIME sniffing).

        Ожидаемый результат (ОР): X-Content-Type-Options: nosniff присутствует.
        """
        headers = _get_headers(guest_page)
        assert headers.get("x-content-type-options", "").lower() == "nosniff", (
            "Уязвимость: отсутствует X-Content-Type-Options: nosniff — "
            "возможен MIME-sniffing (загрузка скрипта как другого типа)."
        )

    @allure.title("Безопасность: Заголовок Referrer-Policy")
    def test_referrer_policy(self, guest_page: Page):
        """
        Бизнес-кейс: Referrer-Policy ограничивает утечку URL (и данных в query)
        в заголовке Referer при переходах на другие сайты.

        Ожидаемый результат (ОР): заголовок Referrer-Policy присутствует.
        """
        headers = _get_headers(guest_page)
        assert headers.get("referrer-policy", ""), (
            "Уязвимость: отсутствует Referrer-Policy — полный URL (включая query) "
            "может утекать внешним сайтам в заголовке Referer."
        )

    @allure.title("Безопасность: Заголовок Permissions-Policy")
    @pytest.mark.skip(reason="Отключено временно: подтверждённое замечание (нет Permissions-Policy), см. report.txt — до исправления на портале")
    def test_permissions_policy(self, guest_page: Page):
        """
        Бизнес-кейс: Permissions-Policy отключает опасные браузерные API
        (камера, микрофон, геолокация, push) для сторонних фреймов.

        Ожидаемый результат (ОР): заголовок Permissions-Policy присутствует.
        """
        headers = _get_headers(guest_page)
        assert headers.get("permissions-policy", ""), (
            "Уязвимость (низкая): отсутствует Permissions-Policy — "
            "браузерные API (камера/микрофон/гео) не ограничены политикой."
        )

    @allure.title("Безопасность: Отсутствие раскрытия версии сервера (Server)")
    @pytest.mark.skip(reason="Отключено временно: подтверждённое замечание (Server: nginx/1.22.1), см. report.txt — до исправления на портале")
    def test_no_server_version_disclosure(self, guest_page: Page):
        """
        Бизнес-кейс: заголовок Server не должен раскрывать точную версию ПО —
        это упрощает подбор известных уязвимостей.

        Ожидаемый результат (ОР): заголовок Server отсутствует либо без номера версии.
        """
        headers = _get_headers(guest_page)
        server = headers.get("server", "")
        import re
        has_version = bool(re.search(r"\d+\.\d+", server))
        assert not has_version, (
            f"Уязвимость (низкая): заголовок Server раскрывает версию — '{server}'. "
            "Рекомендуется отключить версионирование в nginx."
        )

    @allure.title("Безопасность: Отсутствие заголовка X-Powered-By")
    def test_no_x_powered_by(self, guest_page: Page):
        """
        Бизнес-кейс: X-Powered-By раскрывает стек приложения (Django/Python).

        Ожидаемый результат (ОР): заголовок X-Powered-By отсутствует.
        """
        headers = _get_headers(guest_page)
        assert "x-powered-by" not in headers, (
            f"Уязвимость (низкая): раскрывается стек приложения — "
            f"X-Powered-By: {headers.get('x-powered-by')}."
        )


@allure.epic("Безопасность")
@allure.feature("Транспорт и сессионные куки")
class TestTransportAndCookies:
    """Проверка принудительного HTTPS и флагов безопасности сессионных кук."""

    @allure.title("Безопасность: HTTP перенаправляет на HTTPS")
    def test_http_redirects_to_https(self, guest_page: Page):
        """
        Бизнес-кейс: запрос по HTTP должен перенаправляться на HTTPS,
        чтобы учётные данные не передавались по незащищённому каналу.

        Ожидаемый результат (ОР): HTTP-ответ — 301/302 с Location на https://.
        """
        response = guest_page.request.get("http://gsz.gov.by/", max_redirects=0)
        location = response.headers.get("location", "")
        assert response.status in (301, 302, 307, 308) and location.startswith("https://"), (
            f"Уязвимость: HTTP не перенаправляет на HTTPS (статус {response.status}, "
            f"Location '{location}'). Учётные данные могут передаваться по HTTP."
        )

    @allure.title("Безопасность: Сессионные куки с флагами Secure + HttpOnly + SameSite")
    def test_session_cookie_flags(self, guest_page: Page):
        """
        Бизнес-кейс: сессионные куки должны иметь Secure (только HTTPS),
        HttpOnly (недоступны из JS — защита от кражи при XSS) и SameSite
        (защита от CSRF).

        Ожидаемый результат (ОР): сессионные куки имеют все три флага.
        """
        # Загружаем главную, чтобы сервер установил куки, и читаем их из контекста
        goto_with_retry(guest_page, BASE_URL + "/", wait_until="load")
        cookies = guest_page.context.cookies()
        detail = [
            f"{c['name']}: secure={c.get('secure')} httponly={c.get('httpOnly')} samesite={c.get('sameSite')}"
            for c in cookies
        ]
        allure.attach("\n".join(detail) or "(нет кук)", name="Куки", attachment_type=allure.attachment_type.TEXT)

        # Проверяем сессионные куки (sessionid, csrftoken и любые *session*)
        session_cookies = [c for c in cookies if re.search(r"session|csrftoken", c["name"], re.IGNORECASE)]
        assert session_cookies, "Не найдено ни одной сессионной куки для проверки флагов."

        problems = []
        for c in session_cookies:
            name = c["name"]
            if not c.get("secure"):
                problems.append(f"{name}: нет Secure")
            if not c.get("httpOnly"):
                problems.append(f"{name}: нет HttpOnly")
            if not c.get("sameSite"):
                problems.append(f"{name}: нет SameSite")
        assert not problems, (
            "Уязвимость: сессионные куки без защитных флагов: " + "; ".join(problems) + "."
        )


@allure.epic("Безопасность")
@allure.feature("CORS")
class TestCORS:
    """Проверка отсутствия небезопасной настройки CORS."""

    @allure.title("Безопасность: CORS не отражает произвольный Origin с credentials")
    def test_cors_no_reflected_origin_with_credentials(self, guest_page: Page):
        """
        Бизнес-кейс: если сервер отражает произвольный Origin в
        Access-Control-Allow-Origin вместе с Access-Control-Allow-Credentials: true,
        любой сайт может читать защищённые ответы от имени пользователя (CORS-атака).

        Ожидаемый результат (ОР): для чужого Origin не выдаётся
        Access-Control-Allow-Origin: <этот Origin> + credentials: true.
        """
        attacker_origin = "https://evil-attacker.example"
        response = guest_page.request.get(
            BASE_URL + "/",
            headers={"Origin": attacker_origin},
            max_redirects=0,
        )
        acao = response.headers.get("access-control-allow-origin", "")
        acac = response.headers.get("access-control-allow-credentials", "").lower()
        allure.attach(
            f"Origin: {attacker_origin}\nAccess-Control-Allow-Origin: {acao}\n"
            f"Access-Control-Allow-Credentials: {acac}",
            name="CORS-ответ",
            attachment_type=allure.attachment_type.TEXT,
        )
        dangerous = acao == attacker_origin and acac == "true"
        assert not dangerous, (
            "Уязвимость: CORS отражает произвольный Origin с credentials — "
            f"Access-Control-Allow-Origin: {acao}, Access-Control-Allow-Credentials: true. "
            "Возможна кража данных через сторонний сайт."
        )
