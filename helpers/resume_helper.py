import re
import allure
from playwright.sync_api import Page
from pages.resume_page import ResumePage
from helpers.network_helper import goto_with_retry


def login_as_job_seeker(page: Page):
    """Авторизует пользователя как соискателя."""
    page.goto("https://gsz.gov.by/user/login/")
    
    # Ждем появления формы логина
    page.wait_for_selector("form#login-form", state="visible", timeout=90000)
    
    # Ищем поле логина по name
    username_field = page.locator("input[name='username']")
    username_field.wait_for(state="visible", timeout=90000)
    
    # Заполняем поля с проверкой
    username_field.fill("job_seeker_username")
    page.locator("input[name='password']").fill("job_seeker_password")
    
    # Кликаем кнопку входа
    page.click("button[type='submit']")
    
    # Проверяем успешную авторизацию
    page.wait_for_selector("a[href*='/user/logout/']", state="visible", timeout=60000)

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

        resume.language_dropdown.select_option(label="Английский", force=True)
        resume.lang_level_dropdown.select_option(label="средний", force=True)

        resume.skills_container.click()
        resume.skills_search_input.press_sequentially("Тайм-менеджмент", delay=100)
        page.wait_for_timeout(500)
        resume.select2_first_option.click()

        resume.additional_info_textarea.fill("тестобщ")

        resume.submit_resume_button.click()
        page.wait_for_timeout(3000)

def fill_and_submit_required_resume_fields(page: Page) -> str | None:
    """Заполняет обязательные поля формы резюме, отправляет и возвращает ID созданного резюме."""
    resume = ResumePage(page)

    with allure.step("Быстрое заполнение обязательных полей резюме"):
        resume.profession_container.wait_for(state="visible", timeout=5000)
        resume.profession_container.click()
        resume.select2_search_input.press_sequentially("Авербандщик", delay=100)
        page.wait_for_timeout(500)
        resume.select2_first_option.click()

        resume.salary_input.fill("2000")

        resume.language_dropdown.select_option(label="Английский", force=True)
        resume.lang_level_dropdown.select_option(label="средний", force=True)

        resume.submit_resume_button.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)

    last_link = page.locator(
        "a[href*='/registration/job-seeker/resume/'][href$='/update/']"
    ).last
    last_link.wait_for(state="visible", timeout=5000)
    href = last_link.get_attribute("href")
    match = re.search(r"/resume/(\d+)/", href) if href else None
    return match.group(1) if match else None

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
        page.wait_for_load_state("load")
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
        page.wait_for_load_state("load")


def clear_resume_by_id(page: Page, resume_id: str):
    """Снимает с публикации (если нужно) и удаляет конкретное резюме по его ID."""
    resume = ResumePage(page)
    resume_list_url = "https://gsz.gov.by/registration/job-seeker/resume/list/"

    if page.url != resume_list_url:
        goto_with_retry(page, resume_list_url, wait_until="load")
        page.wait_for_load_state("load")

    unpublish_link = resume.get_unpublish_btn_by_id(resume_id)
    if unpublish_link.count() > 0:
        unpublish_link.click()
        page.wait_for_load_state("load")
        page.wait_for_timeout(1000)

    # Находим позицию резюме в списке по edit-ссылке и кликаем соответствующую кнопку удаления
    edit_links = page.locator(
        "a[href*='/registration/job-seeker/resume/'][href$='/update/']"
    ).all()
    delete_buttons = page.get_by_role("button", name="Удалить")

    for idx, link in enumerate(edit_links):
        href = link.get_attribute("href")
        if href and f"/resume/{resume_id}/" in href:
            delete_buttons.nth(idx).click()
            resume.popup_confirm_delete_btn.wait_for(state="visible", timeout=3000)
            resume.popup_confirm_delete_btn.click()
            resume.delete_resume_modal.wait_for(state="hidden", timeout=5000)
            return
