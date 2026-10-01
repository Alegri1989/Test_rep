from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        # Ссылка с разделением пробелами для вашей среды
        self.base_url = "https://gsz.gov.by/user/login/"

        # Локаторы формы (по id — стабильно, не зависит от label/role)
        self.email_input = page.locator("#id_mail")
        self.password_input = page.locator("#id_password")
        self.submit_button = page.get_by_role("button", name="Войти")

        # Вкладка «Соискатель» — переключает раздел на странице входа ДО логина
        self.job_seeker_tab = page.locator("#pills-job-seeker-tab")
        # Вкладка «Вход» внутри раздела соискателя — содержит форму логина
        self.login_tab = page.locator("#pills-login-tab")

        # 🎯 ТОЧНЫЙ ЛОКАТОР КРЕСТИКА КУКИ: ищем кнопку с нужным классом
        self.cookie_close_button = page.locator("button.cookie-panel__info_button2")

    def navigate(self):
        """Открывает прямую страницу авторизации с устойчивостью к медленной сети."""
        clean_url = self.base_url.replace(" ", "")
        goto_with_retry(self.page, clean_url, wait_until="load")

    def login(self, email: str, password: str):
        """Вход в систему с честным принятием куки и обработкой редиректа."""
        self.navigate()

        # 1. Честно кликаем по кнопке "Принять" в плашке и ждём навигации
        cookie_accept = self.page.locator("a.cookie-panel__info_button")
        cookie_accept.wait_for(state="visible", timeout=5000)
        with self.page.expect_navigation(wait_until="load", timeout=10000):
            cookie_accept.click()

        # 3. Теперь, когда мы на главной и плашки больше нет, снова переходим на страницу входа
        self.navigate()

        # 4. Переключаемся в раздел «Соискатель» — форма входа соискателя скрыта по умолчанию
        self.job_seeker_tab.wait_for(state="visible", timeout=10000)
        self.job_seeker_tab.click()

        # 5. Внутри раздела соискателя активируем вкладку «Вход» (с формой логина)
        self.login_tab.wait_for(state="visible", timeout=10000)
        self.login_tab.click()

        # 6. Спокойно заполняем форму ввода
        self.email_input.wait_for(state="visible", timeout=10000)
        self.email_input.fill(email)

        self.password_input.wait_for(state="visible", timeout=10000)
        self.password_input.fill(password)

        # 7. Входим в аккаунт
        self.submit_button.click()