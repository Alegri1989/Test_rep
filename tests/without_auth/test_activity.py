import re
from urllib.parse import quote
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.activity_page import ActivityPage


@pytest.mark.activity
@allure.epic("Мероприятия")
@allure.feature("Загрузка страницы")
@allure.title("Смоук: Страница мероприятий загружается с карточками")
def test_page_loads_with_activity_cards(activity_page: ActivityPage):
    """
    Смоук: Публичный список мероприятий доступен без авторизации
    и содержит хотя бы одну карточку.

    Прекондишены:
    1. Пользователь не авторизован.

    Шаги:
    1. Открыть страницу списка мероприятий.

    ОР:
    - На странице присутствует хотя бы одна ссылка-карточка мероприятия.
    - Кнопка поиска и select сортировки видны.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        activity_page.navigate()

    with allure.step("ОР: Карточки и элементы управления видны"):
        expect(activity_page.activity_links.first).to_be_visible()
        expect(activity_page.search_btn).to_be_visible()
        expect(activity_page.sort_select).to_be_visible()


@pytest.mark.activity
@allure.epic("Мероприятия")
@allure.feature("Фильтр по региону")
@allure.title("Бизнес-кейс: Фильтрация мероприятий по региону через нативный select")
def test_filter_by_region_native_select(guest_page: Page, activity_page: ActivityPage):
    """
    Бизнес-кейс: Выбор региона из нативного select и применение фильтра
    обновляет URL с параметром activity_region.

    Шаги:
    1. Открыть страницу.
    2. Выбрать "Минск" (value=7) в select региона.
    3. Нажать "Поиск".

    ОР:
    - URL содержит activity_region=7.
    - Карточки мероприятий видны.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        activity_page.navigate()

    with allure.step("Шаг 2: Выбор региона 'Минск'"):
        activity_page.region_select.select_option("7")

    with allure.step("Шаг 3: Применение фильтра"):
        activity_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит activity_region=7, карточки видны"):
        expect(guest_page).to_have_url(re.compile(r"activity_region=7"))
        expect(activity_page.activity_links.first).to_be_visible()


@pytest.mark.activity
@allure.epic("Мероприятия")
@allure.feature("Фильтр по заголовку")
@allure.title("Бизнес-кейс: Фильтрация мероприятий по ключевому слову в заголовке")
def test_filter_by_description_text(guest_page: Page, activity_page: ActivityPage):
    """
    Бизнес-кейс: Ввод текста в поле "Наименование (заголовок)" и применение
    фильтра обновляет URL с параметром description.

    Шаги:
    1. Открыть страницу.
    2. Ввести текст в поле заголовка.
    3. Нажать "Поиск".

    ОР:
    - URL содержит параметр description с введённым значением (URL-encoded).
    """
    search_term = "Ярмарка"

    with allure.step("Шаг 1: Переход на страницу"):
        activity_page.navigate()

    with allure.step(f"Шаг 2: Ввод текста '{search_term}' в поле заголовка"):
        activity_page.description_input.fill(search_term)

    with allure.step("Шаг 3: Применение фильтра"):
        activity_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит description с введённым значением"):
        expect(guest_page).to_have_url(
            re.compile(rf"description={re.escape(quote(search_term))}", re.IGNORECASE)
        )


@pytest.mark.activity
@allure.epic("Мероприятия")
@allure.feature("Сортировка")
@allure.title("Бизнес-кейс: Изменение сортировки обновляет URL (submit-on-change)")
def test_sort_by_changes_url(guest_page: Page, activity_page: ActivityPage):
    """
    Бизнес-кейс: Select сортировки имеет класс submit-on-change — при смене
    значения форма отправляется автоматически без нажатия "Поиск".

    Шаги:
    1. Открыть страницу (по умолчанию sort_by=sort_published_at_desc).
    2. Изменить сортировку на "по возрастанию".

    ОР:
    - URL содержит sort_by=sort_published_at_asc.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        activity_page.navigate()

    with allure.step("Шаг 2: Смена сортировки на 'по возрастанию'"):
        activity_page.sort_select.select_option("sort_published_at_asc")
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит sort_by=sort_published_at_asc"):
        expect(guest_page).to_have_url(re.compile(r"sort_by=sort_published_at_asc"))


@pytest.mark.activity
@allure.epic("Мероприятия")
@allure.feature("Детальная страница")
@allure.title("Бизнес-кейс: Клик по карточке мероприятия открывает страницу просмотра")
def test_activity_card_opens_public_view(guest_page: Page, activity_page: ActivityPage):
    """
    Бизнес-кейс: Клик по ссылке карточки (a.news__link) переходит на
    детальную страницу мероприятия /activity/<id>/public-view/.

    Шаги:
    1. Открыть страницу списка мероприятий.
    2. Кликнуть по первой карточке.

    ОР:
    - URL соответствует шаблону /registration/activity/<id>/public-view/.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        activity_page.navigate()

    with allure.step("Шаг 2: Клик по первой карточке мероприятия"):
        activity_page.activity_links.first.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит /activity/<id>/public-view/"):
        expect(guest_page).to_have_url(
            re.compile(r"/registration/activity/\d+/public-view/")
        )


@pytest.mark.activity
@allure.epic("Мероприятия")
@allure.feature("Фильтр по дате")
@allure.title("Бизнес-кейс: Фильтрация мероприятий по дате публикации (YYYY-MM)")
def test_filter_by_publication_date(guest_page: Page, activity_page: ActivityPage):
    """
    Бизнес-кейс: Фильтр по дате публикации принимает формат YYYY-MM и передаёт
    его в URL. Дата берётся динамически из первой карточки, чтобы гарантировать
    наличие результатов.

    Шаги:
    1. Открыть страницу, считать дату первой карточки (DD.MM.YYYY).
    2. Преобразовать в YYYY-MM и установить через JS (поле readonly, датпикер не нужен).
    3. Нажать "Поиск".

    ОР:
    - URL содержит publication_date=YYYY-MM.
    - Карточки мероприятий видны.
    """
    with allure.step("Шаг 1: Переход на страницу, считываем дату первой карточки"):
        activity_page.navigate()
        date_text = guest_page.locator(".news__date").first.inner_text().strip()
        # DD.MM.YYYY → YYYY-MM
        parts = date_text.split(".")
        year_month = f"{parts[2]}-{parts[1]}"

    with allure.step(f"Шаг 2: Установка фильтра даты '{year_month}'"):
        activity_page.set_publication_date(year_month)

    with allure.step("Шаг 3: Применение фильтра"):
        activity_page.apply_filter_and_wait()

    with allure.step(f"ОР: URL содержит publication_date={year_month}, карточки видны"):
        expect(guest_page).to_have_url(
            re.compile(rf"publication_date={re.escape(year_month)}")
        )
        expect(activity_page.activity_links.first).to_be_visible()
