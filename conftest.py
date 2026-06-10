import os
import json
import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage

# Путь к файлу для сохранения состояния авторизации (куки, сессии)
AUTH_STATE_PATH = "auth_state.json"

# Загружаем настройки (URL, логин, пароль) из конфигурационного файла JSON
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


def pytest_addoption(parser):
    """Регистрируем флаги проекта, чтобы pytest не ругался на их отсутствие."""
    parser.addoption(
        "--headed", action="store_true", default=False, help="Запуск браузера в видимом режиме"
    )
    parser.addoption(
        "--slowmo", action="store", default=0, type=int, help="Замедление действий в мс (например, 1000)"
    )


@pytest.fixture(scope="session", autouse=True)
def run_global_auth(pytestconfig):
    """Глобальная фикстура для автоматической авторизации в начале тестовой сессии."""
    is_headless = not pytestconfig.getoption("headed")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"])
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.login(CONFIG['user_email'], CONFIG['user_password'])

        # ЖДЕМ ГАРАНТИРОВАННОГО ВХОДА: собираем полное имя из конфига для проверки
        fio = CONFIG["default_profile"]
        full_name = f"{fio['last_name']} {fio['first_name']} {fio['middle_name']}".upper()

        # Ожидаем появление элемента с ФИО в верхнем углу (таймаут 10 секунд)
        page.get_by_text(full_name).wait_for(state="visible", timeout=10000)

        # Даем сайту еще 500 мс на окончательное сохранение кук после рендеринга
        page.wait_for_timeout(500)

        # Сохраняем готовую сессию
        context.storage_state(path=AUTH_STATE_PATH)
        browser.close()

    yield

    if os.path.exists(AUTH_STATE_PATH):
        os.remove(AUTH_STATE_PATH)


@pytest.fixture(scope="function")
def auth_page(pytestconfig, request):
    """Функциональная фикстура, которая создает чистую страницу с уже готовой авторизацией."""
    is_headless = not pytestconfig.getoption("headed")
    # Считываем значение из терминала (по умолчанию 0)
    slow_mo_val = pytestconfig.getoption("slowmo")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=["--lang=ru-RU"],
            slow_mo=slow_mo_val  # Подставляем считанное значение
        )

        context = browser.new_context(
            storage_state=AUTH_STATE_PATH,
            record_video_dir="videos/",
            locale="ru-RU"
        )
        page = context.new_page()

        request.node.funcargs['page_object'] = page

        yield page

        context.close()
        browser.close()


@pytest.fixture(scope="session")
def app_config():
    """Фикстура предоставляет доступ к настройкам из config.json без прямых импортов."""
    return CONFIG


def pytest_generate_tests(metafunc):
    """Динамическая параметризация тестов данными из config.json без прямых импортов."""
    if "test_status" in metafunc.fixturenames:
        metafunc.parametrize("test_status", CONFIG["profile_test_data"]["statuses"])

    if "test_education" in metafunc.fixturenames:
        metafunc.parametrize("test_education", CONFIG["profile_test_data"]["educations"])