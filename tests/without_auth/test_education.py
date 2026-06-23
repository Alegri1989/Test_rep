import datetime
import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.education_page import EducationPage

RU_MONTH_NAMES = {
    1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
    7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь",
}


def assert_current_month_in_all_group_forming_cards(education_page: EducationPage):
    """Проверяет, что текущий месяц фигурирует в планируемом формировании группы во всех карточках выдачи."""
    education_page.group_forming_value.first.wait_for(state="visible", timeout=5000)

    count = education_page.group_forming_value.count()
    assert count > 0, "Ошибка: фильтрация вернула пустой список курсов обучения"

    current_month_name = RU_MONTH_NAMES[datetime.date.today().month]
    for i in range(count):
        group_text = education_page.group_forming_value.nth(i).text_content().strip().lower()
        assert current_month_name in group_text, (
            f"Ошибка: на позиции {i + 1} текущий месяц '{current_month_name}' "
            f"не найден среди месяцев формирования группы '{group_text}'"
        )


@pytest.mark.education
@allure.title("Бизнес-кейс: Фильтрация курсов обучения по Региону")
def test_guest_filter_by_region(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка работы фильтра региона обучения, скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Регион обучения".
    2. Выбрать в обычном select значение "Минск".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что во всех карточках выдачи указан выбранный регион обучения.

    Ожидаемый результат (ОР):
    - Скрытый спойлер успешно раскрывается, select принимает выбор без Select2.
    - Выдача после фильтрации содержит только курсы обучения с регионом "Минск".
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Регион обучения'"):
        education_page.navigate()
        education_page.open_spoiler_if_hidden(education_page.region_filter_title, education_page.region_select)

    with allure.step("Шаг 2: Выбор региона 'Минск'"):
        education_page.region_select.select_option(label="Минск")

    with allure.step("Шаг 3: Применение фильтра"):
        education_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация выбранного региона во всех карточках результатов"):
        education_page.region_value.first.wait_for(state="visible", timeout=5000)

        count = education_page.region_value.count()
        assert count > 0, "Ошибка: фильтрация по региону вернула пустой список курсов обучения"

        for i in range(count):
            region_text = education_page.region_value.nth(i).text_content().strip()
            assert region_text == "Минск", (
                f"Ошибка: на позиции {i + 1} найден курс обучения с чужим регионом '{region_text}'"
            )


@pytest.mark.education
@allure.title("Бизнес-кейс: Фильтрация курсов обучения по текущему месяцу Периода обучения")
def test_guest_filter_by_period_current_month(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка работы фильтра периода обучения через датапикер, скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Период обучения".
    2. Открыть датапикер и выбрать текущий выделенный (focused) месяц.
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что во всех карточках выдачи в планируемом формировании группы фигурирует текущий месяц.

    Ожидаемый результат (ОР):
    - Датапикер открывается в режиме выбора месяца и принимает клик по текущему месяцу.
    - Выдача после фильтрации содержит только курсы, формирующие группу в текущем месяце.
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Период обучения'"):
        education_page.navigate()
        education_page.open_spoiler_if_hidden(
            education_page.period_filter_title, education_page.period_start_input
        )

    with allure.step("Шаг 2: Выбор текущего месяца в датапикере"):
        education_page.select_current_month_in_period_datepicker()

    with allure.step("Шаг 3: Применение фильтра"):
        education_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация наличия текущего месяца в планируемом формировании группы"):
        assert_current_month_in_all_group_forming_cards(education_page)


@pytest.mark.education
@allure.title("Бизнес-кейс: Фильтрация курсов обучения по признаку 'группа формируется'")
def test_guest_filter_by_start_when_full(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка работы чекбокса-фильтра "группа формируется", скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Период обучения".
    2. Кликнуть по текстовому лейблу чекбокса "группа формируется".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Раскрыть спойлер повторно и проверить, что чекбокс остался отмеченным после перезагрузки.
    5. Проверить, что во всех карточках выдачи в планируемом формировании группы фигурирует текущий месяц.

    Ожидаемый результат (ОР):
    - Чекбокс успешно активируется по клику на лейбл, в URL фиксируется параметр start_when_full.
    - Состояние чекбокса сохраняется после применения фильтра.
    - Выдача после фильтрации содержит только курсы, формирующие группу в текущем месяце
      (на момент написания теста чекбокс на бэкенде эквивалентен фильтрации по текущему месяцу).
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Период обучения'"):
        education_page.navigate()
        education_page.open_spoiler_if_hidden(
            education_page.period_filter_title, education_page.start_when_full_label
        )

    with allure.step("Шаг 2: Клик по чекбоксу 'группа формируется'"):
        education_page.start_when_full_label.click()
        assert education_page.start_when_full_checkbox.is_checked(), "Ошибка: чекбокс не отметился по клику на лейбл"

    with allure.step("Шаг 3: Применение фильтра"):
        education_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация сохранения состояния чекбокса после применения фильтра"):
        expect(guest_page).to_have_url(re.compile(r"start_when_full=on"))
        education_page.open_spoiler_if_hidden(
            education_page.period_filter_title, education_page.start_when_full_label
        )
        assert education_page.start_when_full_checkbox.is_checked(), "Ошибка: чекбокс сбросился после применения фильтра"

    with allure.step("ОР 2: Верификация наличия текущего месяца в планируемом формировании группы"):
        assert_current_month_in_all_group_forming_cards(education_page)


@pytest.mark.education
@allure.title("Бизнес-кейс: Сброс установленных фильтров курсов обучения")
def test_guest_reset_applied_filters(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных поисковых фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения.

    Шаги:
    1. Открыть страницу, раскрыть спойлер региона и выбрать значение "Минск".
    2. Применить фильтр нажатием кнопки "Поиск".
    3. Кликнуть по кнопке "Сбросить фильтр".
    4. Раскрыть спойлер региона повторно и верифицировать возврат к значению "Любой" и дефолтному URL.

    Ожидаемый результат (ОР):
    - Система выполняет перезагрузку страницы и возвращает пользователя на дефолтный URL со знаком вопроса.
    - Ранее выбранный регион сбрасывается до значения "Любой".
    """
    with allure.step("Шаг 1: Переход на страницу, раскрытие спойлера и выбор региона 'Минск'"):
        education_page.navigate()
        education_page.open_spoiler_if_hidden(education_page.region_filter_title, education_page.region_select)
        education_page.region_select.select_option(label="Минск")

    with allure.step("Шаг 2: Применение фильтра"):
        education_page.apply_filter_and_wait()

    with allure.step("Шаг 3: Нажатие на кнопку 'Сбросить фильтр' и ожидание обновления страницы"):
        education_page.reset_filter_btn.wait_for(state="visible", timeout=5000)
        education_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация сброса региона до значения 'Любой' и возврата к дефолтному URL"):
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/training-course/public/list/?")
        education_page.open_spoiler_if_hidden(education_page.region_filter_title, education_page.region_select)
        expect(education_page.region_select).to_have_value("0")


@pytest.mark.education
@allure.title("Бизнес-кейс: Переход на детальную страницу курса обучения по кнопке 'Подробнее'")
def test_guest_navigate_to_detail_via_button(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка перехода на детальную страницу курса обучения по кнопке "Подробнее".

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения.

    Шаги:
    1. Перейти на страницу и дождаться видимости кнопки "Подробнее" на первой карточке.
    2. Кликнуть по кнопке.
    3. Дождаться полной загрузки детальной страницы курса обучения.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу вида /registration/training-course/{id}/public-view/.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание кнопки 'Подробнее'"):
        education_page.navigate()
        education_page.detail_btn.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Подробнее' на первой карточке"):
        education_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на детальную страницу курса обучения"):
        expect(guest_page).to_have_url(re.compile(r"/registration/training-course/\d+/public-view/"))


@pytest.mark.education
@allure.title("Бизнес-кейс: Переход по кнопке 'Контактные данные службы занятости' с карточки курса обучения")
def test_guest_navigate_to_employment_departments_via_contact_link(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка перехода на страницу контактных данных службы занятости по кнопке с карточки.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения.

    Шаги:
    1. Перейти на страницу и дождаться видимости кнопки "Контактные данные службы занятости".
    2. Кликнуть по кнопке (открывается в новой вкладке).
    3. Дождаться полной загрузки открывшейся вкладки.

    Ожидаемый результат (ОР):
    - В новой вкладке открывается страница вида /directory/information/employment-departments/.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание кнопки контактных данных"):
        education_page.navigate()
        education_page.contact_link.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Контактные данные службы занятости'"):
        with guest_page.expect_popup() as popup_info:
            education_page.contact_link.first.click()
        popup = popup_info.value
        popup.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация открытия страницы контактных данных службы занятости"):
        expect(popup).to_have_url(re.compile(r"/directory/information/employment-departments/"))
        popup.close()


@pytest.mark.education
@allure.title("Бизнес-кейс: Постраничная навигация по курсам обучения (вперед на страницу 2, назад на страницу 1)")
def test_guest_pagination_forward_and_back(guest_page: Page, education_page: EducationPage):
    """
    Бизнес-кейс: Проверка корректности постраничной навигации по выдаче курсов обучения.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница обучения, выдача содержит больше одной страницы.

    Шаги:
    1. Открыть страницу и кликнуть по ссылке на вторую страницу пагинации.
    2. Верифицировать, что активный номер страницы стал равен "2".
    3. Кликнуть по стрелке "назад" (caret-left).
    4. Верифицировать возврат на первую страницу выдачи.

    Ожидаемый результат (ОР):
    - Постраничная навигация корректно переключает выдачу как вперед, так и назад.
    """
    with allure.step("Шаг 1: Переход на страницу и клик по ссылке второй страницы пагинации"):
        education_page.navigate()
        education_page.page_2_link.wait_for(state="visible", timeout=5000)
        education_page.page_2_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация активной второй страницы"):
        expect(education_page.active_page_number).to_have_text("2")
        education_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по стрелке 'назад'"):
        education_page.back_arrow_btn.wait_for(state="visible", timeout=5000)
        education_page.back_arrow_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 2: Верификация возврата на первую страницу"):
        expect(education_page.active_page_number).to_have_text("1")
        education_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
