from playwright.sync_api import Page, expect
import allure


def verify_pagination_forward_back(guest_page: Page, page_object):
    """Общий каркас проверки постраничной навигации: вперёд на стр. 2, назад на стр. 1.

    Логика идентична для всех страниц выдачи (education, future_work, gpd),
    отличающихся только page object.
    """
    with allure.step("Шаг 1: Переход на страницу и клик по ссылке второй страницы"):
        page_object.navigate()
        page_object.page_2_link.wait_for(state="visible", timeout=5000)
        page_object.page_2_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация активной второй страницы"):
        expect(page_object.active_page_number).to_have_text("2")
        page_object.vacancy_cards.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по стрелке 'назад'"):
        page_object.back_arrow_btn.wait_for(state="visible", timeout=5000)
        page_object.back_arrow_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 2: Верификация возврата на первую страницу"):
        expect(page_object.active_page_number).to_have_text("1")
        page_object.vacancy_cards.first.wait_for(state="visible", timeout=5000)
