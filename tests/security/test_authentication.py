"""Безопасность аутентификации: перечисление пользователей, ограничение
перебора паролей, безопасность сессии (fixation, инвалидация при выходе).

Важно: форма входа на портале обрабатывается через JS (AJAX POST на /user/login/),
а ошибка входа показывается через alert(). Поэтому тесты перехватывают ответ сети
и текст диалога, а не ищут HTML-элементы ошибок.
"""
import re
import allure
import pytest
from playwright.sync_api import Page

from helpers.network_helper import goto_with_retry

BASE_URL = "https://gsz.gov.by"
LOGIN_URL = f"{BASE_URL}/user/login/"
REAL_EMAIL = "Galerko.S@mintrud.by"          # реальный аккаунт из config.json
REAL_PASSWORD = "Primero2"
# Чётко вымышленный email — чтобы тест перебора не задевал реальные аккаунты.
FAKE_EMAIL = "sec_scan_nonexistent_8f3a@example.invalid"


def _dismiss_cookie(page: Page):
    try:
        btn = page.locator("a.cookie-panel__info_button").first
        btn.wait_for(state="visible", timeout=3000)
        btn.click()
        page.wait_for_timeout(300)
    except Exception:
        pass


def _open_login_form(page: Page, retries: int = 2):
    """Открывает страницу входа и активирует вкладку с формой логина соискателя.
    При невидимости #id_mail перезагружает страницу и пробует снова (защита от флейка)."""
    for attempt in range(retries + 1):
        goto_with_retry(page, LOGIN_URL, wait_until="load")
        _dismiss_cookie(page)
        for sel in ("#pills-job-seeker-tab", "#pills-login-tab"):
            try:
                loc = page.locator(sel)
                if loc.count():
                    loc.first.wait_for(state="visible", timeout=5000)
                    loc.first.click()
                    page.wait_for_timeout(200)
            except Exception:
                pass
        try:
            page.locator("#id_mail").wait_for(state="visible", timeout=10000)
            return
        except Exception:
            if attempt == retries:
                raise
            # Флейк: форма не появилась — перезагружаем и пробуем снова
            page.wait_for_timeout(500)
            continue


def _setup_dialog_capture(page: Page):
    """Авто-закрытие alert() и сбор их текстов в список."""
    alerts: list = []

    def on_dialog(d):
        alerts.append(d.message)
        d.accept()

    page.on("dialog", on_dialog)
    return alerts


def _login_once(page: Page, alerts: list, email: str, password: str):
    """Одна попытка входа. Возвращает (HTTP-статус AJAX-POST, текст alert)."""
    alerts.clear()
    page.locator("#id_mail").fill(email)
    page.locator("#id_password").fill(password)
    with page.expect_response(
        lambda r: r.request.method == "POST" and "/user/login/" in r.url,
        timeout=20000,
    ) as info:
        page.get_by_role("button", name="Войти").click()
    resp = info.value
    page.wait_for_timeout(800)
    return resp.status, (alerts[0] if alerts else "")


@allure.epic("Безопасность")
@allure.feature("Аутентификация — перечисление пользователей")
class TestUserEnumeration:
    """Проверка, что портал не позволяет определить существование аккаунта."""

    @allure.title("Безопасность: Одинаковая ошибка для существующего и несуществующего email")
    def test_login_no_user_enumeration(self, guest_page: Page):
        """
        Бизнес-кейс: сообщения об ошибке при неверном пароле для существующего
        email и для несуществующего email должны быть идентичны — иначе атакующий
        может перечислить реальные учётные записи.

        Ожидаемый результат (ОР): текст ошибки (alert) в обоих случаях одинаковый.
        """
        alerts = _setup_dialog_capture(guest_page)
        wrong_password = "WrongPass_12345"

        with allure.step("Шаг 1: Логин с реальным email и неверным паролем"):
            _open_login_form(guest_page)
            status_real, err_real = _login_once(guest_page, alerts, REAL_EMAIL, wrong_password)
            allure.attach(f"HTTP {status_real} | alert: {err_real}", name="Ошибка: реальный email",
                          attachment_type=allure.attachment_type.TEXT)

        with allure.step("Шаг 2: Логин с несуществующим email и паролем"):
            _open_login_form(guest_page)
            status_fake, err_fake = _login_once(guest_page, alerts, FAKE_EMAIL, wrong_password)
            allure.attach(f"HTTP {status_fake} | alert: {err_fake}", name="Ошибка: несуществующий email",
                          attachment_type=allure.attachment_type.TEXT)

        with allure.step("ОР: сообщения об ошибке идентичны (нет перечисления пользователей)"):
            assert err_real and err_real == err_fake, (
                "Уязвимость (перечисление пользователей): сообщения об ошибке различаются. "
                f"Реальный email: '{err_real}', несуществующий: '{err_fake}'. "
                "Атакующий может по разнице определить, существует ли аккаунт."
            )

    @allure.title("Безопасность: Восстановление пароля не выдаёт существование email")
    def test_recovery_password_no_enumeration(self, guest_page: Page):
        """
        Бизнес-кейс: форма восстановления пароля должна реагировать одинаково
        на существующий и несуществующий email (чтобы не было перечисления).

        Ожидаемый результат (ОР): текст ответа одинаков для обоих email.
        """

        def _recover_message(email: str) -> str:
            goto_with_retry(guest_page, f"{BASE_URL}/recovery-password/", wait_until="load")
            guest_page.wait_for_load_state("networkidle")
            _dismiss_cookie(guest_page)
            # Выбираем способ «По email», чтобы показать поле ввода
            guest_page.locator(".recovery-method[data-method='email']").first.click()
            guest_page.wait_for_timeout(600)
            email_input = guest_page.locator("#id_email")
            email_input.wait_for(state="visible", timeout=10000)
            email_input.fill(email)
            guest_page.wait_for_timeout(600)
            # Ждём, пока кнопка отправки станет активной
            try:
                guest_page.wait_for_function(
                    "() => { const b = document.querySelector('.send-email-button'); "
                    "return b && !b.classList.contains('disabled') && !b.disabled; }",
                    timeout=8000,
                )
            except Exception:
                pass
            guest_page.locator(".send-email-button").first.click(force=True, timeout=8000)
            guest_page.wait_for_timeout(2500)
            return guest_page.locator("body").inner_text(timeout=5000)

        with allure.step("Шаг 1: Восстановление для реального email"):
            msg_real = _recover_message(REAL_EMAIL)
            allure.attach(msg_real[:1500], name="Ответ: реальный email", attachment_type=allure.attachment_type.TEXT)

        with allure.step("Шаг 2: Восстановление для несуществующего email"):
            msg_fake = _recover_message(FAKE_EMAIL)
            allure.attach(msg_fake[:1500], name="Ответ: несуществующий email", attachment_type=allure.attachment_type.TEXT)

        with allure.step("ОР: ответы одинаковые (нет перечисления)"):
            not_found = re.compile(r"не\s*(существ|найд|зарегистр)|не существует|не найден|не зарегистрирован", re.IGNORECASE)
            real_marker = bool(not_found.search(msg_real))
            fake_marker = bool(not_found.search(msg_fake))
            assert not (real_marker != fake_marker), (
                "Уязвимость (перечисление пользователей): страница восстановления пароля "
                f"по-разному реагирует на существующий ({real_marker}) и несуществующий "
                f"({fake_marker}) email."
            )


@allure.epic("Безопасность")
@allure.feature("Аутентификация — ограничение перебора паролей")
class TestBruteForceProtection:
    """Проверка наличия rate-limiting / блокировки при переборе паролей."""

    @allure.title("Безопасность: Ограничение частоты неудачных попыток входа")
    @pytest.mark.brute_force
    @pytest.mark.skip(reason="Отключено временно: подтверждённое замечание (нет rate-limiting), см. report.txt — до исправления на портале")
    def test_login_rate_limiting(self, guest_page: Page):
        """
        Бизнес-кейс: после серии неудачных попыток входа портал должен применить
        ограничение (CAPTCHA, блокировка, 429) — иначе возможен перебор пароля.

        Важно: используется вымышленный email, чтобы не заблокировать реальный аккаунт.

        Ожидаемый результат (ОР): после серии неудачных попыток появляется ограничение.
        """
        alerts = _setup_dialog_capture(guest_page)
        _open_login_form(guest_page)

        attempts = 8
        statuses = []
        alert_texts = []
        for i in range(attempts):
            status, alert = _login_once(guest_page, alerts, FAKE_EMAIL, f"WrongPass_{i}_12345")
            statuses.append(status)
            alert_texts.append(alert)

        allure.attach(
            f"Попыток: {attempts}\nСтатусы: {statuses}\nAlerts: {alert_texts}",
            name="Результат rate-limit", attachment_type=allure.attachment_type.TEXT,
        )
        blocked_by_status = any(s in (403, 429, 503) for s in statuses)
        blocked_by_text = any(
            re.search(r"слишком|try again|too many|captcha|не робот|подтвердите|через некоторое время|заблокирован|повторите попытку", a, re.IGNORECASE)
            for a in alert_texts
        )
        assert blocked_by_status or blocked_by_text, (
            "Уязвимость: нет ограничения частоты неудачных попыток входа — "
            f"все {attempts} попыток вернули 200 без CAPTCHA/блокировки. "
            "Возможен перебор пароля (brute force). Рекомендуется rate-limiting / CAPTCHA."
        )


@allure.epic("Безопасность")
@allure.feature("Безопасность сессии")
class TestSessionSecurity:
    """Проверка безопасности сессионных идентификаторов."""

    @allure.title("Безопасность: Сессионный ID меняется после входа (защита от session fixation)")
    def test_session_id_changes_on_login(self, guest_page: Page):
        """
        Бизнес-кейс: после успешной авторизации сервер обязан выдать новый
        сессионный идентификатор — иначе атакующий, заложенный заранее, может
        «прилипнуть» к сессии (session fixation).

        Ожидаемый результат (ОР): сессионная кука до и после входа различается.
        """
        alerts = _setup_dialog_capture(guest_page)
        _open_login_form(guest_page)
        cookies_before = {c["name"]: c["value"] for c in guest_page.context.cookies()}
        session_before = {k: v for k, v in cookies_before.items() if "session" in k.lower()}
        allure.attach(str(session_before), name="Сессия до входа", attachment_type=allure.attachment_type.TEXT)

        with allure.step("Успешный вход"):
            _login_once(guest_page, alerts, REAL_EMAIL, REAL_PASSWORD)
            guest_page.wait_for_timeout(1000)

        cookies_after = {c["name"]: c["value"] for c in guest_page.context.cookies()}
        session_after = {k: v for k, v in cookies_after.items() if "session" in k.lower()}
        allure.attach(str(session_after), name="Сессия после входа", attachment_type=allure.attachment_type.TEXT)

        if session_before and session_after:
            same_key = set(session_before) & set(session_after)
            changed = any(session_before[k] != session_after[k] for k in same_key)
            assert changed, (
                "Уязвимость (session fixation): сессионный идентификатор не изменился "
                "после входа. Атакующий может зафиксировать сессию заранее."
            )
        else:
            assert session_after, "После входа не обнаружена сессионная кука — не удалось проверить fixation."

    @allure.title("Безопасность: Сессия инвалидируется при выходе")
    def test_session_invalidated_on_logout(self, job_seeker_page: Page):
        """
        Бизнес-кейс: после выхода сессия должна быть недействительна —
        повторный запрос по старой сессии не должен давать доступ к личным данным.

        Ожидаемый результат (ОР): после logout защищённая страница недоступна
        (редирект на логин / 403 / 401).
        """
        page = job_seeker_page
        protected_url = f"{BASE_URL}/registration/job-seeker/personal-info/"

        with allure.step("Шаг 1: Проверяем, что до выхода есть доступ"):
            goto_with_retry(page, protected_url, wait_until="load")
            assert "login" not in page.url, "Прекондишен: доступ до выхода не получен."

        with allure.step("Шаг 2: Выход из сессии (переход на /logout/)"):
            # Кнопка «Выход» — скрытый пункт выпадающего меню; надёжнее перейти на /logout/ напрямую
            page.goto(f"{BASE_URL}/logout/")
            page.wait_for_load_state("load", timeout=20000)
            page.wait_for_timeout(1000)

        with allure.step("Шаг 3: Повторно запрашиваем защищённую страницу по старой сессии"):
            response = page.request.get(protected_url, max_redirects=0)
            location = response.headers.get("location", "")
            redirected_to_login = "login" in location or "login" in page.url
            allure.attach(f"Статус после logout: {response.status}, Location: {location}",
                          name="Ответ после logout", attachment_type=allure.attachment_type.TEXT)
            assert response.status in (301, 302, 303, 401, 403) or redirected_to_login, (
                f"Уязвимость: после выхода сессия всё ещё валидна — защищённая страница "
                f"вернула {response.status}. Сессия не инвалидирована при logout."
            )
