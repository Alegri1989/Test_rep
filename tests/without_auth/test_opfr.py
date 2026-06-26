import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.opfr_page import OpfrPage


@pytest.mark.opfr
@allure.title("Бизнес-кейс: Переключение в режим документов и скачивание файла")
def test_guest_toggle_to_documents_and_download(guest_page: Page, opfr_page: OpfrPage):
    """
    Бизнес-кейс: Проверка переключения вида страницы на список документов и скачивания файла.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница ОПФР-организаций.

    Шаги:
    1. Перейти на страницу и дождаться кнопки "Перейти к документам".
    2. Кликнуть по кнопке переключения вида.
    3. Дождаться появления кнопки "Скачать".
    4. Кликнуть по кнопке "Скачать" и перехватить событие скачивания.

    Ожидаемый результат (ОР):
    - После клика по переключателю появляется кнопка "Скачать" в списке документов.
    - Браузер инициирует скачивание файла с непустым именем.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание кнопки переключения вида"):
        opfr_page.navigate()
        opfr_page.toggle_view_btn.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Перейти к документам'"):
        opfr_page.toggle_view_btn.click()

    with allure.step("Шаг 3: Ожидание появления кнопки 'Скачать' в режиме документов"):
        opfr_page.download_btn.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 4: Клик по кнопке 'Скачать' с перехватом события скачивания"):
        with guest_page.expect_download(timeout=15000) as download_info:
            opfr_page.download_btn.first.click()
        download = download_info.value

    with allure.step("ОР 1: Верификация инициирования скачивания файла"):
        assert download.suggested_filename, "Ошибка: браузер не получил имя скачиваемого файла"


@pytest.mark.opfr
@allure.title("Бизнес-кейс: Переход на детальную страницу организации по кнопке 'Подробнее'")
def test_guest_navigate_to_org_detail_via_detail_btn(guest_page: Page, opfr_page: OpfrPage):
    """
    Бизнес-кейс: Проверка перехода на детальную страницу ОПФР-организации по кнопке "Подробнее".

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница ОПФР-организаций.

    Шаги:
    1. Перейти на страницу и дождаться видимости кнопки "Подробнее" на первой карточке.
    2. Сохранить href кнопки для верификации целевого URL.
    3. Кликнуть по кнопке "Подробнее".
    4. Дождаться полной загрузки детальной страницы организации.

    Ожидаемый результат (ОР):
    - Пользователь переходит на страницу вида /registration/opfr_organisations/{id}/list/.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание кнопки 'Подробнее'"):
        opfr_page.navigate()
        opfr_page.detail_btn.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Извлечение ожидаемого URL кнопки 'Подробнее'"):
        expected_href = opfr_page.detail_btn.first.get_attribute("href")
        expected_url = f"https://gsz.gov.by{expected_href}" if expected_href.startswith("/") else expected_href

    with allure.step("Шаг 3: Клик по кнопке 'Подробнее' на первой карточке"):
        opfr_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на детальную страницу организации"):
        expect(guest_page).to_have_url(re.compile(r"/registration/opfr_organisations/\d+/list/"))
        expect(guest_page).to_have_url(expected_url)


@pytest.mark.opfr
@allure.title("Бизнес-кейс: Фильтрация организаций по наименованию")
def test_guest_filter_by_org_name(guest_page: Page, opfr_page: OpfrPage):
    """
    Бизнес-кейс: Проверка работы текстового фильтра по наименованию ОПФР-организации.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница ОПФР-организаций.

    Шаги:
    1. Перейти на страницу.
    2. Ввести в поле "Наименование организации" поисковый запрос "Скидельский".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что в выдаче присутствуют карточки и их наименования содержат поисковый запрос.

    Ожидаемый результат (ОР):
    - Выдача после фильтрации содержит только организации, в наименовании которых есть "Скидельский".
    - URL содержит параметр name= с поисковым запросом.
    """
    search_term = "Скидельский"

    with allure.step("Шаг 1: Переход на страницу"):
        opfr_page.navigate()

    with allure.step(f"Шаг 2: Ввод поискового запроса '{search_term}' в поле наименования"):
        opfr_page.name_filter_input.wait_for(state="visible", timeout=5000)
        opfr_page.name_filter_input.fill(search_term)

    with allure.step("Шаг 3: Применение фильтра"):
        opfr_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация параметра name в URL"):
        expect(guest_page).to_have_url(re.compile(r"name="))

    with allure.step("ОР 2: Верификация наличия результатов и соответствия поисковому запросу"):
        opfr_page.org_title_link.first.wait_for(state="visible", timeout=5000)
        count = opfr_page.org_title_link.count()
        assert count > 0, f"Ошибка: фильтрация по '{search_term}' вернула пустой список организаций"

        for i in range(count):
            title_text = opfr_page.org_title_link.nth(i).text_content().strip()
            assert search_term.lower() in title_text.lower(), (
                f"Ошибка: на позиции {i + 1} найдена организация '{title_text}', "
                f"не содержащая '{search_term}'"
            )


@pytest.mark.opfr
@allure.title("Бизнес-кейс: Фильтрация организаций по региону")
def test_guest_filter_by_region(guest_page: Page, opfr_page: OpfrPage):
    """
    Бизнес-кейс: Проверка работы фильтра региона через Select2-виджет.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница ОПФР-организаций.

    Шаги:
    1. Перейти на страницу.
    2. Выбрать в Select2-фильтре региона значение "Минск".
    3. Применить фильтрацию нажатием кнопки "Поиск".

    Ожидаемый результат (ОР):
    - Select2 принимает выбранное значение и отображает его в контейнере.
    - URL после применения фильтра содержит параметр region=.
    """
    region = "Минск"

    with allure.step("Шаг 1: Переход на страницу"):
        opfr_page.navigate()

    with allure.step(f"Шаг 2: Выбор региона '{region}' в Select2-виджете"):
        opfr_page.region_select2_container.wait_for(state="visible", timeout=5000)
        opfr_page.select_region(region)

    with allure.step("ОР 1: Верификация отображения выбранного региона в Select2-контейнере"):
        expect(opfr_page.region_select2_container).to_have_text(region)

    with allure.step("Шаг 3: Применение фильтра"):
        opfr_page.apply_filter_and_wait()

    with allure.step("ОР 2: Верификация параметра region в URL"):
        expect(guest_page).to_have_url(re.compile(r"region="))


@pytest.mark.opfr
@allure.title("Бизнес-кейс: Сброс установленных фильтров организаций")
def test_guest_reset_applied_filters(guest_page: Page, opfr_page: OpfrPage):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных поисковых фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница ОПФР-организаций.

    Шаги:
    1. Перейти на страницу, ввести наименование "Скидельский" и применить фильтр.
    2. Кликнуть по кнопке "Сбросить фильтр".
    3. Верифицировать возврат к дефолтному URL и очистку поля наименования.

    Ожидаемый результат (ОР):
    - Страница перезагружается на дефолтный URL со знаком вопроса.
    - Поле наименования организации очищено.
    """
    with allure.step("Шаг 1: Переход на страницу, ввод наименования и применение фильтра"):
        opfr_page.navigate()
        opfr_page.name_filter_input.wait_for(state="visible", timeout=5000)
        opfr_page.name_filter_input.fill("Скидельский")
        opfr_page.apply_filter_and_wait()

    with allure.step("Шаг 2: Нажатие на кнопку 'Сбросить фильтр' и ожидание обновления страницы"):
        opfr_page.reset_filter_btn.wait_for(state="visible", timeout=5000)
        opfr_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация возврата к дефолтному URL"):
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/opfr_organisations/public-list/?")

    with allure.step("ОР 2: Верификация очистки поля наименования организации"):
        expect(opfr_page.name_filter_input).to_have_value("")


@pytest.mark.opfr
@allure.title("Бизнес-кейс: Переход на детальную страницу организации по клику на её наименование")
def test_guest_navigate_to_org_detail_via_title_link(guest_page: Page, opfr_page: OpfrPage):
    """
    Бизнес-кейс: Проверка перехода на детальную страницу ОПФР-организации по клику на её наименование.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница ОПФР-организаций.

    Шаги:
    1. Перейти на страницу и дождаться видимости ссылки-наименования первой карточки.
    2. Сохранить href ссылки для верификации целевого URL.
    3. Кликнуть по наименованию организации.
    4. Дождаться полной загрузки детальной страницы.

    Ожидаемый результат (ОР):
    - Пользователь переходит на страницу вида /registration/opfr_organisations/{id}/list/.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание ссылки-наименования первой карточки"):
        opfr_page.navigate()
        opfr_page.org_title_link.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Извлечение ожидаемого URL ссылки-наименования"):
        expected_href = opfr_page.org_title_link.first.get_attribute("href")
        expected_url = f"https://gsz.gov.by{expected_href}" if expected_href.startswith("/") else expected_href

    with allure.step("Шаг 3: Клик по наименованию организации"):
        opfr_page.org_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на детальную страницу организации"):
        expect(guest_page).to_have_url(re.compile(r"/registration/opfr_organisations/\d+/list/"))
        expect(guest_page).to_have_url(expected_url)
