from playwright.sync_api import Page, expect
import allure


def verify_filter_reset(guest_page: Page, page_object, default_url: str):
    """Общий каркас проверки сброса фильтров:
    1. Переход на страницу.
    2. Применение демо-фильтра (уникальный для каждого page object).
    3. Нажатие кнопки "Сбросить фильтр".
    4. Проверка возврата к дефолтному URL и очистки демо-фильтра.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        page_object.navigate()

    with allure.step("Шаг 2: Применение демо-фильтра"):
        page_object.apply_sample_filter()

    with allure.step("Шаг 3: Нажатие 'Сбросить фильтр' и ожидание обновления страницы"):
        page_object.reset_filter_btn.wait_for(state="visible", timeout=5000)
        page_object.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация возврата к дефолтному URL"):
        expect(guest_page).to_have_url(default_url)

    with allure.step("ОР 2: Верификация очистки демо-фильтра"):
        page_object.verify_filter_cleared()
