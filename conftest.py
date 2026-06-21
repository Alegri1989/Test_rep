import os
import json
import logging.config
from os import path
import pytest
import allure
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage

# Настройка конфигурации логов на старте
lof_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.ini')
logging.config.fileConfig(lof_file_path)

AUTH_STATE_PATH = "auth_state.json"

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук для отслеживания статуса выполнения теста."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.rep_call = rep


# 🎯 Флаги --headed и --slowmo НЕ регистрируем тут специально!
# Их уже регистрирует плагин pytest-playwright (он есть в зависимостях проекта),
# поэтому свой pytest_addoption для этих имён добавлять нельзя — будет
# "ArgumentError: conflicting option string" при старте pytest.
# pytestconfig.getoption("headed") / ("slowmo") работают и без этого блока.


@pytest.fixture(scope="session", autouse=True)
def run_global_auth(pytestconfig):
    """Глобальная фикстура для автоматической авторизации."""
    is_headless = not pytestconfig.getoption("headed")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"])
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
def auth_page(pytestconfig, request):
    """Создает чистую страницу браузера и крепит артефакты в Allure."""
    is_headless = not pytestconfig.getoption("headed")

    # 🎯 Если в консоли слоумо не указан (равен 0), ставим базовые 400 мс для стабильности сьюта
    slow_mo_val = pytestconfig.getoption("slowmo")
    if slow_mo_val == 0:
        slow_mo_val = 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], slow_mo=slow_mo_val)
        context = browser.new_context(storage_state=AUTH_STATE_PATH, record_video_dir="videos/", locale="ru-RU")
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

        page.goto("https://gsz.gov.by/registration/job-seeker/personal-info/")
        page.wait_for_load_state("networkidle")

        request.node.funcargs['page_object'] = page

        yield page

        # Закрываем логи и освобождаем файл
        logging.shutdown()

        # Прикрепляем готовый log.txt в Allure
        if os.path.exists("log.txt"):
            try:
                if not page.is_closed():
                    page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass

                # Закрываем логи и освобождаем файл
            logging.shutdown()

        # Переинициализируем логгер обратно для следующих тестов сессии
        logging.config.fileConfig(lof_file_path)

        # Автоматический скриншот при падении теста
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
