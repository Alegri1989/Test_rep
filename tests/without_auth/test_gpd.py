import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.gpd_page import GpdPage


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Фильтрация работ по ГПД по Сфере деятельности")
def test_guest_filter_by_sphere_of_activity(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка работы множественного фильтра сферы деятельности, скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Сфера деятельности".
    2. Выбрать через Select2 значение "Работы, не требующие квалификации".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что во всех карточках выдачи указана выбранная сфера деятельности.

    Ожидаемый результат (ОР):
    - Скрытый спойлер успешно раскрывается, множественный Select2 принимает посимвольный ввод.
    - Выдача после фильтрации содержит только работы выбранной сферы деятельности.
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Сфера деятельности'"):
        gpd_page.navigate()
        gpd_page.open_spoiler_if_hidden(gpd_page.sphere_filter_title, gpd_page.sphere_search_field)

    with allure.step("Шаг 2: Выбор сферы деятельности через Select2"):
        gpd_page.select_from_multiselect(gpd_page.sphere_search_field, "Работы, не требующие квалификации")

    with allure.step("Шаг 3: Применение фильтра"):
        gpd_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация выбранной сферы деятельности во всех карточках результатов"):
        gpd_page.sphere_value.first.wait_for(state="visible", timeout=5000)

        count = gpd_page.sphere_value.count()
        assert count > 0, "Ошибка: фильтрация по сфере деятельности вернула пустой список работ"

        for i in range(count):
            sphere_text = gpd_page.sphere_value.nth(i).text_content().strip()
            assert "Работы, не требующие квалификации" in sphere_text, (
                f"Ошибка: на позиции {i + 1} найдена работа с чужой сферой деятельности '{sphere_text}'"
            )


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Фильтрация работ по Предмету гражданско-правового договора")
def test_guest_filter_by_type_gpd(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка работы фильтра-чекбоксов предмета гражданско-правового договора.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Предмет гражданско-правового договора".
    2. Кликнуть по текстовому лейблу чекбокса "Выполнение работ".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что во всех карточках выдачи указан выбранный предмет договора.

    Ожидаемый результат (ОР):
    - Скрытый спойлер с чекбоксами успешно раскрывается по клику на заголовок.
    - Выдача после фильтрации содержит только работы с выбранным предметом договора "Выполнение работ".
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Предмет гражданско-правового договора'"):
        gpd_page.navigate()
        gpd_page.open_spoiler_if_hidden(gpd_page.type_gpd_filter_title, gpd_page.type_gpd_work_label)

    with allure.step("Шаг 2: Клик по чекбоксу 'Выполнение работ'"):
        gpd_page.type_gpd_work_label.click()

    with allure.step("Шаг 3: Применение фильтра"):
        gpd_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация выбранного предмета договора во всех карточках результатов"):
        gpd_page.type_gpd_value.first.wait_for(state="visible", timeout=5000)

        count = gpd_page.type_gpd_value.count()
        assert count > 0, "Ошибка: фильтрация по предмету договора вернула пустой список работ"

        for i in range(count):
            type_text = gpd_page.type_gpd_value.nth(i).text_content().strip()
            assert "Выполнение работ" in type_text, (
                f"Ошибка: на позиции {i + 1} найдена работа с чужим предметом договора '{type_text}'"
            )


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Фильтрация работ по ГПД по Нанимателю")
def test_guest_filter_by_employer(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка работы множественного фильтра по нанимателю, скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам, на ней есть хотя бы одна вакансия.

    Шаги:
    1. Перейти на страницу и зафиксировать название нанимателя из первой карточки выдачи.
    2. Раскрыть скрытый спойлер блока "Наниматель".
    3. Выбрать зафиксированного нанимателя через множественный Select2.
    4. Применить фильтрацию нажатием кнопки "Поиск".
    5. Проверить, что все карточки результатов принадлежат выбранному нанимателю.

    Ожидаемый результат (ОР):
    - Выдача после фильтрации содержит только вакансии выбранного нанимателя.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация нанимателя первой карточки"):
        gpd_page.navigate()
        gpd_page.organization_link.first.wait_for(state="visible", timeout=5000)
        employer_name = gpd_page.organization_link.first.text_content().strip()

    with allure.step("Шаг 2: Раскрытие спойлера фильтра 'Наниматель'"):
        gpd_page.open_spoiler_if_hidden(gpd_page.employer_filter_title, gpd_page.employer_search_field)

    with allure.step("Шаг 3: Выбор зафиксированного нанимателя через Select2"):
        gpd_page.select_from_multiselect(gpd_page.employer_search_field, employer_name)

    with allure.step("Шаг 4: Применение фильтра"):
        gpd_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация принадлежности всех карточек выбранному нанимателю"):
        gpd_page.organization_link.first.wait_for(state="visible", timeout=5000)

        count = gpd_page.organization_link.count()
        assert count > 0, "Ошибка: фильтрация по нанимателю вернула пустой список работ"

        for i in range(count):
            card_employer = gpd_page.organization_link.nth(i).text_content().strip()
            assert card_employer == employer_name, (
                f"Ошибка: на позиции {i + 1} найдена работа чужого нанимателя '{card_employer}'"
            )


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Фильтрация работ по ГПД по минимальной Заработной плате")
def test_guest_filter_by_min_salary(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка работы числового фильтра минимальной планки заработной платы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Открыть страницу и заполнить инпут "Заработная плата от" значением "500".
    2. Применить фильтр нажатием кнопки "Поиск".
    3. Проверить, что доход на всех карточках выдачи не ниже установленной планки.

    Ожидаемый результат (ОР):
    - Система корректно отсекает вакансии, доход по которым ниже установленного лимита в 500 рублей.
    """
    with allure.step("Шаг 1: Переход на страницу и заполнение поля 'Заработная плата от'"):
        gpd_page.navigate()
        gpd_page.salary_min_input.wait_for(state="visible", timeout=5000)
        gpd_page.salary_min_input.click()
        gpd_page.salary_min_input.fill("500")

    with allure.step("Шаг 2: Применение фильтра"):
        gpd_page.apply_filter_and_wait()

    with allure.step("ОР 1: Проверка соответствия уровня зарплаты на всех карточках страницы"):
        gpd_page.salary_value.first.wait_for(state="visible", timeout=5000)

        count = gpd_page.salary_value.count()
        assert count > 0, "Ошибка: фильтрация по зарплате вернула пустой список работ"

        for i in range(count):
            salary_text = gpd_page.salary_value.nth(i).text_content().replace(" ", "").replace("\xa0", "")
            numbers = re.findall(r"[\d.,]+", salary_text)
            assert numbers, f"Ошибка: не удалось распарсить зарплату '{salary_text}' на позиции {i + 1}"

            salary_value = float(numbers[0].replace(",", "."))
            assert salary_value >= 500, (
                f"Ошибка: на позиции {i + 1} найдена работа с неподходящей зарплатой: {salary_value}"
            )


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Сброс установленных фильтров работ по ГПД")
def test_guest_reset_applied_filters(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных поисковых фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Открыть страницу и заполнить инпут "Заработная плата от" значением "500".
    2. Применить фильтр нажатием кнопки "Поиск".
    3. Кликнуть по кнопке "Сбросить фильтр".
    4. Верифицировать очистку поля и возврат к дефолтному URL со знаком вопроса.

    Ожидаемый результат (ОР):
    - Система выполняет перезагрузку страницы и возвращает пользователя на дефолтный URL со знаком вопроса.
    - Ранее введенное значение зарплаты сбрасывается до пустого значения.
    """
    with allure.step("Шаг 1: Переход на страницу и заполнение поля 'Заработная плата от'"):
        gpd_page.navigate()
        gpd_page.salary_min_input.wait_for(state="visible", timeout=5000)
        gpd_page.salary_min_input.click()
        gpd_page.salary_min_input.fill("500")

    with allure.step("Шаг 2: Применение фильтра"):
        gpd_page.apply_filter_and_wait()

    with allure.step("Шаг 3: Нажатие на кнопку 'Сбросить фильтр' и ожидание обновления страницы"):
        gpd_page.reset_filter_btn.wait_for(state="visible", timeout=5000)
        gpd_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация очистки инпута зарплаты и возврата к дефолтному URL"):
        expect(gpd_page.salary_min_input).to_have_value("")
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/gpd/public-works/?")


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Сортировка работ по ГПД по зарплате (возрастание/убывание)")
@pytest.mark.parametrize("sort_value, check", [
    ("salary_asc", lambda values: values == sorted(values)),
    ("salary_desc", lambda values: values == sorted(values, reverse=True)),
])
def test_guest_sorting_by_salary(guest_page: Page, gpd_page: GpdPage, sort_value: str, check):
    """
    Бизнес-кейс: Проверка корректности сортировки выдачи работ по ГПД по уровню заработной платы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Перейти на страницу и дождаться видимости селекта сортировки.
    2. Выбрать тестируемый режим сортировки по значению.
    3. Дождаться перезагрузки страницы (компонент submit-on-change).
    4. Собрать значения зарплат со всех карточек выдачи и проверить порядок сортировки.

    Ожидаемый результат (ОР):
    - Селект сортировки принимает выбранное значение, в URL добавляется query-параметр sort_by.
    - Зарплаты на карточках выдачи отсортированы в заявленном порядке.
    """
    with allure.step(f"Шаг 1: Переход на страницу и выбор сортировки '{sort_value}'"):
        gpd_page.navigate()
        gpd_page.sort_by_select.wait_for(state="visible", timeout=5000)
        gpd_page.sort_by_select.select_option(value=sort_value)

    with allure.step("Шаг 2: Ожидание перезагрузки бэкенда и валидация состояния"):
        guest_page.wait_for_load_state("load")
        expect(gpd_page.sort_by_select).to_have_value(sort_value)
        expect(guest_page).to_have_url(re.compile(f"sort_by={sort_value}"))

    with allure.step("ОР 1: Верификация порядка зарплат на карточках выдачи"):
        gpd_page.salary_value.first.wait_for(state="visible", timeout=5000)

        count = gpd_page.salary_value.count()
        assert count > 0, "Ошибка: сортировка вернула пустой список работ"

        salaries = []
        for i in range(count):
            salary_text = gpd_page.salary_value.nth(i).text_content().replace(" ", "").replace("\xa0", "")
            numbers = re.findall(r"[\d.,]+", salary_text)
            if numbers:
                salaries.append(float(numbers[0].replace(",", ".")))

        assert check(salaries), f"Ошибка: зарплаты не отсортированы корректно для '{sort_value}': {salaries}"


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Переход на детальную страницу вакансии по кнопке 'Подробнее'")
def test_guest_navigate_to_detail_via_button(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка перехода на детальную страницу вакансии по кнопке "Подробнее".

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Перейти на страницу и дождаться видимости кнопки "Подробнее" на первой карточке.
    2. Кликнуть по кнопке.
    3. Дождаться полной загрузки детальной страницы вакансии.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу вида /registration/future-vacancy/gpd-works/{id}/detail/.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание кнопки 'Подробнее'"):
        gpd_page.navigate()
        gpd_page.detail_btn.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Подробнее' на первой карточке"):
        gpd_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на детальную страницу вакансии"):
        expect(guest_page).to_have_url(re.compile(r"/registration/future-vacancy/gpd-works/\d+/detail/"))


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Переход на страницу нанимателя по клику на название организации")
def test_guest_navigate_to_employer_via_organization_link(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка перехода на страницу нанимателя по клику на название организации в карточке.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Перейти на страницу и зафиксировать название нанимателя на первой карточке.
    2. Кликнуть по ссылке с названием организации.
    3. Дождаться полной загрузки страницы нанимателя.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу вида /directory/business-entity/{id}/detail/public/.
    - На открытой странице отображается название выбранной организации.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация нанимателя первой карточки"):
        gpd_page.navigate()
        gpd_page.organization_link.first.wait_for(state="visible", timeout=5000)
        employer_name = gpd_page.organization_link.first.text_content().strip()

    with allure.step("Шаг 2: Клик по ссылке с названием организации"):
        gpd_page.organization_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на страницу нанимателя"):
        expect(guest_page).to_have_url(re.compile(r"/directory/business-entity/\d+/detail/public/"))
        expect(guest_page.locator(f"text={employer_name}").first).to_be_visible(timeout=5000)


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Переход на страницу нанимателя по ссылке организации внутри детальной страницы вакансии")
def test_guest_navigate_to_employer_from_detail_page(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка перехода на страницу нанимателя по ссылке организации, расположенной
    не на карточке списка, а внутри детальной страницы вакансии.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Перейти на страницу выдачи и кликнуть по кнопке "Подробнее" первой карточки.
    2. На открывшейся детальной странице вакансии зафиксировать название нанимателя по ссылке.
    3. Кликнуть по ссылке с названием организации внутри детальной страницы.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу нанимателя вида /directory/business-entity/{id}/detail/public/.
    - На открытой странице нанимателя присутствует блок "Вакансии организации".
    """
    with allure.step("Шаг 1: Переход на страницу выдачи и провал в детальную карточку первой вакансии"):
        gpd_page.navigate()
        gpd_page.detail_btn.first.wait_for(state="visible", timeout=5000)
        gpd_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("Шаг 2: Фиксация нанимателя по ссылке внутри детальной страницы вакансии"):
        gpd_page.detail_organization_link.wait_for(state="visible", timeout=5000)
        employer_name = gpd_page.detail_organization_link.text_content().strip()

    with allure.step("Шаг 3: Клик по ссылке с названием организации внутри детальной страницы"):
        gpd_page.detail_organization_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на страницу нанимателя и наличия блока вакансий организации"):
        expect(guest_page).to_have_url(re.compile(r"/directory/business-entity/\d+/detail/public/"))
        expect(guest_page.locator(f"text={employer_name}").first).to_be_visible(timeout=5000)
        expect(guest_page.locator("text=Вакансии организации")).to_be_visible(timeout=5000)


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Изменение количества отображаемых работ на странице (10 -> 20 -> 50 -> 10)")
def test_guest_change_paginate_by_count(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка работы селекта количества элементов на странице выдачи работ по ГПД.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам.

    Шаги:
    1. Открыть страницу и проверить, что по умолчанию в селекте выбрано значение "10".
    2. Переключить селект на значение "20", дождаться загрузки и проверить количество карточек.
    3. Переключить селект на значение "50", дождаться загрузки и проверить количество карточек.
    4. Переключить селект обратно на "10" и верифицировать возврат к исходному количеству.

    Ожидаемый результат (ОР):
    - Селект успешно переключает режимы отображения, бэкенд перестраивает выдачу с соответствующим лимитом строк.
    """
    with allure.step("Шаг 1: Переход на страницу и проверка дефолтного значения 10"):
        gpd_page.navigate()
        gpd_page.paginate_by_select.wait_for(state="visible", timeout=5000)
        expect(gpd_page.paginate_by_select).to_have_value("10")

        gpd_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        initial_cards_count = gpd_page.vacancy_cards.count()
        assert 0 < initial_cards_count <= 10, f"Ошибка: дефолтное количество карточек {initial_cards_count} > 10"

    with allure.step("Шаг 2: Переключение лимита на '20' и верификация количества"):
        gpd_page.paginate_by_select.select_option(label="20")
        guest_page.wait_for_load_state("load")

        gpd_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        cards_count_20 = gpd_page.vacancy_cards.count()
        assert 0 < cards_count_20 <= 20, f"Ошибка: при лимите 20 отобразилось {cards_count_20} карточек"

    with allure.step("Шаг 3: Переключение лимита на '50' и верификация количества"):
        gpd_page.paginate_by_select.select_option(label="50")
        guest_page.wait_for_load_state("load")

        gpd_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        cards_count_50 = gpd_page.vacancy_cards.count()
        assert 0 < cards_count_50 <= 50, f"Ошибка: при лимите 50 отобразилось {cards_count_50} карточек"
        assert cards_count_50 >= cards_count_20, (
            f"Ошибка: при лимите 50 карточек меньше, чем при лимите 20 ({cards_count_50} < {cards_count_20})"
        )

    with allure.step("Шаг 4: Возврат лимита на '10' и финальная верификация"):
        gpd_page.paginate_by_select.select_option(label="10")
        guest_page.wait_for_load_state("load")

        gpd_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        final_cards_count = gpd_page.vacancy_cards.count()
        assert 0 < final_cards_count <= 10, f"Ошибка: после возврата на 10 отобразилось {final_cards_count} карточек"


@pytest.mark.gpd
@allure.title("Бизнес-кейс: Постраничная навигация (вперед на страницу 2, назад на страницу 1)")
def test_guest_pagination_forward_and_back(guest_page: Page, gpd_page: GpdPage):
    """
    Бизнес-кейс: Проверка корректности постраничной навигации по выдаче работ по ГПД.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница работ по гражданско-правовым договорам, выдача содержит больше одной страницы.

    Шаги:
    1. Открыть страницу и кликнуть по ссылке на вторую страницу пагинации.
    2. Верифицировать, что активный номер страницы стал равен "2".
    3. Кликнуть по стрелке "назад" (caret-left).
    4. Верифицировать возврат на первую страницу выдачи.

    Ожидаемый результат (ОР):
    - Постраничная навигация корректно переключает выдачу как вперед, так и назад.
    """
    with allure.step("Шаг 1: Переход на страницу и клик по ссылке второй страницы пагинации"):
        gpd_page.navigate()
        gpd_page.page_2_link.wait_for(state="visible", timeout=5000)
        gpd_page.page_2_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация активной второй страницы"):
        expect(gpd_page.active_page_number).to_have_text("2")
        gpd_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по стрелке 'назад'"):
        gpd_page.back_arrow_btn.wait_for(state="visible", timeout=5000)
        gpd_page.back_arrow_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 2: Верификация возврата на первую страницу"):
        expect(gpd_page.active_page_number).to_have_text("1")
        gpd_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
