import os
import sys
import json
import logging.config
from pathlib import Path
import pytest
import allure
from playwright.sync_api import sync_playwright, Page

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from pages.login_page import LoginPage
from helpers.network_helper import goto_with_retry

# Настройка конфигурации логов на старте
lof_file_path = _ROOT / 'logging.ini'
logging.config.fileConfig(lof_file_path)

AUTH_STATE_PATH = str(_ROOT / "auth_state.json")

with open(_ROOT / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук для отслеживания статуса выполнения теста."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.rep_call = rep


def pytest_addoption(parser):
    pass


@pytest.fixture(scope="session", autouse=True)
def run_global_auth(pytestconfig):
    """Глобальная фикстура для автоматической авторизации."""
    # 🛡️ Безопасное чтение флага headed
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], channel="chrome")
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.login(CONFIG['user_email'], CONFIG['user_password'])

        fio = CONFIG["default_profile"]
        full_name = f"{fio['last_name']} {fio['first_name']} {fio['middle_name']}".upper()

        page.get_by_text(full_name).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(500)

        context.storage_state(path=AUTH_STATE_PATH)
        browser.close()

    yield

    if os.path.exists(AUTH_STATE_PATH):
        os.remove(AUTH_STATE_PATH)


@pytest.fixture(scope="function")
def open_create_resume_page(auth_page) -> Page:
    """Фикстура открывает страницу создания резюме с выполненной авторизацией"""
    resume_url = "https://gsz.gov.by/registration/job-seeker/resume/create/"
    goto_with_retry(auth_page, resume_url, wait_until="load")
    auth_page.wait_for_selector("#id_desired_profession", state="visible", timeout=30000)
    auth_page.wait_for_load_state("networkidle")
    return auth_page

@pytest.fixture(scope="function")
def open_vacancy_search_page(auth_page) -> Page:
    """Фикстура открывает страницу поиска вакансий с выполненной авторизацией"""
    vacancy_url = "https://gsz.gov.by/registration/vacancy-search/"
    goto_with_retry(auth_page, vacancy_url, wait_until="load")
    auth_page.wait_for_selector("#id_profession", state="visible", timeout=30000)
    auth_page.wait_for_load_state("networkidle")
    return auth_page

@pytest.fixture(scope="function")
def auth_page(pytestconfig, request):
    """Создает чистую страницу браузера и крепит артефакты в Allure."""
    # 🛡️ Безопасное чтение флага headed
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    # 🎯 Безопасное чтение флага slowmo
    slow_mo_val = 400
    try:
        if pytestconfig.getoption("slowmo") != 0:
            slow_mo_val = pytestconfig.getoption("slowmo")
    except ValueError:
        pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], slow_mo=slow_mo_val, channel="chrome")
        context = browser.new_context(storage_state=AUTH_STATE_PATH, locale="ru-RU")  # record_video_dir="videos/"
        page = context.new_page()

        file_logger = logging.getLogger("file")

        page.on(
            "request",
            lambda req: file_logger.debug(f"СЕТЬ: ЗАПРОС -> {req.method} {req.url}")
            if req.url.startswith("https://gsz.gov.by") and req.resource_type in ["xhr", "fetch", "document"] else None
        )
        page.on(
            "response",
            lambda res: file_logger.debug(f"СЕТЬ: ОТВЕТ <- [{res.status}] {res.url}")
            if res.url.startswith("https://gsz.gov.by") and res.request.resource_type in ["xhr", "fetch",
                                                                                          "document"] else None
        )

        goto_with_retry(page, "https://gsz.gov.by/registration/job-seeker/personal-info/", wait_until="load")
        page.wait_for_load_state("networkidle")

        request.node.funcargs['page_object'] = page

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
                        attachment_type=allure.attachment_type.PNG
                    )
            except Exception:
                pass

        context.close()
        browser.close()


@pytest.fixture(scope="session")
def app_config():
    return CONFIG


def pytest_generate_tests(metafunc):
    if "test_status" in metafunc.fixturenames:
        metafunc.parametrize("test_status", CONFIG["profile_test_data"]["statuses"])

    if "test_education" in metafunc.fixturenames:
        metafunc.parametrize("test_education", CONFIG["profile_test_data"]["educations"])

    if "test_sorting" in metafunc.fixturenames:
        metafunc.parametrize("test_sorting", CONFIG["profile_test_data"]["sorting_options"])
