from playwright.sync_api import Page, expect
import allure


def verify_change_paginate_by_count(guest_page: Page, page_object, card_locator):
    """Общий каркас проверки смены лимита карточек на странице (10 -> 20 -> 50 -> 10).

    Логика идентична для всех страниц выдачи; различается только локаут карточек
    (vacancy_cards vs vacancy_title_link) — передаётся параметром.
    """
    with allure.step("Шаг 1: Проверка дефолтного значения 10"):
        page_object.navigate()
        page_object.paginate_by_select.wait_for(state="visible", timeout=5000)
        expect(page_object.paginate_by_select).to_have_value("10")
        card_locator.first.wait_for(state="visible", timeout=5000)
        initial = card_locator.count()
        assert 0 < initial <= 10, f"Ошибка: дефолтное количество карточек {initial} > 10"

    for limit in ("20", "50", "10"):
        with allure.step(f"Переключение лимита на '{limit}' и верификация количества"):
            page_object.paginate_by_select.select_option(label=limit)
            guest_page.wait_for_load_state("load")
            card_locator.first.wait_for(state="visible", timeout=5000)
            count = card_locator.count()
            assert 0 < count <= int(limit), (
                f"Ошибка: при лимите {limit} отобразилось {count} карточек"
            )
