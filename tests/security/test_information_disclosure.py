"""Раскрытие информации: служебные файлы, directory traversal, open redirect,
глагольные ошибки. Все проверки анонимные и неразрушающие.
"""
import re
import allure
import pytest
from playwright.sync_api import Page

BASE_URL = "https://gsz.gov.by"


def _status(page: Page, url: str) -> int:
    try:
        return page.request.get(url, max_redirects=0).status
    except Exception as e:
        return -1


@allure.epic("Безопасность")
@allure.feature("Раскрытие служебных файлов")
class TestSensitiveFiles:
    """Проверка, что служебные/служебные файлы недоступны анониму."""

    @pytest.mark.parametrize("path", [
        "/.git/config",
        "/.git/HEAD",
        "/.env",
        "/.env.local",
        "/config.json.bak",
        "/config.json~",
        "/.DS_Store",
        "/web.config",
        "/wp-config.php.bak",
        "/.htaccess",
        "/backup.sql",
        "/dump.sql",
        "/database.yml",
        "/.svn/entries",
    ], ids=lambda p: p.strip("/"))
    @allure.title("Безопасность: Служебный файл недоступен")
    def test_sensitive_file_not_accessible(self, guest_page: Page, path: str):
        """
        Бизнес-кейс: файлы конфигурации, резервные копии и служебные файлы
        VCS не должны отдаваться по HTTP — это утечка секретов и кода.

        Ожидаемый результат (ОР): ответ 403/404 (не 200/301).
        """
        url = f"{BASE_URL}{path}"
        status = _status(guest_page, url)
        allure.attach(f"{url} -> {status}", name="Статус", attachment_type=allure.attachment_type.TEXT)
        assert status in (403, 404), (
            f"Уязвимость: служебный файл доступен по HTTP — {url} вернул {status}. "
            "Возможна утечка конфигурации/секретов/кода."
        )


@allure.epic("Безопасность")
@allure.feature("Directory traversal")
class TestDirectoryTraversal:
    """Проверка защиты от выхода за пределы корня приложения."""

    @pytest.mark.parametrize("path", [
        "/../../etc/passwd",
        "/registration/../../etc/passwd",
        "/static/../../../../etc/passwd",
        "/%2e%2e/%2e%2e/etc/passwd",
        "/..%2f..%2f..%2fetc/passwd",
    ], ids=lambda p: p)
    @allure.title("Безопасность: Directory traversal заблокирован")
    def test_directory_traversal_blocked(self, guest_page: Page, path: str):
        """
        Бизнес-кейс: попытка выхода за корень приложения (.., URL-кодирование)
        не должна давать доступ к системным файлам.

        Ожидаемый результат (ОР): ответ 400/403/404, и в теле нет содержимого /etc/passwd.
        """
        url = f"{BASE_URL}{path}"
        try:
            resp = guest_page.request.get(url, max_redirects=0)
            status = resp.status
            body = resp.text() if status == 200 else ""
        except Exception:
            status = -1
            body = ""
        allure.attach(f"{url} -> {status}", name="Статус", attachment_type=allure.attachment_type.TEXT)
        leaked = "root:" in body and "passwd" in body
        assert status in (400, 403, 404) and not leaked, (
            f"Уязвимость (Directory traversal): {url} вернул {status}, "
            f"утечка /etc/passwd: {leaked}. Возможно чтение файлов за пределами корня."
        )


@allure.epic("Безопасность")
@allure.feature("Open redirect")
class TestOpenRedirect:
    """Проверка отсутствия open redirect через параметры перенаправления."""

    @allure.title("Безопасность: Нет open redirect через параметры ?next / ?url / ?redirect")
    def test_no_open_redirect(self, guest_page: Page):
        """
        Бизнес-кейс: параметры перенаправления (next, url, redirect, target)
        не должны позволять уводить пользователя на внешний злонамеренный сайт
        (фишинг).

        Ожидаемый результат (ОР): редирект на внешний домен не выполняется.
        """
        evil = "https://evil-attacker.example/phish"
        candidates = [
            f"{BASE_URL}/?next={evil}",
            f"{BASE_URL}/?url={evil}",
            f"{BASE_URL}/?redirect={evil}",
            f"{BASE_URL}/?target={evil}",
            f"{BASE_URL}/user/login/?next={evil}",
            f"{BASE_URL}/user/login/?redirect={evil}",
            f"{BASE_URL}/logout/?next={evil}",
        ]
        redirected = []
        for url in candidates:
            try:
                resp = guest_page.request.get(url, max_redirects=0)
                location = resp.headers.get("location", "")
                if location.startswith("http") and "evil-attacker" in location:
                    redirected.append(f"{url} -> {location}")
            except Exception:
                pass

        allure.attach("\n".join(redirected) or "Не найдено", name="Open redirect",
                      attachment_type=allure.attachment_type.TEXT)
        assert not redirected, (
            "Уязвимость (Open redirect): портал перенаправляет на внешний домен: "
            + "; ".join(redirected) + ". Используется для фишинга."
        )


@allure.epic("Безопасность")
@allure.feature("Глагольные ошибки")
class TestVerboseErrors:
    """Проверка, что страницы ошибок не раскрывают стек/информацию о приложении."""

    @allure.title("Безопасность: Страница 404 не раскрывает стек приложения")
    def test_404_no_stack_trace(self, guest_page: Page):
        """
        Бизнес-кейс: страница «не найдено» не должна содержать traceback,
        пути к файлам, версии фреймворка или SQL — это раскрывает архитектуру.

        Ожидаемый результат (ОР): в теле 404 нет признаков отладочной информации.
        """
        url = f"{BASE_URL}/definitely-not-exists-8f3a9c/"
        resp = guest_page.request.get(url, max_redirects=0)
        body = resp.text() if resp.status in (404, 500) else ""
        allure.attach(f"Статус: {resp.status}", name="Статус", attachment_type=allure.attachment_type.TEXT)

        sensitive_patterns = [
            r"Traceback \(most recent call last\)",
            r"django\.core\.handlers",
            r"File \"/[^\"]+\.py\", line \d+",
            r"SQLSyntaxError|OperationalError|IntegrityError",
            r"INTERNAL SERVER ERROR",
            r"Apache|nginx/\d",
        ]
        leaked = [p for p in sensitive_patterns if re.search(p, body, re.IGNORECASE)]
        assert resp.status == 404 and not leaked, (
            f"Уязвимость (раскрытие информации): страница 404 раскрывает отладочные "
            f"данные: {leaked}. Статус: {resp.status}."
        )

    @allure.title("Безопасность: Неверный метод не раскрывает стек")
    def test_bad_request_no_stack(self, guest_page: Page):
        """
        Бизнес-кейс: запрос с некорректным телом/методом не должен отдавать
        отладочный traceback.

        Ожидаемый результат (ОР): в ответе нет Traceback.
        """
        resp = guest_page.request.post(
            f"{BASE_URL}/definitely-not-exists-8f3a9c/",
            data={"x": "<script>alert(1)</script>"},
            max_redirects=0,
        )
        body = resp.text() if resp.status >= 400 else ""
        leaked = bool(re.search(r"Traceback \(most recent call last\)|File \"/[^\"]+\.py\", line \d+", body))
        allure.attach(f"Статус: {resp.status}, traceback: {leaked}", name="Результат",
                      attachment_type=allure.attachment_type.TEXT)
        assert not leaked, (
            "Уязвимость (раскрытие информации): на ошибку возвращён отладочный "
            "traceback с путями к файлам приложения."
        )
