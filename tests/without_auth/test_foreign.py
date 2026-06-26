import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.foreign_page import ForeignPage


@pytest.mark.foreign_citizens
@allure.epic("Занятость иностранных граждан")
@allure.feature("Страница списка НПА для иностранных граждан")
@allure.title("Бизнес-кейс: Переход по баннеру 'Вакансии для иностранных граждан' на поиск вакансий")
def test_vacancies_banner_navigates_to_foreign_vacancy_search(guest_page: Page, foreign_page: ForeignPage):
    """
    Бизнес-кейс: Проверка работы баннера-ссылки "Вакансии для иностранных граждан".

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница занятости иностранных граждан.

    Шаги:
    1. Перейти на страницу списка НПА для иностранных граждан.
    2. Дождаться видимости баннера "Вакансии для иностранных граждан".
    3. Кликнуть по баннеру.
    4. Дождаться полной загрузки страницы поиска вакансий.

    Ожидаемый результат (ОР):
    - Пользователь переходит на страницу поиска вакансий.
    - В URL присутствует параметр for_foreigner=on, подтверждающий применённый фильтр для иностранных граждан.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание баннера"):
        foreign_page.navigate()
        foreign_page.vacancies_banner.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по баннеру 'Вакансии для иностранных граждан'"):
        foreign_page.vacancies_banner.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на страницу поиска вакансий с фильтром for_foreigner=on"):
        expect(guest_page).to_have_url(
            re.compile(r"/registration/vacancy-search/.*for_foreigner=on")
        )


@pytest.mark.foreign_citizens
@allure.epic("Занятость иностранных граждан")
@allure.feature("Страница списка НПА для иностранных граждан")
@allure.title("Бизнес-кейс: Разворачивание первого аккордеон-блока и видимость кнопок действий")
def test_first_accordion_expands_and_shows_action_buttons(guest_page: Page, foreign_page: ForeignPage):
    """
    Бизнес-кейс: Проверка раскрытия аккордеон-блока и появления кнопок "Перейти" и "Скачать".

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница занятости иностранных граждан.

    Шаги:
    1. Перейти на страницу списка НПА.
    2. Убедиться, что аккордеон-переключатели присутствуют на странице.
    3. Кликнуть по первому аккордеон-переключателю для разворачивания блока.
    4. Дождаться появления кнопок "Перейти" и "Скачать" внутри раскрытого блока.

    Ожидаемый результат (ОР):
    - После клика по заголовку аккордеона в DOM становятся видимы кнопки "Перейти" и "Скачать".
    """
    with allure.step("Шаг 1: Переход на страницу и проверка наличия аккордеон-переключателей"):
        foreign_page.navigate()
        foreign_page.accordion_toggles.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по первому аккордеон-блоку для его разворачивания"):
        foreign_page.expand_first_accordion()

    with allure.step("ОР 1: Кнопка 'Перейти' отображается внутри раскрытого блока"):
        expect(foreign_page.go_to_buttons.first).to_be_visible()

    with allure.step("ОР 2: Кнопка 'Скачать' отображается внутри раскрытого блока"):
        foreign_page.download_buttons_list.first.wait_for(state="visible", timeout=3000)
        expect(foreign_page.download_buttons_list.first).to_be_visible()


@pytest.mark.foreign_citizens
@allure.epic("Занятость иностранных граждан")
@allure.feature("Страница списка НПА для иностранных граждан")
@allure.title("Бизнес-кейс: Переход на детальную страницу НПА по кнопке 'Перейти'")
def test_go_to_button_opens_detail_page(guest_page: Page, foreign_page: ForeignPage):
    """
    Бизнес-кейс: Проверка перехода на детальную страницу НПА по кнопке "Перейти" из аккордеон-блока.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница занятости иностранных граждан.

    Шаги:
    1. Перейти на страницу списка НПА.
    2. Развернуть первый аккордеон-блок.
    3. Извлечь href кнопки "Перейти" для последующей верификации целевого URL.
    4. Кликнуть по кнопке "Перейти".
    5. Дождаться полной загрузки детальной страницы.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу вида /foreign-citizens-employment/{id}/public-view/.
    - URL текущей страницы совпадает с извлечённым href кнопки "Перейти".
    """
    with allure.step("Шаг 1: Переход на страницу и разворачивание первого аккордеона"):
        foreign_page.navigate()
        foreign_page.expand_first_accordion()

    with allure.step("Шаг 2: Извлечение ожидаемого URL кнопки 'Перейти'"):
        expected_href = foreign_page.go_to_buttons.first.get_attribute("href")
        expected_url = f"https://gsz.gov.by{expected_href}" if expected_href.startswith("/") else expected_href

    with allure.step("Шаг 3: Клик по кнопке 'Перейти' на первом блоке"):
        foreign_page.go_to_buttons.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на детальную страницу НПА"):
        expect(guest_page).to_have_url(
            re.compile(r"/registration/foreign-citizens-employment/\d+/public-view/")
        )
        expect(guest_page).to_have_url(expected_url)


@pytest.mark.foreign_citizens
@allure.epic("Занятость иностранных граждан")
@allure.feature("Страница списка НПА для иностранных граждан")
@allure.title("Бизнес-кейс: Скачивание файла НПА через кнопку 'Скачать' на странице списка")
def test_download_button_on_list_page_starts_download(guest_page: Page, foreign_page: ForeignPage):
    """
    Бизнес-кейс: Проверка инициации скачивания файла НПА через кнопку "Скачать" на странице списка.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница занятости иностранных граждан.

    Шаги:
    1. Перейти на страницу списка НПА.
    2. Развернуть первый аккордеон-блок.
    3. Кликнуть по кнопке "Скачать" (стиль btn-outline-primary).
    4. Дождаться события инициирования скачивания файла.

    Ожидаемый результат (ОР):
    - Браузер инициирует скачивание файла.
    - Имя предлагаемого файла соответствует PDF-документу.
    """
    with allure.step("Шаг 1: Переход на страницу и разворачивание первого аккордеона"):
        foreign_page.navigate()
        foreign_page.expand_first_accordion()

    with allure.step("Шаг 2: Клик по кнопке 'Скачать' с перехватом события скачивания"):
        foreign_page.download_buttons_list.first.wait_for(state="visible", timeout=3000)
        with guest_page.expect_download(timeout=15000) as download_info:
            foreign_page.download_buttons_list.first.click()
        download = download_info.value

    with allure.step("ОР 1: Верификация инициирования скачивания PDF-файла"):
        assert download.suggested_filename, "Ошибка: браузер не получил имя скачиваемого файла"
        assert download.suggested_filename.endswith(".pdf"), (
            f"Ошибка: ожидался PDF-файл, получен '{download.suggested_filename}'"
        )


@pytest.mark.foreign_citizens
@allure.epic("Занятость иностранных граждан")
@allure.feature("Детальная страница НПА для иностранных граждан")
@allure.title("Бизнес-кейс: Скачивание файла НПА через кнопку 'Скачать' на детальной странице")
def test_download_button_on_detail_page_starts_download(guest_page: Page, foreign_page: ForeignPage):
    """
    Бизнес-кейс: Проверка инициации скачивания файла НПА через кнопку "Скачать" на детальной странице.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница занятости иностранных граждан.

    Шаги:
    1. Перейти на страницу списка НПА.
    2. Развернуть первый аккордеон-блок.
    3. Кликнуть по кнопке "Перейти" для перехода на детальную страницу.
    4. На детальной странице кликнуть по кнопке "Скачать" (стиль btn-primary).
    5. Дождаться события инициирования скачивания файла.

    Ожидаемый результат (ОР):
    - Браузер инициирует скачивание файла с детальной страницы НПА.
    - Имя предлагаемого файла соответствует PDF-документу.
    """
    with allure.step("Шаг 1: Переход на страницу, разворачивание аккордеона и переход на детальную страницу"):
        foreign_page.navigate()
        foreign_page.expand_first_accordion()
        foreign_page.go_to_buttons.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("Шаг 2: Верификация нахождения на детальной странице НПА"):
        expect(guest_page).to_have_url(
            re.compile(r"/registration/foreign-citizens-employment/\d+/public-view/")
        )

    with allure.step("Шаг 3: Ожидание кнопки 'Скачать' на детальной странице"):
        foreign_page.download_button_detail.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 4: Клик по кнопке 'Скачать' с перехватом события скачивания"):
        with guest_page.expect_download(timeout=15000) as download_info:
            foreign_page.download_button_detail.click()
        download = download_info.value

    with allure.step("ОР 1: Верификация инициирования скачивания PDF-файла с детальной страницы"):
        assert download.suggested_filename, "Ошибка: браузер не получил имя скачиваемого файла"
        assert download.suggested_filename.endswith(".pdf"), (
            f"Ошибка: ожидался PDF-файл, получен '{download.suggested_filename}'"
        )
