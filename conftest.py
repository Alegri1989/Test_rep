import os
import json
import pytest
import allure
from playwright.sync_api import sync_playwright, Page

# Путь к файлу для сохранения состояния авторизации (куки, сессии)
AUTH_STATE_PATH = "auth_state.json"

# Загружаем настройки (URL, логин, пароль) из конфигурационного файла JSON
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


def block_ads_route(route):
    """Перехватывает сетевые запросы сайта и блокирует рекламные скрипты Google.
    """
    url = route.request.url.lower()
    if "googleads" in url or "googlesyndication" in url:
        if route.request.resource_type == "script":
            return route.abort()  # Полностью отменяем загрузку рекламы
    return route.continue_()  # Разрешаем загрузку остальных полезных файлов сайта


@pytest.fixture(scope="session", autouse=True)
def run_global_auth(pytestconfig):
    """Глобальная фикстура для автоматической авторизации в начале тестовой сессии.

    Один раз логинится на сайте, сохраняет куки в файл auth_state.json и закрывается.
    После завершения всех тестов удаляет созданный файл авторизации.
    """
    # Определяем режим запуска браузера: с окном (--headed) или в фоне (headless)
    is_headless = not pytestconfig.getoption("headed")

    with sync_playwright() as p:
        # Запускаем браузер Chromium с английской локалью без автопереводчика страниц
        browser = p.chromium.launch(
            headless=is_headless,
            args=["--disable-features=Translate", "--lang=en-US"]
        )
        context = browser.new_context(locale="en-US")
        context.route("**/*", block_ads_route)  # Включаем блокировщик рекламы
        page = context.new_page()

        # Переходим на страницу логина, используя адрес из config.json
        page.goto(f"{CONFIG['base_url']}/login", wait_until="domcontentloaded")
        page.locator(".login-form").wait_for(state="visible")

        # Заполняем форму авторизации данными из конфига и нажимаем кнопку войти
        page.locator(".login-form input[type='email']").fill(CONFIG['user_email'])
        page.locator(".login-form input[type='password']").fill(CONFIG['user_password'])
        page.locator(".login-form button[type='submit']").click()

        # Ждем подтверждения успешного входа на сайт
        page.wait_for_selector("text=Logged in as")

        # Сохраняем сессию (токены и куки) в файл, чтобы не логиниться в каждом тесте заново
        context.storage_state(path=AUTH_STATE_PATH)
        browser.close()

    yield  # Здесь выполняются все наши тесты проекта

    # Блок финализации: удаляем файл авторизации после окончания всех тестов сессии
    if os.path.exists(AUTH_STATE_PATH):
        os.remove(AUTH_STATE_PATH)


@pytest.fixture(scope="function")
def auth_page(pytestconfig, request):
    """Функциональная фикстура, которая создает чистую страницу браузера для каждого теста.

    Автоматически подкидывает сохраненный файл авторизации и включает запись видео.
    """
    is_headless = not pytestconfig.getoption("headed")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=["--disable-features=Translate", "--lang=en-US"]
        )
        # Создаем контекст с уже готовой авторизацией и настройкой записи видео
        context = browser.new_context(
            storage_state=AUTH_STATE_PATH,
            record_video_dir="videos/",
            locale="en-US"
        )
        context.route("**/*", block_ads_route)
        page = context.new_page()

        # Передаем объект страницы в переменные pytest (request),
        # чтобы хук создания скриншотов имел доступ к экрану браузера в случае падения
        request.node.funcargs['page_object'] = page

        yield page  # Передаем готовую страницу внутрь тестовой функции

        # Закрываем страницу и браузер после завершения отдельного теста
        context.close()
        browser.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Хук Pytest, который следит за статусом выполнения каждого шага теста.

    Если тест падает, хук берет активный объект страницы из фикстуры, делает
    полноэкранный скриншот в байтах и прикрепляет его к отчету Allure.
    """
    outcome = yield
    report = outcome.get_result()

    # Проверяем, что шаг теста завершился ошибкой (failed) непосредственно во время выполнения
    if report.when == "call" and report.failed:
        # Проверяем, успела ли фикстура передать страницу браузера
        if 'page_object' in item.funcargs:
            page: Page = item.funcargs['page_object']
            # Делаем снимок всей страницы сайта
            screenshot = page.screenshot(full_page=True)
            # Прикрепляем полученный скриншот к отчету Allure
            allure.attach(
                screenshot,
                name="Screenshot on Failure",
                attachment_type=allure.attachment_type.PNG
            )