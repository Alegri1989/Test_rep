import os
import json
import queue
import logging
import threading
import allure
import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from helpers.network_helper import goto_with_retry

_EMPLOYER_AUTH_FILE = "auth_state_employer_responses.json"
_EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"

with open("config.json", "r", encoding="utf-8") as f:
    _CONFIG = json.load(f)


@pytest.fixture(scope="session")
def _run_employer_auth_responses(pytestconfig):
    """Авторизует нанимателя и сохраняет auth state для тестов откликов."""
    try:
        is_headless = not pytestconfig.getoption("headed")
    except ValueError:
        is_headless = True

    employer = _CONFIG["employer"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=["--lang=ru-RU"], channel="chrome")
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()
        LoginPage(page).login(employer["email"], employer["password"])
        page.wait_for_load_state("load")
        page.wait_for_timeout(1000)
        goto_with_retry(page, _EMPLOYER_INFO_URL, wait_until="load")
        context.storage_state(path=_EMPLOYER_AUTH_FILE)
        browser.close()

    yield

    if os.path.exists(_EMPLOYER_AUTH_FILE):
        os.remove(_EMPLOYER_AUTH_FILE)


@pytest.fixture(scope="function")
def call_in_employer_browser(pytestconfig, request, _run_employer_auth_responses):
    """
    Фикстура-диспетчер: запускает браузер нанимателя в отдельном потоке
    и возвращает callable, через который тест передаёт функции для
    выполнения внутри этого потока.

    Playwright Page привязан к гринлету своего потока и не может
    использоваться из другого потока. Паттерн с очередью решает это:
    Page никогда не покидает поток, а тест посылает ему lambda-функции.
    """
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

    work_q: queue.Queue = queue.Queue()
    result_q: queue.Queue = queue.Queue()
    init_errors = []
    ready = threading.Event()

    def _thread():
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=is_headless,
                    args=["--lang=ru-RU"],
                    slow_mo=slow_mo_val,
                    channel="chrome",
                )
                context = browser.new_context(
                    storage_state=_EMPLOYER_AUTH_FILE,
                    # record_video_dir="videos/",
                    locale="ru-RU",
                )
                page = context.new_page()
                goto_with_retry(page, _EMPLOYER_INFO_URL, wait_until="load")
                ready.set()

                while True:
                    fn = work_q.get()
                    if fn is None:
                        break
                    try:
                        result_q.put(("ok", fn(page)))
                    except Exception as exc:
                        result_q.put(("err", exc))

                if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
                    try:
                        if not page.is_closed():
                            allure.attach(
                                page.screenshot(full_page=True, timeout=5000),
                                name="Скриншот нанимателя при падении",
                                attachment_type=allure.attachment_type.PNG,
                            )
                    except Exception:
                        pass

                context.close()
                browser.close()
        except Exception as exc:
            init_errors.append(exc)
            ready.set()

    thread = threading.Thread(target=_thread, daemon=True)
    thread.start()
    ready.wait(timeout=60)

    if init_errors:
        raise init_errors[0]

    def call(fn, timeout=60):
        """Выполняет fn(page) в потоке браузера нанимателя, возвращает результат."""
        work_q.put(fn)
        status, value = result_q.get(timeout=timeout)
        if status == "err":
            raise value
        return value

    yield call

    work_q.put(None)
    thread.join(timeout=30)
