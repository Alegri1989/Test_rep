import allure
from playwright.sync_api import Page


class ResumePage:
    def __init__(self, page: Page):
        self.page = page

        # Кнопка создания на странице списка резюме
        self.create_resume_button = page.get_by_role("link", name="Создать резюме")

        # Заблокированные инпуты профиля
        self.last_name_input = page.locator("#id_last_name")
        self.first_name_input = page.locator("#id_first_name")
        self.middle_name_input = page.locator("#id_patronymic")
        self.age_input = page.locator("#id_age")
        self.education_dropdown = page.locator("#id_education")

        # Отображаемые контейнеры адреса (Select2)
        self.region_container = page.locator("#select2-id_region-container")
        self.district_container = page.locator("#select2-id_district-container")
        self.address_container = page.locator("#select2-id_village_council-container")

        # Чекбоксы
        self.privacy_checkbox = page.get_by_label("Скрыть ФИО")
        self.relocate_checkbox = page.get_by_label(
            "Рассматриваю трудоустройство в другой местности (переезд)"
        )

        # Кнопки добавления контактов
        self.add_phone_button = page.get_by_role("button", name="Добавить номер")
        self.add_email_button = page.get_by_role("button", name="Добавить E-mail")

        # Дефолтное поле Email
        self.email_input_0 = page.locator("#id_resume_emails-0-email")

        # Динамическое поле телефона
        self.phone_input_0 = page.locator("#id_resume_phones-0-number")

        # Кнопки удаления конкретных строк (крестики)
        self.delete_phone_button_0 = page.locator(
            "#id_resume_phones-0-number ~ button[data-formset-delete-button]"
        )
        self.delete_email_button_1 = page.locator(
            "#id_resume_emails-1-email ~ button[data-formset-delete-button]"
        )

        # Раздел "Пожелания к работе"
        self.profession_container = page.locator(
            "#select2-id_desired_profession-0-desired_profession-container"
        )
        self.select2_search_input = page.locator(
            "input.select2-search__field[aria-controls*='desired_profession']"
        )
        self.select2_first_option = page.locator(".select2-results__option").first
        # Производная должности на форме создания (create)
        self.derivative_dropdown = page.locator(
            "#id_desired_profession-0-derivative_post_or_profession"
        )
        # Производная должности на форме редактирования (update)
        self.derivative_update_dropdown = page.locator(
            "#id_derivative_post_or_profession"
        )
        self.salary_input = page.locator("#id_desired_salary")
        self.employment_nature_dropdown = page.locator("#id_employment_nature")
        self.work_mode_dropdown = page.locator("#id_work_mode")
        self.housing_checkbox = page.get_by_label("Требуется жилье")

        # Раздел "Опыт работы"
        self.add_experience_button = page.get_by_role(
            "button", name="Добавить место работы"
        )
        self.exp_org_input = page.locator("#id_resume_experience-0-organization")
        self.exp_years_input = page.locator("#id_resume_experience-0-experience_years")
        self.exp_months_input = page.locator("#id_resume_experience-0-experience_month")
        self.exp_profession_input = page.locator("#id_resume_experience-0-profession")
        self.exp_duties_input = page.locator("#id_resume_experience-0-duties")
        self.exp_additional_textarea = page.locator(
            "#id_resume_experience-0-additionally"
        )
        self.delete_experience_button_0 = page.locator(
            "#id_resume_experience-0-duties ~ button[data-formset-delete-button]"
        )

        # Раздел "Образование"
        self.add_education_button = page.get_by_role(
            "button", name="Добавить место обучения"
        )
        self.edu_name_input = page.locator("#id_resume_education-0-name")
        self.edu_specialty_input = page.locator("#id_resume_education-0-specialty")
        self.edu_ending_input = page.locator("#id_resume_education-0-ending")
        self.edu_info_textarea = page.locator("#id_resume_education-0-info")
        self.delete_education_button_0 = page.locator(
            "#id_resume_education-0-specialty ~ button[data-formset-delete-button]"
        )

        # Раздел "Владение языками"
        self.language_dropdown = page.locator("#id_resume_languages-0-language")
        self.lang_level_dropdown = page.locator("#id_resume_languages-0-language_level")
        self.add_language_button = page.get_by_role("button", name="Добавить язык")
        self.delete_language_button_1 = page.locator(
            "#id_resume_languages-1-language_level ~ button[data-formset-delete-button]"
        )

        # Раздел "Гибкие навыки"
        self.skills_container = page.locator(".select2-selection--multiple")
        self.skills_search_input = page.locator
        self.skills_search_input = page.locator(
            "input.select2-search__field[aria-controls*='acquired_skills']"
        )
        self.skills_first_remove_btn = page.locator(
            ".select2-selection__choice__remove"
        ).first

        self.additional_info_textarea = page.locator("#id_wishes")

        self.submit_resume_button = page.get_by_role(
            "button", name="Создать резюме"
        )

        self.first_resume_edit_link = page.locator(
            "a[href*='/registration/job-seeker/resume/'][href$='/update/']"
        ).first

        self.last_resume_delete_btn = page.get_by_role("button", name="Удалить").last
        self.popup_confirm_delete_btn = page.locator("#delete")

    def get_skill_option_by_text(self, text: str):
        """Возвращает локатор строки в результатах поиска по тексту навыка."""
        return self.page.locator(
            f"#select2-id_acquired_skills-results "
            f".select2-results__option:has-text('{text}')"
        )


