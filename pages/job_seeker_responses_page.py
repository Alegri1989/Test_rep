from playwright.sync_api import Page, expect
from helpers.network_helper import goto_with_retry


class JobSeekerResponsesPage:
    """Page object для E2E-сценария отклика соискателя на вакансию.

    Сценарий: поиск вакансии по УНП нанимателя → отклик → выбор резюме →
    сопроводительное письмо → отправка → верификация успеха.
    """

    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/vacancy-search/"

        # Поиск вакансий
        self.search_input = page.locator("#id_profession")
        self.search_button = page.locator("button:has(.btn-title:has-text('Найти'))")
        self.employer_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Наниматель')]/following::span[contains(@class, 'select2-selection')]"
        ).first
        self.select2_search_field = page.locator(".select2-container--open input.select2-search__field")
        self.select2_options = page.locator(".select2-container--open li.select2-results__option")
        self.submit_filter_btn = page.locator("button[type='submit']").filter(has_text="Поиск").first

        # Карточки вакансий
        self.vacancy_title_link = page.locator("a.debounced-link")

        # Кнопка отклика (на странице вакансии)
        self.apply_button = page.locator(
            "a[href*='#resume-form-anchor'], a:has-text('Откликнуться')"
        ).first

        # Форма отклика (на странице вакансии, якорь #resume-form-anchor)
        self.resume_selector = page.locator("select[name='resume'], select#id_resume").first
        self.cover_letter_input = page.locator(
            "textarea[name='cover_letter'], textarea#id_cover_letter"
        ).first
        self.submit_application_btn = page.locator(
            "button[type='submit']:has-text('Откликнуться на вакансию')"
        ).first

        # Успех
        self.success_message = page.locator(
            ".alert-success, .success-message, [class*='success']"
        ).first

    def navigate_to_vacancy_search(self):
        """Переход на страницу поиска вакансий."""
        goto_with_retry(self.page, self.url, wait_until="load")
        self.page.wait_for_selector("#id_profession", state="visible", timeout=30000)
        self.page.wait_for_timeout(2000)

    def filter_by_employer_unp(self, unp: str):
        """Фильтрация вакансий по УНП нанимателя через Select2."""
        # Раскрываем спойлер, если скрыт
        if not self.employer_dropdown.is_visible():
            spoiler = self.page.locator("xpath=//h4[contains(text(), 'Наниматель')]").first
            spoiler.scroll_into_view_if_needed()
            spoiler.click()
            self.employer_dropdown.wait_for(state="visible", timeout=5000)

        self.employer_dropdown.click()
        self.select2_search_field.wait_for(state="visible", timeout=3000)
        self.select2_search_field.press_sequentially(unp, delay=60)
        self.page.wait_for_timeout(800)
        self.select2_options.first.wait_for(state="visible", timeout=3000)
        self.select2_options.first.click()

        # Применяем фильтр
        self.submit_filter_btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        self.submit_filter_btn.click(force=True)
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(500)

    def apply_for_vacancy(self, vacancy_id: str):
        """Открытие вакансии и переход к форме отклика."""
        # Ждём появления карточки вакансии
        self.vacancy_title_link.first.wait_for(state="visible", timeout=10000)
        self.vacancy_title_link.first.click()
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(500)

        # Нажимаем кнопку отклика (якорь #resume-form-anchor или текст)
        apply_btn = self.page.locator(
            "a[href*='#resume-form-anchor'], a:has-text('Откликнуться')"
        ).first
        apply_btn.wait_for(state="visible", timeout=10000)
        apply_btn.click()
        self.page.wait_for_timeout(1000)

    def select_resume(self, resume_id: str):
        """Выбор резюме из списка. Если resume_id не найден, берёт первое доступное."""
        self.resume_selector.wait_for(state="visible", timeout=10000)
        try:
            self.resume_selector.select_option(value=resume_id, timeout=3000)
        except Exception:
            # resume_id из конфига не существует в списке — берём первую доступную опцию
            options = self.resume_selector.locator("option").all()
            if len(options) > 1:
                first_option_value = options[1].get_attribute("value")
                self.resume_selector.select_option(value=first_option_value)
            else:
                raise RuntimeError("Нет доступных резюме для отклика")
        self.page.wait_for_timeout(300)

    def fill_cover_letter(self, text: str):
        """Заполнение сопроводительного письма (опционально)."""
        try:
            self.cover_letter_input.wait_for(state="visible", timeout=3000)
            self.cover_letter_input.fill(text)
            self.page.wait_for_timeout(300)
        except Exception:
            pass  # Поле может отсутствовать на форме

    def submit_application(self):
        """Отправка отклика."""
        self.submit_application_btn.wait_for(state="visible", timeout=10000)
        self.submit_application_btn.click()
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1000)

    def verify_success(self):
        """Верификация успешной отправки отклика."""
        # После отправки формы страница может перезагрузиться или показать alert.
        # Ждём, что форма отклика исчезла (успех) или появилось success-сообщение.
        try:
            self.success_message.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            pass
        # Альтернатива: форма отклика больше не видна (успешная отправка)
        try:
            self.resume_selector.wait_for(state="hidden", timeout=10000)
            return
        except Exception:
            pass
        # Альтернатива: URL изменился (редирект после отправки)
        try:
            self.page.wait_for_url("**/message/**", timeout=10000)
            return
        except Exception:
            pass
        raise RuntimeError("Не удалось подтвердить успешную отправку отклика")
