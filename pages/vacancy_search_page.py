from playwright.sync_api import Page
from helpers.network_helper import goto_with_retry


class VacancySearchPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://gsz.gov.by/registration/vacancy-search/"

        # Основной блок поиска
        self.search_input = page.locator("#id_profession")
        self.search_button = page.locator("button:has(.btn-title:has-text('Найти'))")

        # Кнопки панели фильтров
        self.submit_filter_btn = page.locator("button[type='submit']").filter(has_text="Поиск").first
        self.reset_filter_btn = page.locator("a:has-text('Сбросить фильтр')").first

        # Трёхуровневый фильтр локации (Область, Район, Город)
        self.region_dropdown = page.locator("#select2-id_region-container")
        self.district_dropdown = page.locator("#select2-id_district-container")
        self.address_dropdown = page.locator("#select2-id_village_council-container")

        # Блоки фильтров Select2
        self.work_time_mode_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Режим рабочего времени')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        self.employer_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Наниматель')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        self.work_nature_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Характер работы')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        self.education_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Образование')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        self.citizens_category_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'С возможностью трудоустройства')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        self.soft_skills_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Гибкие навыки')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        self.activity_sphere_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Сфера деятельности')]/following::span[contains(@class, 'select2-selection')]"
        ).first

        # 11. Фильтр Дополнительные параметры (Локаторы текстовых лейблов)
        self.additional_params_dropdown = page.locator(
            "xpath=//h4[contains(text(), 'Дополнительные параметры')]"
        ).first
        self.students_label = page.locator("label[for='id_temporary_for_students']")
        self.age_14_16_label = page.locator("label[for='id_tfs_0']")

        # Общие элементы внутри активного раскрытого окна Select2
        self.select2_search_field = page.locator(".select2-container--open input.select2-search__field")
        self.select2_options = page.locator(".select2-container--open li.select2-results__option")

        # Селекторы карточек результатов поиска
        self.vacancy_title_link = page.locator("a.debounced-link")

        # Кнопка "Контакты" на карточке вакансии (ведет на якорь contact-info-anchor детальной страницы)
        self.vacancy_contacts_button = page.locator("a[href*='detail-public/#contact-info-anchor']")

        # Заблокированная для гостя кнопка "Откликнуться" (используется и в списке, и на детальной странице -
        # одна и та же разметка, отличие только в том, на какой странице сейчас находится page)
        self.apply_button_in_list = page.locator(
            "a[title='Только соискатель может откликнуться на вакансию']"
        )
        self.apply_button_in_detail = page.locator(
            "a[title='Только соискатель может откликнуться на вакансию']"
        )

        # Дополнительные поля
        self.salary_min_input = page.locator("#id_salary_min")
        self.search_period_dropdown = page.locator("#id_search_period")
        self.wage_rate_spoiler_title = page.locator("h4.col-11:has-text('Ставка')")
        self.wage_rate_from_input = page.locator("#id_wage_rate_from")
        self.wage_rate_to_input = page.locator("#id_wage_rate_to")

    def navigate(self):
        """Чистый переход на страницу поиска вакансий с устойчивостью к медленной сети."""
        clean_url = self.url.replace(" ", "")
        goto_with_retry(self.page, clean_url, wait_until="load")

    def open_spoiler_if_hidden(self, title_text: str, target_dropdown):
        """Проверяет видимость фильтра и кликает по его заголовку h4 для раскрытия спойлера."""
        if not target_dropdown.is_visible():
            spoiler_title = self.page.locator(f"xpath=//h4[contains(text(), '{title_text}')]").first
            spoiler_title.scroll_into_view_if_needed()
            spoiler_title.click()
            target_dropdown.wait_for(state="visible", timeout=3000)

    def select_from_dropdown(self, dropdown_locator, item_name: str):
        """Выбор элемента из списка Select2 со встречным посимвольным вводом."""
        dropdown_locator.click()
        self.select2_search_field.wait_for(state="visible", timeout=3000)
        self.select2_search_field.press_sequentially(item_name, delay=60)
        self.page.wait_for_timeout(800)

        target_option = self.page.get_by_role("option", name=item_name, exact=True)
        target_option.wait_for(state="visible", timeout=3000)
        target_option.click()

    def select_employer_by_unp(self, unp_value: str):
        """Вводит УНП посимвольно и кликает по первому выпавшему результату организации."""
        self.employer_dropdown.click()
        self.select2_search_field.wait_for(state="visible", timeout=3000)
        self.select2_search_field.press_sequentially(unp_value, delay=60)
        self.page.wait_for_timeout(800)
        self.select2_options.first.wait_for(state="visible", timeout=3000)
        self.select2_options.first.click()

    def open_wage_rate_spoiler_if_needed(self):
        """Раскрывает спойлер 'Ставка', если инпуты скрыты."""
        if not self.wage_rate_from_input.is_visible():
            self.wage_rate_spoiler_title.click()
            self.wage_rate_from_input.wait_for(state="visible", timeout=3000)