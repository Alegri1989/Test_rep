"""Фикстуры для пакета автотестов безопасности (tests/security).

Отличается от остальных пакетов тем, что предоставляет три контекста доступа:
  - guest_page      — анонимный браузер (без авторизации);
  - job_seeker_page — браузер, авторизованный как соискатель;
  - employer_page   — браузер, авторизованный как наниматель.

Авторизация выполняется один раз на сессию (сохраняется в storage_state),
а для каждого теста создаётся чистый контекст из сохранённого состояния —
по образцу корневых фикстур проекта.
"""
import os
import json
import logging
import logging.config
import allure
import pytest
from os import path
from playwright.sync_api import sync_playwright, Page

from pages.login_page import LoginPage
from helpers.network_helper import goto_with_retry

ROOT_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
lof_file_path = path.join(ROOT_DIR, "logging.ini")

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

BASE_URL = CONFIG["base_url"]
JS_AUTH_STATE = "auth_state_sec_js.json"
EMP_AUTH_STATE = "auth_state_sec_emp.json"


def _is_headless(pytestconfig) -> bool:
    try:
        return not pytestconfig.getoption("headed")
    except (ValueError, AttributeError):
        return True


def _slowmo(pytestconfig) -> int:
    try:
        v = pytestconfig.getoption("slowmo")
        return v if v else 0
    except (ValueError, AttributeError):
        return 0


@pytest.fixture(scope="session", autouse=True)
def run_global_auth():
    """Отключает глобальную авторизацию из корневых conftest для папки security."""
    pass


def _attach_network_logs_and_screenshot(request, page):
    """Общий разбор артефактов: сетевые логи + скриншот при падении."""
    if os.path.exists("log.txt"):
        try:
            with open("log.txt", "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            if log_content.strip():
                allure.attach(log_content, name="Сетевые логи", attachment_type=allure.attachment_type.TEXT)
        except Exception:
            pass
        open("log.txt", "w").close()

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        try:
            if not page.is_closed():
                allure.attach(
                    page.screenshot(full_page=True, timeout=5000),
                    name="Скриншот при падении",
                    attachment_type=allure.attachment_type.PNG,
                )
        except Exception:
            pass


def _attach_network_listeners(page):
    file_logger = logging.getLogger("file")
    page.on(
        "request",
        lambda req: file_logger.debug(f"СЕТЬ: ЗАПРОС -> {req.method} {req.url}")
        if req.url.startswith(BASE_URL) and req.resource_type in ["xhr", "fetch", "document"] else None,
    )
    page.on(
        "response",
        lambda res: file_logger.debug(f"СЕТЬ: ОТВЕТ <- [{res.status}] {res.url}")
        if res.url.startswith(BASE_URL) and res.request.resource_type in ["xhr", "fetch", "document"] else None,
    )


def _dismiss_cookie_panel(page):
    try:
        cookie_btn = page.locator("a.cookie-panel__info_button").first
        cookie_btn.wait_for(state="visible", timeout=3000)
        cookie_btn.click()
        page.wait_for_timeout(300)
    except Exception:
        pass


@pytest.fixture(scope="function")
def guest_page(pytestconfig, request) -> Page:
    """Анонимный браузер без авторизации."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=_is_headless(pytestconfig), args=["--lang=ru-RU"], channel="chrome")
        context = browser.new_context(locale="ru-RU", viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page.set_default_navigation_timeout(45000)
        page.set_default_timeout(15000)
        _attach_network_listeners(page)

        goto_with_retry(page, BASE_URL, wait_until="load")
        _dismiss_cookie_panel(page)

        request.node.funcargs["page_object"] = page
        yield page

        try:
            if not page.is_closed():
                page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass
        logging.shutdown()
        _attach_network_logs_and_screenshot(request, page)
        logging.config.fileConfig(lof_file_path)
        context.close()
        browser.close()


def _login_and_save_state(pytestconfig, email: str, password: str, state_path: str, landing_url: str):
    """Входит в систему и сохраняет storage_state в state_path."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=_is_headless(pytestconfig), args=["--lang=ru-RU"], channel="chrome")
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()
        login_page = LoginPage(page)
        login_page.login(email, password)
        page.wait_for_load_state("load")
        page.wait_for_timeout(500)
        goto_with_retry(page, landing_url, wait_until="load")
        context.storage_state(path=state_path)
        browser.close()


def _is_login_redirect(url: str) -> bool:
    """True, если URL — редирект на страницу входа (сессия потеряна)."""
    return "login_required" in url or "/user/login" in url


def _login_in_context(page, email: str, password: str):
    """Вход в текущем контексте. Повторяет последовательность LoginPage.login,
    но кука-кнопка необязательна (может быть уже принята/скрыта)."""
    lp = LoginPage(page)
    lp.navigate()
    # Кука: если видна — принимаем и ждём навигации (как в оригинале), иначе пропускаем
    cookie_accept = page.locator("a.cookie-panel__info_button")
    try:
        if cookie_accept.first.is_visible(timeout=2000):
            with page.expect_navigation(wait_until="load", timeout=10000):
                cookie_accept.first.click()
            lp.navigate()
    except Exception:
        pass
    lp.job_seeker_tab.wait_for(state="visible", timeout=10000)
    lp.job_seeker_tab.click()
    lp.login_tab.wait_for(state="visible", timeout=10000)
    lp.login_tab.click()
    lp.email_input.wait_for(state="visible", timeout=10000)
    lp.email_input.fill(email)
    lp.password_input.wait_for(state="visible", timeout=10000)
    lp.password_input.fill(password)
    lp.submit_button.click()
    # Дожидаемся установки сессионных cookies перед сохранением состояния
    page.wait_for_load_state("load", timeout=30000)
    page.wait_for_timeout(500)


def _ensure_authed(page, context, email: str, password: str, state_path: str, landing_url: str) -> bool:
    """Проверяет, что page авторизован; при редиректе на логин — выполняет вход
    в том же контексте и обновляет storage_state.
    Возвращает True, если сессия валидна."""
    if not _is_login_redirect(page.url):
        return True
    # Сессия потеряна — входим заново в текущем контексте (без вложенного sync_playwright)
    _login_in_context(page, email, password)
    page.wait_for_load_state("load")
    goto_with_retry(page, landing_url, wait_until="load")
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    if _is_login_redirect(page.url):
        return False
    context.storage_state(path=state_path)
    return True


@pytest.fixture(scope="session")
def _js_auth_state(pytestconfig):
    """Однократный вход соискателя на сессию (сохраняет auth_state_sec_js.json)."""
    user = CONFIG["user_email"]
    pwd = CONFIG["user_password"]
    landing = f"{BASE_URL}/registration/job-seeker/personal-info/"
    _login_and_save_state(pytestconfig, user, pwd, JS_AUTH_STATE, landing)
    yield
    if os.path.exists(JS_AUTH_STATE):
        os.remove(JS_AUTH_STATE)


@pytest.fixture(scope="session")
def _emp_auth_state(pytestconfig):
    """Однократный вход нанимателя на сессию (сохраняет auth_state_sec_emp.json)."""
    employer = CONFIG["employer"]
    landing = f"{BASE_URL}/registration/employer/business-entity-info/"
    _login_and_save_state(pytestconfig, employer["email"], employer["password"], EMP_AUTH_STATE, landing)
    yield
    if os.path.exists(EMP_AUTH_STATE):
        os.remove(EMP_AUTH_STATE)


@pytest.fixture(scope="function")
def job_seeker_page(pytestconfig, request, _js_auth_state) -> Page:
    """Чистая страница, авторизованная как соискатель."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=_is_headless(pytestconfig), args=["--lang=ru-RU"],
            slow_mo=_slowmo(pytestconfig), channel="chrome",
        )
        context = browser.new_context(storage_state=JS_AUTH_STATE, locale="ru-RU")
        page = context.new_page()
        _attach_network_listeners(page)
        landing = f"{BASE_URL}/registration/job-seeker/personal-info/"
        goto_with_retry(page, landing, wait_until="load")
        # networkidle может не наступить на медленном портале — не падаем, ждём только load
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        # Защита от потери сессии: если редирект на логин — один раз перезалогиниваемся
        if not _ensure_authed(page, context, CONFIG["user_email"], CONFIG["user_password"], JS_AUTH_STATE, landing):
            pytest.fail("Не удалось восстановить сессию соискателя после редиректа на логин")
        page.wait_for_timeout(1000)

        request.node.funcargs["page_object"] = page
        yield page

        try:
            if not page.is_closed():
                page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass
        logging.shutdown()
        _attach_network_logs_and_screenshot(request, page)
        logging.config.fileConfig(lof_file_path)
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def employer_page(pytestconfig, request, _emp_auth_state) -> Page:
    """Чистая страница, авторизованная как наниматель."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=_is_headless(pytestconfig), args=["--lang=ru-RU"],
            slow_mo=_slowmo(pytestconfig), channel="chrome",
        )
        context = browser.new_context(storage_state=EMP_AUTH_STATE, locale="ru-RU")
        page = context.new_page()
        _attach_network_listeners(page)
        landing = f"{BASE_URL}/registration/employer/business-entity-info/"
        goto_with_retry(page, landing, wait_until="load")
        # Защита от потери сессии: если редирект на логин — один раз перезалогиниваемся
        if not _ensure_authed(page, context, CONFIG["employer"]["email"], CONFIG["employer"]["password"], EMP_AUTH_STATE, landing):
            pytest.fail("Не удалось восстановить сессию нанимателя после редиректа на логин")
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        request.node.funcargs["page_object"] = page
        yield page

        try:
            if not page.is_closed():
                page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass
        logging.shutdown()
        _attach_network_logs_and_screenshot(request, page)
        logging.config.fileConfig(lof_file_path)
        context.close()
        browser.close()
