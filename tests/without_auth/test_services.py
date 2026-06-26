import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.services_page import ServicesPage


@pytest.mark.services
@allure.epic("Услуги службы занятости")
@allure.feature("Загрузка страницы")
@allure.title("Смоук: Страница услуг загружается со списком пунктов")
def test_page_loads_with_service_items(services_page: ServicesPage):
    """
    Смоук: Публичный список услуг доступен без авторизации и содержит
    пункты с раскрываемыми заголовками.

    Шаги:
    1. Открыть страницу списка услуг.

    ОР:
    - На странице присутствует хотя бы один заголовок с иконкой разворота.
    - Кнопки "Перейти" скрыты до раскрытия (контент свёрнут по умолчанию).
    """
    with allure.step("Шаг 1: Переход на страницу"):
        services_page.navigate()

    with allure.step("ОР: Заголовки видны, кнопки 'Перейти' скрыты"):
        expect(services_page.service_headers.first).to_be_visible()
        expect(services_page.view_buttons.first).not_to_be_visible()


@pytest.mark.services
@allure.epic("Услуги службы занятости")
@allure.feature("Разворот пункта")
@allure.title("Бизнес-кейс: Клик по заголовку раскрывает содержимое и показывает кнопку 'Перейти'")
def test_expand_item_reveals_view_button(services_page: ServicesPage):
    """
    Бизнес-кейс: Клик по h4 первого пункта раскрывает содержимое,
    и кнопка "Перейти" становится видимой.

    Шаги:
    1. Открыть страницу.
    2. Кликнуть по заголовку первого пункта.

    ОР:
    - Кнопка "Перейти" первого пункта становится видимой.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        services_page.navigate()

    with allure.step("Шаг 2: Клик по заголовку первого пункта"):
        services_page.expand_item(0)

    with allure.step("ОР: Кнопка 'Перейти' видна"):
        expect(services_page.view_buttons.first).to_be_visible()


@pytest.mark.services
@allure.epic("Услуги службы занятости")
@allure.feature("Разворот пункта")
@allure.title("Бизнес-кейс: Повторный клик по заголовку сворачивает содержимое")
def test_collapse_item_hides_view_button(services_page: ServicesPage):
    """
    Бизнес-кейс: Повторный клик по раскрытому заголовку сворачивает
    содержимое — кнопка "Перейти" скрывается.

    Шаги:
    1. Открыть страницу.
    2. Раскрыть первый пункт.
    3. Кликнуть по заголовку повторно.

    ОР:
    - Кнопка "Перейти" снова скрыта.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        services_page.navigate()

    with allure.step("Шаг 2: Раскрытие первого пункта"):
        services_page.expand_item(0)
        expect(services_page.view_buttons.first).to_be_visible()

    with allure.step("Шаг 3: Повторный клик — сворачивание"):
        services_page.expand_item(0)

    with allure.step("ОР: Кнопка 'Перейти' скрыта"):
        expect(services_page.view_buttons.first).not_to_be_visible()


@pytest.mark.services
@allure.epic("Услуги службы занятости")
@allure.feature("Детальная страница")
@allure.title("Бизнес-кейс: Кнопка 'Перейти' открывает детальную страницу услуги")
def test_view_button_navigates_to_detail(guest_page: Page, services_page: ServicesPage):
    """
    Бизнес-кейс: После раскрытия пункта клик на "Перейти" переходит на
    детальную страницу услуги /services/<id>/public-view/.

    Шаги:
    1. Открыть страницу.
    2. Раскрыть первый пункт.
    3. Нажать "Перейти".

    ОР:
    - URL соответствует шаблону /registration/services/<id>/public-view/.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        services_page.navigate()

    with allure.step("Шаг 2: Раскрытие первого пункта"):
        services_page.expand_item(0)

    with allure.step("Шаг 3: Клик 'Перейти'"):
        services_page.view_buttons.first.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит /services/<id>/public-view/"):
        expect(guest_page).to_have_url(
            re.compile(r"/registration/services/\d+/public-view/")
        )


@pytest.mark.services
@allure.epic("Услуги службы занятости")
@allure.feature("Детальная страница")
@allure.title("Бизнес-кейс: Кнопка 'Назад' на детальной странице возвращает к списку услуг")
def test_back_button_returns_to_list(guest_page: Page, services_page: ServicesPage):
    """
    Бизнес-кейс: На детальной странице услуги кнопка "Назад" возвращает
    пользователя к публичному списку услуг.

    Шаги:
    1. Открыть страницу списка.
    2. Раскрыть первый пункт и нажать "Перейти".
    3. На детальной странице нажать "Назад".

    ОР:
    - URL возвращается к /registration/services/public/list/.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        services_page.navigate()

    with allure.step("Шаг 2: Раскрытие пункта и переход на детальную страницу"):
        services_page.expand_item(0)
        services_page.view_buttons.first.click()
        guest_page.wait_for_load_state("domcontentloaded")
        expect(guest_page).to_have_url(re.compile(r"/services/\d+/public-view/"))

    with allure.step("Шаг 3: Клик 'Назад'"):
        services_page.back_button.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL вернулся к списку услуг"):
        expect(guest_page).to_have_url(
            re.compile(r"/registration/services/public/list/")
        )
