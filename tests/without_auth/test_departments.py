import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.departments_page import DepartmentsPage


@pytest.mark.departments
@allure.epic("Справочник отделов занятости")
@allure.feature("Загрузка страницы")
@allure.title("Смоук: Страница отделов занятости загружается с карточками")
def test_page_loads_with_department_cards(departments_page: DepartmentsPage):
    """
    Смоук: Страница справочника отделов занятости доступна без авторизации
    и содержит карточки с кнопками навигации.

    Прекондишены:
    1. Пользователь не авторизован.

    Шаги:
    1. Открыть страницу справочника отделов.

    ОР:
    - На странице видна хотя бы одна карточка отдела.
    - Первая карточка содержит кнопки "Подробнее" и "Перейти на сайт".
    """
    with allure.step("Шаг 1: Переход на страницу"):
        departments_page.navigate()

    with allure.step("ОР: Карточки отделов и кнопки навигации видны"):
        expect(departments_page.department_cards.first).to_be_visible()
        expect(departments_page.detail_buttons.first).to_be_visible()
        expect(departments_page.site_buttons.first).to_be_visible()


@pytest.mark.departments
@allure.epic("Справочник отделов занятости")
@allure.feature("Фильтр по региону")
@allure.title("Бизнес-кейс: Фильтрация списка отделов по региону через Select2")
def test_filter_by_region_updates_url(guest_page: Page, departments_page: DepartmentsPage):
    """
    Бизнес-кейс: Выбор региона в Select2 и применение фильтра обновляет URL
    с числовым параметром region и показывает карточки.

    Шаги:
    1. Открыть страницу.
    2. Выбрать "Минск" в Select2 региона.
    3. Нажать "Поиск".

    ОР:
    - URL содержит region=<число>.
    - Карточки видны (результаты не пусты).
    """
    with allure.step("Шаг 1: Переход на страницу"):
        departments_page.navigate()

    with allure.step("Шаг 2: Выбор региона 'Минск'"):
        departments_page.select_region("Минск")

    with allure.step("Шаг 3: Применение фильтра"):
        departments_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит region=\\d+, карточки видны"):
        expect(guest_page).to_have_url(re.compile(r"region=\d+"))
        expect(departments_page.department_cards.first).to_be_visible()


@pytest.mark.departments
@allure.epic("Справочник отделов занятости")
@allure.feature("Сброс фильтра")
@allure.title("Бизнес-кейс: Кнопка 'Сбросить фильтр' возвращает к полному списку")
def test_reset_filter_clears_params(guest_page: Page, departments_page: DepartmentsPage):
    """
    Бизнес-кейс: После применения фильтра по региону кнопка "Сбросить фильтр"
    возвращает URL в исходное состояние и показывает полный список отделов.

    Шаги:
    1. Открыть страницу.
    2. Применить фильтр по региону.
    3. Нажать "Сбросить фильтр".

    ОР:
    - URL: /directory/information/employment-departments/?
    - Карточки видны.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        departments_page.navigate()

    with allure.step("Шаг 2: Применение фильтра по региону 'Минск'"):
        departments_page.select_region("Минск")
        departments_page.apply_filter_and_wait()

    with allure.step("Шаг 3: Сброс фильтра"):
        departments_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL сброшен, карточки видны"):
        expect(guest_page).to_have_url(
            "https://gsz.gov.by/directory/information/employment-departments/?"
        )
        expect(departments_page.department_cards.first).to_be_visible()


@pytest.mark.departments
@allure.epic("Справочник отделов занятости")
@allure.feature("Детальная страница")
@allure.title("Бизнес-кейс: Кнопка 'Подробнее' открывает детальную страницу отдела")
def test_detail_button_navigates_to_detail_page(guest_page: Page, departments_page: DepartmentsPage):
    """
    Бизнес-кейс: Клик на "Подробнее" первой карточки переходит на страницу
    с детальной информацией об отделе занятости.

    Шаги:
    1. Открыть страницу.
    2. Нажать "Подробнее" на первой карточке.

    ОР:
    - URL соответствует шаблону /employment-departments/<id>/detail/.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        departments_page.navigate()

    with allure.step("Шаг 2: Клик на 'Подробнее' первой карточки"):
        departments_page.detail_buttons.first.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит /employment-departments/<id>/detail/"):
        expect(guest_page).to_have_url(
            re.compile(r"employment-departments/\d+/detail/")
        )


@pytest.mark.departments
@allure.epic("Справочник отделов занятости")
@allure.feature("Внешняя ссылка")
@allure.title("Бизнес-кейс: Кнопка 'Перейти на сайт' открывается в новой вкладке")
def test_external_site_button_opens_in_new_tab(departments_page: DepartmentsPage):
    """
    Бизнес-кейс: Кнопка "Перейти на сайт" первой карточки имеет атрибут
    target='_blank' и ссылается на внешний сайт (не на gsz.gov.by).

    Шаги:
    1. Открыть страницу.
    2. Проверить атрибуты кнопки "Перейти на сайт" первой карточки.

    ОР:
    - Атрибут target="_blank" присутствует.
    - href начинается с http:// или https://.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        departments_page.navigate()

    with allure.step("ОР: Кнопка 'Перейти на сайт' имеет target='_blank' и внешний href"):
        first_site_btn = departments_page.site_buttons.first
        expect(first_site_btn).to_be_visible()
        expect(first_site_btn).to_have_attribute("target", "_blank")
        expect(first_site_btn).to_have_attribute("href", re.compile(r"^https?://"))


@pytest.mark.departments
@allure.epic("Справочник отделов занятости")
@allure.feature("Карта")
@allure.title("Бизнес-кейс: Кнопка 'Перейти к карте' переключает вид и показывает карту")
def test_map_view_toggle_shows_map(departments_page: DepartmentsPage):
    """
    Бизнес-кейс: Нажатие кнопки "Перейти к карте" показывает интерактивную
    карту с отделами занятости и меняет текст кнопки на "Перейти к списку".

    Шаги:
    1. Открыть страницу.
    2. Нажать "Перейти к карте".

    ОР:
    - Элемент карты (#map) становится видимым.
    - Текст кнопки меняется на "Перейти к списку".
    """
    with allure.step("Шаг 1: Переход на страницу"):
        departments_page.navigate()

    with allure.step("Шаг 2: Клик на 'Перейти к карте'"):
        departments_page.map_toggle_btn.click()
        departments_page._page.wait_for_timeout(800)

    with allure.step("ОР: Карта видна, кнопка сменила текст"):
        expect(departments_page.map_element).to_be_visible()
        expect(departments_page.map_toggle_btn).to_have_text(
            re.compile(r"Перейти к списку", re.IGNORECASE)
        )
