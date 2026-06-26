import allure
from playwright.sync_api import Page
from pages.resume_page import ResumePage
from helpers.network_helper import goto_with_retry


def fill_and_submit_resume_form(page: Page):
    """Хелпер для максимального заполнения всех полей формы резюме."""
    resume = ResumePage(page)

    with allure.step("Полное заполнение формы резюме всеми данными"):
        resume.profession_container.wait_for(state="visible", timeout=5000)
        resume.profession_container.click()
        resume.select2_search_input.press_sequentially("Авербандщик", delay=100)
        page.wait_for_timeout(500)
        resume.select2_first_option.click()

        resume.salary_input.fill("2000")
        resume.employment_nature_dropdown.select_option(label="Постоянная")
        resume.work_mode_dropdown.select_option(label="Одна смена")

        resume.add_experience_button.click()
        resume.exp_org_input.fill("Тесторг")
        resume.exp_profession_input.fill("Тестдолжность")
        resume.exp_duties_input.fill("Тестобязанности")
        resume.exp_years_input.fill("2")
        resume.exp_months_input.fill("5")

        resume.add_education_button.click()
        resume.edu_name_input.fill("Тестовый ВУЗ")
        resume.edu_specialty_input.fill("Тест-Специализация")
        resume.edu_qualification_input.fill("Повар")
        resume.edu_ending_input.fill("2020")
        resume.edu_info_textarea.fill("тестобр")

        resume.select_language_s2("Английский")
        resume.select_lang_level_s2("средний")

        resume.skills_container.click()
        resume.skills_search_input.press_sequentially("Тайм-менеджмент", delay=100)
        page.wait_for_timeout(500)
        resume.select2_first_option.click()

        resume.additional_info_textarea.fill("тестобщ")

        resume.submit_resume_button.click()
        page.wait_for_timeout(3000)

def fill_and_submit_required_resume_fields(page: Page):
    """Хелпер для быстрого заполнения только обязательных полей формы резюме (профессия, зарплата, язык)."""
    resume = ResumePage(page)

    with allure.step("Быстрое заполнение обязательных полей резюме"):
        resume.profession_container.wait_for(state="visible", timeout=5000)
        resume.profession_container.click()
        resume.select2_search_input.press_sequentially("Авербандщик", delay=100)
        page.wait_for_timeout(500)
        resume.select2_first_option.click()

        resume.salary_input.fill("2000")

        resume.select_language_s2("Английский")
        resume.select_lang_level_s2("средний")

        resume.submit_resume_button.click()
        page.wait_for_timeout(3000)

def clear_all_resumes_from_account(page: Page):
    """Полностью удаляет все резюме со страницы списка (снимает с публикации и удаляет)."""
    resume = ResumePage(page)
    resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"

    if page.url != resume_list_url:
        goto_with_retry(page, resume_list_url, wait_until="load")
        page.wait_for_load_state("load")

    # Сначала снимаем все опубликованные резюме с публикации с паузой
    while resume.all_unpublish_links.count() > 0:
        resume.all_unpublish_links.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

    # Пошагово удаляем каждый черновик с задержкой между удалениями
    while resume.all_delete_buttons.count() > 0:
        initial_count = resume.all_delete_buttons.count()
        page.wait_for_timeout(1500)

        resume.all_delete_buttons.first.click()
        resume.popup_confirm_delete_btn.wait_for(state="visible", timeout=3000)
        resume.popup_confirm_delete_btn.click()

        try:
            page.wait_for_function(
                f"() => document.querySelectorAll('.delete_resume__button').length < {initial_count}",
                timeout=5000
            )
        except Exception:
            page.wait_for_timeout(1000)

        resume.delete_resume_modal.wait_for(state="hidden", timeout=5000)
        page.wait_for_load_state("networkidle")