import allure
import pytest
from playwright.sync_api import Page, expect
from pages.help_page import HelpPage


@pytest.mark.help_page
@allure.title("Бизнес-кейс: Проверка скачивания руководства пользователя для соискателя")
def test_guest_download_seeker_guide(auth_page: Page):
    page = auth_page
    help_page = HelpPage(page)

    with allure.step("Шаг 1: Переход на страницу помощи"):
        help_page.navigate()

    with allure.step("Шаг 2: Проверка видимости кнопки и корректности ссылки на PDF соискателя"):
        expect(help_page.download_seeker_guide_btn).to_be_visible(timeout=5000)
        href = help_page.download_seeker_guide_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".pdf"), f"Ошибка: ссылка ведет на неверный формат '{href}'"


@pytest.mark.help_page
@allure.title("Бизнес-кейс: Проверка скачивания ВСЕХ инструкций во вкладке нанимателя")
def test_guest_download_employer_instructions(auth_page: Page):
    page = auth_page
    help_page = HelpPage(page)

    with allure.step("Шаг 1: Переход на страницу помощи"):
        help_page.navigate()

    with allure.step("Шаг 2: Скролл и переключение на вкладку 'Нанимателю' через JS"):
        help_page.employer_tab.scroll_into_view_if_needed()
        help_page.employer_tab.dispatch_event("click")
        page.wait_for_timeout(1500)
        expect(help_page.employer_tab).to_contain_class("active")

    with allure.step("Шаг 3: Проверка ссылки на руководство администратора нанимателя (PDF)"):
        expect(help_page.download_employer_guide_btn).to_be_visible(timeout=5000)
        href = help_page.download_employer_guide_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".pdf"), f"Ошибка: ссылка ведет на неверный формат '{href}'"

    with allure.step("Шаг 4: Проверка ссылки на порядок подачи вакансий (PDF)"):
        expect(help_page.download_vacancy_order_btn).to_be_visible(timeout=3000)
        href = help_page.download_vacancy_order_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".pdf"), f"Ошибка: ссылка ведет на неверный формат '{href}'"

    with allure.step("Шаг 5: Проверка ссылки на инструкцию по входу нанимателя (PDF)"):
        expect(help_page.download_login_instruction_btn).to_be_visible(timeout=3000)
        href = help_page.download_login_instruction_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".pdf"), f"Ошибка: ссылка ведет на неверный формат '{href}'"

    with allure.step("Шаг 6: Проверка ссылки на инструкцию для Chrome (PDF)"):
        expect(help_page.download_chrome_instruction_btn).to_be_visible(timeout=3000)
        href = help_page.download_chrome_instruction_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".pdf"), f"Ошибка: ссылка ведет на неверный формат '{href}'"

    with allure.step("Шаг 7: Проверка ссылки на инструкцию комплекта абонента ГосСУОК (PDF)"):
        expect(help_page.download_gossuok_instruction_btn).to_be_visible(timeout=3000)
        href = help_page.download_gossuok_instruction_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".pdf"), f"Ошибка: ссылка ведет на неверный формат '{href}'"

    with allure.step("Шаг 8: Проверка ссылки на шаблон заявки для справочника ЮЛ (DOCX)"):
        expect(help_page.download_legal_entity_template_btn).to_be_visible(timeout=3000)
        href = help_page.download_legal_entity_template_btn.get_attribute("href")
        assert href is not None, "Ошибка: у ссылки отсутствует атрибут href"
        assert href.lower().endswith(".docx"), f"Ошибка: ссылка ведет на неверный формат '{href}'"