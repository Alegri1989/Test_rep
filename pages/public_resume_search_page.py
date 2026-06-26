from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class PublicResumeSearchPage:
    def __init__(self, page: Page):
        self._page = page
        self.url = "https://gsz.gov.by/registration/resume-search/"

        # Верхняя строка поиска
        self.profession_input = page.locator("#id_resume_profession")
        self.search_btn_main = page.locator("button.theme-btn.btn-style-one")

        # Всегда видимые фильтры (без спойлера)
        self.region_container = page.locator("#select2-id_region-container")
        self.salary_min_input = page.locator("#id_salary_min")

        # Кнопки управления фильтрами
        self.submit_filter_btn = page.locator("button[type='submit'].btn.btn-primary")
        self.reset_filter_btn = page.locator("a.btn-outline-primary[href*='resume-search/?']")

        # Заголовки спойлеров (кликабельны — раскрывают блок)
        self.status_header = page.locator("#id_status-header")
        self.work_mode_header = page.locator("#id_work_mode-header")
        self.employment_nature_header = page.locator("#id_employment_nature-header")
        self.education_header = page.locator("#id_education-header")
        self.skills_header = page.locator("#id_acquired_skills-header")
        self.additional_header = page.locator("#other-header")

        # Поля внутри спойлеров
        self.status_select = page.locator("#id_status")
        self.agree_to_relocate_checkbox = page.locator("#id_agree_to_relocate")
        self.experience_checkbox = page.locator("#id_experience")

        # Сортировка и количество на странице
        self.paginate_select = page.locator("#paginate_by_select")
        self.sort_select = page.locator("#sort_by")

        # Карточки резюме
        self.resume_cards = page.locator("div.inner-box.h-100")
        self.profession_in_card = page.locator("h4.job-title a b")

        # Кнопки внутри карточек (заблокированы для гостя)
        self.apply_buttons = page.locator("a.btn.btn-primary.disabled[title*='резюме']")
        self.contacts_buttons = page.locator("a.btn.btn-outline-primary.disabled[title*='резюме']")

        # Блок "Контактное лицо по резюме" (должен отсутствовать для гостя)
        self.contact_person_block = page.locator("b", has_text="Контактное лицо по резюме")

    def navigate(self):
        goto_with_retry(self._page, self.url, wait_until="load")
        self.resume_cards.first.wait_for(state="visible", timeout=10000)

    def select_region(self, region_name: str):
        # Устанавливаем значение нативного select напрямую без jQuery trigger:
        # $(sel).trigger('change') сбрасывает значение обратно (Select2 перехватывает
        # событие и выставляет собственное внутреннее пустое состояние).
        self._page.wait_for_selector('select[name="region"]', state="attached", timeout=5000)
        self._page.evaluate(f"""
            () => {{
                const sel = document.querySelector('select[name="region"]');
                if (!sel) return;
                const opt = [...sel.options].find(o => o.text.trim().includes('{region_name}'));
                if (opt) sel.value = opt.value;
            }}
        """)

    def expand_filter(self, header_locator):
        """Раскрывает спойлер фильтра и ждёт появления его содержимого."""
        header_locator.scroll_into_view_if_needed()
        header_locator.click()
        self._page.wait_for_timeout(400)

    def apply_filter_and_wait(self):
        self.submit_filter_btn.click()
        self._page.wait_for_load_state("domcontentloaded")
