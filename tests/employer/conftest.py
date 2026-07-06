import os
import json
import logging
import logging.config
import allure
import pytest
from os import path
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from helpers.network_helper import goto_with_retry

EMPLOYER_AUTH_STATE = "auth_state_employer.json"
EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"


@pytest.fixture(scope="session", autouse=True)
def run_global_auth():
    """Отключает авторизацию соискателя для тестов нанимателя — по аналогии с without_auth."""
    pass

ROOT_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
lof_file_path = path.join(ROOT_DIR, "logging.ini")

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


@pytest.fixture(scope="session")
def run_employer_auth(pytestconfig):
    """Авторизует нанимателя и сохраняет auth_state_employer.json."""
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    employer = CONFIG["employer"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], channel="chrome")
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.login(employer["email"], employer["password"])

        page.wait_for_load_state("load")
        page.wait_for_timeout(1000)

        goto_with_retry(page, EMPLOYER_INFO_URL, wait_until="load")

        context.storage_state(path=EMPLOYER_AUTH_STATE)
        browser.close()

    yield

    if os.path.exists(EMPLOYER_AUTH_STATE):
        os.remove(EMPLOYER_AUTH_STATE)


@pytest.fixture(scope="function")
def auth_employer_page(pytestconfig, request, run_employer_auth):
    """Создаёт чистую страницу с авторизацией нанимателя, открытую на странице сведений."""
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    slow_mo_val = 400
    try:
        if pytestconfig.getoption("slowmo") != 0:
            slow_mo_val = pytestconfig.getoption("slowmo")
    except ValueError:
        pass

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=["--lang=ru-RU"],
            slow_mo=slow_mo_val,
            channel="chrome",
        )
        context = browser.new_context(
            storage_state=EMPLOYER_AUTH_STATE,
            # record_video_dir="videos/",
            locale="ru-RU",
        )
        page = context.new_page()

        file_logger = logging.getLogger("file")
        page.on(
            "request",
            lambda req: file_logger.debug(f"СЕТЬ: ЗАПРОС -> {req.method} {req.url}")
            if req.url.startswith("https://gsz.gov.by")
            and req.resource_type in ["xhr", "fetch", "document"]
            else None,
        )
        page.on(
            "response",
            lambda res: file_logger.debug(f"СЕТЬ: ОТВЕТ <- [{res.status}] {res.url}")
            if res.url.startswith("https://gsz.gov.by")
            and res.request.resource_type in ["xhr", "fetch", "document"]
            else None,
        )

        goto_with_retry(page, EMPLOYER_INFO_URL, wait_until="load")

        request.node.funcargs["page_object"] = page

        yield page

        try:
            if not page.is_closed():
                page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

        logging.shutdown()

        if os.path.exists("log.txt"):
            try:
                with open("log.txt", "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
                if log_content.strip():
                    allure.attach(log_content, name="Сетевые логи", attachment_type=allure.attachment_type.TEXT)
            except Exception:
                pass
            open("log.txt", "w").close()

        logging.config.fileConfig(lof_file_path)

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

        context.close()
        browser.close()
