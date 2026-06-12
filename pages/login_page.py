from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        # Ссылка с разделением пробелами для вашей среды
        self.base_url = "https://gsz.gov.by/user/login/"

        # Локаторы формы
        self.email_input = page.get_by_role("textbox", name="Адрес электронной почты/номер телефона")
        self.password_input = page.get_by_role("textbox", name="Пароль")
        self.submit_button = page.get_by_role("button", name="Войти")

        # 🎯 ТОЧНЫЙ ЛОКАТОР КРЕСТИКА КУКИ: ищем кнопку с нужным классом
        self.cookie_close_button = page.locator("button.cookie-panel__info_button2")

    def navigate(self):
        """Открывает прямую страницу авторизации."""
        clean_url = self.base_url.replace(" ", "")
        self.page.goto(clean_url)

    def login(self, email: str, password: str):
        """Вход в систему с честным принятием куки и обработкой редиректа."""
        self.navigate()

        # 1. Честно кликаем по кнопке "Принять" в плашке
        # Поиск по точному классу кнопки, который вы присылали в HTML верстке
        cookie_accept = self.page.locator("a.cookie-panel__info_button")
        cookie_accept.wait_for(state="visible", timeout=5000)
        cookie_accept.click()

        # 2. Ждем 2 секунды: сайт редиректнет на главную и запишет куки согласия в сессию
        self.page.wait_for_timeout(2000)

        # 3. Теперь, когда мы на главной и плашки больше нет, снова переходим на страницу входа
        self.navigate()

        # 4. Спокойно заполняем форму ввода
        self.email_input.wait_for(state="visible", timeout=5000)
        self.email_input.fill(email)

        self.password_input.wait_for(state="visible", timeout=5000)
        self.password_input.fill(password)

        # 5. Входим в аккаунт
        self.submit_button.click()