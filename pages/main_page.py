from playwright.sync_api import Page


class MainPage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = "https://gsz.gov.by"

        # Ссылки главного верхнего меню
        self.job_seeker_menu = page.get_by_role("button", name="Соискателю")
        self.employer_menu = page.get_by_role("button", name="Нанимателю")
        self.employment_service_menu = page.get_by_role("button", name="Органам занятости")
        self.info_menu = page.get_by_role("button", name="Информация")
        self.e_services_menu = page.get_by_role("button", name="Электронные сервисы")

        # Элементы главного блока поиска
        self.search_input = page.locator("#id_profession")
        self.search_button = page.locator("button:has(.btn-title:has-text('Найти'))")

        # Переключатели масштаба карты
        self.map_scale_country = page.locator("label.radio-label", has_text="Страна")
        self.map_scale_regions = page.locator("label.radio-label", has_text="Области")
        self.map_scale_districts = page.locator("label.radio-label", has_text="Районы")

        # Коллекция точек на SVG карте
        self.map_dots = page.locator("svg circle")

        # Элементы счетчиков слева
        self.region_title = page.locator("#region_rating b")
        self.vacancy_counter = page.locator("#region_vacancy_rating")
        self.resume_counter = page.locator("#region_resume_rating")

        # Всплывающая карточка района справа и ее элементы
        self.info_card_title = page.locator("h4.empl_dep_soato")
        self.info_card = page.locator("div.inner-box").filter(has=self.info_card_title)
        self.go_to_site_button = self.info_card.get_by_role("link", name="Перейти на сайт")
        self.go_to_vacancies_button = self.info_card.get_by_role("link", name="Перейти к вакансиям")
        self.immigrant_employment_button = page.locator(
            "a.btn-style-one[href='/registration/foreign-citizens-employment/public/list/']"
        )

        # Кнопка перехода в блоке временного трудоустройства молодежи
        self.youth_employment_button = page.locator("a[href='/registration/temporary-employment/young/']")

        # Переключатели вкладок популярных вакансий
        self.tab_day = page.locator("#pills-home-tab")
        self.tab_week = page.locator("#pills-profile-tab")
        self.tab_popular = page.locator("#pills-contact-tab")
        self.featured_vacancy_links = page.locator("#pills-contact a.t")
        self.show_more_vacancies_btn = page.get_by_role("link", name="Показать больше")

        # Блок гибких навыков
        self.skills_switch = page.locator("span.switch-label")
        self.skill_time_management = page.locator("label.checkbox-label[for='24']")
        self.skills_search_button = page.locator("#vac_or_res_button")

        # Заголовок блока топ-нанимателей
        self.employers_carousel_section = page.locator("text=Приглашают в команду")

        # Кнопка скачивания мобильного приложения Android
        self.download_app_button = page.locator("button.btn-download")

        # Ссылка на PDF-инструкцию
        self.download_instruction_link = page.get_by_role(
            "link", name="Инструкция по скачиванию мобильного приложения"
        )

    def navigate(self):
        """Открывает главную страницу портала."""
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("networkidle")

    def click_employer_logo_via_js(self, img_name: str):
        """Находит первый видимый логотип по имени файла и кликает по нему через JS."""
        logo_locator = self.page.locator(f"img[src*='{img_name}']").first
        logo_locator.wait_for(state="visible", timeout=5000)
        logo_locator.dispatch_event("click")