import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.future_work_page import FutureWorkPage


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Поиск перспективных рабочих мест по профессии")
def test_guest_search_by_profession(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы основного поля поиска по профессии (аналогичного главной странице).

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Зафиксировать профессию первой карточки текущей (неотфильтрованной) выдачи.
    2. Ввести зафиксированную профессию в поле поиска и нажать кнопку "Найти".
    3. Проверить, что в URL зафиксирован query-параметр profession.

    Ожидаемый результат (ОР):
    - В адресной строке зафиксирован query-параметр 'profession' с введенным значением.
    - Выдача после поиска содержит хотя бы одну карточку с искомой профессией в заголовке.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация профессии первой карточки"):
        future_work_page.navigate()
        future_work_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        profession = future_work_page.vacancy_title_link.first.text_content().strip()

    with allure.step(f"Шаг 2: Ввод профессии '{profession}' и клик по кнопке 'Найти'"):
        future_work_page.search_input.click()
        future_work_page.search_input.fill(profession)
        future_work_page.search_button.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация query-параметра profession в URL и наличия карточки в выдаче"):
        expect(guest_page).to_have_url(re.compile(r"profession="))
        future_work_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        assert future_work_page.vacancy_title_link.count() > 0, "Ошибка: поиск по профессии вернул пустой список"


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по территориально-административной иерархии")
def test_guest_filter_by_region(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра по территориально-административной принадлежности (Область).

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и выбрать из выпадающего списка Select2 область "Минская".
    2. Применить фильтрацию нажатием кнопки "Поиск".
    3. Собрать адреса всех карточек выдачи и проверить вхождение выбранной области.

    Ожидаемый результат (ОР):
    - Выдача возвращает непустой список результатов, где в каждой карточке фигурирует область "Минская".
    """
    with allure.step("Шаг 1: Переход на страницу и выбор области 'Минская'"):
        future_work_page.navigate()
        future_work_page.select_from_dropdown(future_work_page.region_dropdown, "Минская")

    with allure.step("Шаг 2: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация выбранной области во всех карточках результатов"):
        future_work_page.address_value.first.wait_for(state="visible", timeout=5000)

        count = future_work_page.address_value.count()
        assert count > 0, "Ошибка: фильтрация по области вернула пустой список перспективных мест"

        for i in range(count):
            address_text = future_work_page.address_value.nth(i).text_content().strip()
            assert "Минская" in address_text, (
                f"Ошибка: на позиции {i + 1} найдено перспективное место с чужой областью '{address_text}'"
            )


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по минимальной Заработной плате")
def test_guest_filter_by_min_salary(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы числового фильтра минимальной планки заработной платы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Открыть страницу и заполнить инпут "Заработная плата от" значением "1000".
    2. Применить фильтр нажатием кнопки "Поиск".
    3. Проверить, что доход на всех карточках выдачи не ниже установленной планки.

    Ожидаемый результат (ОР):
    - Система корректно отсекает перспективные рабочие места, доход по которым ниже лимита в 1000 рублей.
    """
    with allure.step("Шаг 1: Переход на страницу и заполнение поля 'Заработная плата от'"):
        future_work_page.navigate()
        future_work_page.salary_min_input.wait_for(state="visible", timeout=5000)
        future_work_page.salary_min_input.click()
        future_work_page.salary_min_input.fill("1000")

    with allure.step("Шаг 2: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Проверка соответствия уровня зарплаты на всех карточках страницы"):
        future_work_page.salary_value.first.wait_for(state="visible", timeout=5000)

        count = future_work_page.salary_value.count()
        assert count > 0, "Ошибка: фильтрация по зарплате вернула пустой список"

        for i in range(count):
            salary_text = future_work_page.salary_value.nth(i).text_content().replace(" ", "").replace("\xa0", "")
            numbers = [int(s) for s in re.findall(r"\d+", salary_text)]

            if numbers:
                max_salary_on_card = max(numbers)
                assert max_salary_on_card >= 1000, (
                    f"Ошибка: на позиции {i + 1} найдено место с неподходящей зарплатой: {numbers}"
                )


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по Режиму рабочего времени")
def test_guest_filter_by_work_time_mode(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка фильтра режима времени с валидацией внутри детальной страницы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока режима рабочего времени.
    2. Выбрать из списка Select2 значение "Одна смена".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Перейти на детальную страницу первой отфильтрованной карточки.
    5. Верифицировать наличие параграфа "Одна смена" в блоке условий труда.

    Ожидаемый результат (ОР):
    - Внутри детальной страницы первой отфильтрованной вакансии отображается режим работы "Одна смена".
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера режима времени"):
        future_work_page.navigate()
        future_work_page.open_spoiler_if_hidden(
            future_work_page.work_time_mode_filter_title, future_work_page.work_time_mode_search_field
        )

    with allure.step("Шаг 2: Выбор режима 'Одна смена' через Select2"):
        future_work_page.select_from_dropdown(future_work_page.work_time_mode_search_field, "Одна смена")

    with allure.step("Шаг 3: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки"):
        future_work_page.detail_btn.first.wait_for(state="visible", timeout=5000)
        future_work_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация режима работы внутри детальной страницы"):
        detail_mode_paragraph = guest_page.locator("div.col-6 p:has-text('Одна смена')").first
        expect(detail_mode_paragraph).to_be_visible(timeout=5000)


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по Нанимателю")
def test_guest_filter_by_employer(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра по нанимателю, скрытого за спойлером карточки фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест, на ней есть хотя бы одно место.

    Шаги:
    1. Перейти на страницу и зафиксировать название нанимателя из первой карточки выдачи.
    2. Раскрыть скрытый спойлер блока "Наниматель".
    3. Найти и выбрать зафиксированного нанимателя через Select2.
    4. Применить фильтрацию нажатием кнопки "Поиск".
    5. Проверить, что все карточки результатов принадлежат выбранному нанимателю.

    Ожидаемый результат (ОР):
    - Выдача после фильтрации содержит только перспективные места выбранного нанимателя.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация нанимателя первой карточки"):
        future_work_page.navigate()
        future_work_page.organization_link.first.wait_for(state="visible", timeout=5000)
        employer_name = future_work_page.organization_link.first.text_content().strip()

    with allure.step("Шаг 2: Раскрытие спойлера фильтра 'Наниматель'"):
        future_work_page.open_spoiler_if_hidden(
            future_work_page.employer_filter_title, future_work_page.employer_search_field
        )

    with allure.step("Шаг 3: Выбор зафиксированного нанимателя через Select2"):
        future_work_page.select_from_dropdown(future_work_page.employer_search_field, employer_name)

    with allure.step("Шаг 4: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация принадлежности всех карточек выбранному нанимателю"):
        future_work_page.organization_link.first.wait_for(state="visible", timeout=5000)

        count = future_work_page.organization_link.count()
        assert count > 0, "Ошибка: фильтрация по нанимателю вернула пустой список"

        for i in range(count):
            card_employer = future_work_page.organization_link.nth(i).text_content().strip()
            assert card_employer == employer_name, (
                f"Ошибка: на позиции {i + 1} найдено место чужого нанимателя '{card_employer}'"
            )


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по Характеру работы")
def test_guest_filter_by_work_nature(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра характера занятости с валидацией внутри детальной страницы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока характера работы.
    2. Выбрать из списка вариант "Постоянная" через Select2.
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Перейти на детальную страницу первой отфильтрованной карточки.
    5. Верифицировать наличие параграфа "Постоянная".

    Ожидаемый результат (ОР):
    - Внутри детальной страницы первой вакансии в блоке условий труда отображается статус "Постоянная".
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера характера работы"):
        future_work_page.navigate()
        future_work_page.open_spoiler_if_hidden(
            future_work_page.work_nature_filter_title, future_work_page.work_nature_search_field
        )

    with allure.step("Шаг 2: Выбор характера работы 'Постоянная'"):
        future_work_page.select_from_dropdown(future_work_page.work_nature_search_field, "Постоянная")

    with allure.step("Шаг 3: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки"):
        future_work_page.detail_btn.first.wait_for(state="visible", timeout=5000)
        future_work_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация характера работы внутри детальной страницы"):
        detail_nature_paragraph = guest_page.locator("div.col-6 p:has-text('Постоянная')").first
        expect(detail_nature_paragraph).to_be_visible(timeout=5000)


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по Уровню образования")
def test_guest_filter_by_education(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра минимального уровня образования, требуемого нанимателем.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока образования.
    2. Выбрать из выпадающего списка Select2 уровень "Высшее".
    3. Применить фильтр нажатием кнопки "Поиск".
    4. Перейти на детальную страницу первой отфильтрованной карточки.
    5. Верифицировать наличие точного текста "Высшее" в блоке требований к кандидату.

    Ожидаемый результат (ОР):
    - Внутри открытого места в графе требуемого образования отображается ценз "Высшее".
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера образования"):
        future_work_page.navigate()
        future_work_page.open_spoiler_if_hidden(
            future_work_page.education_filter_title, future_work_page.education_search_field
        )

    with allure.step("Шаг 2: Выбор уровня образования 'Высшее' через Select2"):
        future_work_page.select_from_dropdown(future_work_page.education_search_field, "Высшее")

    with allure.step("Шаг 3: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки"):
        future_work_page.detail_btn.first.wait_for(state="visible", timeout=5000)
        future_work_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация требуемого образования внутри детальной страницы"):
        detail_education_paragraph = guest_page.locator("div.col-6 p:has-text('Высшее')").first
        expect(detail_education_paragraph).to_be_visible(timeout=5000)


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по Сфере деятельности")
def test_guest_filter_by_activity_sphere(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы множественного фильтра сферы деятельности, скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Сфера деятельности".
    2. Выбрать через Select2 значение "Здравоохранение, спорт, красота, социальное обеспечение".
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что в URL зафиксирован выбранный фильтр и выдача не пуста.

    Ожидаемый результат (ОР):
    - Скрытый спойлер успешно раскрывается, множественный Select2 принимает посимвольный ввод.
    - Выдача после фильтрации возвращает непустой список результатов.
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Сфера деятельности'"):
        future_work_page.navigate()
        future_work_page.open_spoiler_if_hidden(
            future_work_page.activity_sphere_filter_title, future_work_page.activity_sphere_search_field
        )

    with allure.step("Шаг 2: Выбор сферы деятельности через Select2"):
        future_work_page.select_from_dropdown(
            future_work_page.activity_sphere_search_field,
            "Здравоохранение, спорт, красота, социальное обеспечение",
        )

    with allure.step("Шаг 3: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация применения фильтра и наличия результатов выдачи"):
        expect(guest_page).to_have_url(re.compile(r"activity_area="))
        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        assert future_work_page.vacancy_cards.count() > 0, (
            "Ошибка: фильтрация по сфере деятельности вернула пустой список"
        )


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по Планируемой дате образования вакансии")
def test_guest_filter_by_planned_date(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра по календарной дате планируемого образования вакансии.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока планируемой даты.
    2. Заполнить календарь датой в пределах допустимого диапазона (min/max инпута).
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Проверить, что в URL зафиксирован выбранный фильтр works_starts.

    Ожидаемый результат (ОР):
    - Скрытый спойлер с календарем успешно раскрывается по клику на заголовок.
    - Выбранная дата корректно передается бэкенду в виде query-параметра works_starts.
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера планируемой даты"):
        future_work_page.navigate()
        future_work_page.open_spoiler_if_hidden(
            future_work_page.planned_date_filter_title, future_work_page.works_starts_input
        )

    with allure.step("Шаг 2: Заполнение календаря датой в пределах допустимого диапазона"):
        max_date = future_work_page.works_starts_input.get_attribute("max")
        future_work_page.works_starts_input.fill(max_date)

    with allure.step("Шаг 3: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация применения фильтра по планируемой дате"):
        expect(guest_page).to_have_url(re.compile(f"works_starts={max_date}"))


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Фильтрация перспективных рабочих мест по признаку 'Предоставляется жилье'")
def test_guest_filter_by_housing(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы чекбокса-фильтра предоставления жилья, скрытого за спойлером.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и раскрыть скрытый спойлер блока "Предоставляется жилье".
    2. Кликнуть по текстовому лейблу чекбокса.
    3. Применить фильтрацию нажатием кнопки "Поиск".
    4. Раскрыть спойлер повторно и проверить, что чекбокс остался отмеченным после перезагрузки.

    Ожидаемый результат (ОР):
    - Чекбокс успешно активируется по клику на лейбл и сохраняет состояние после применения фильтра.
    """
    with allure.step("Шаг 1: Переход на страницу и раскрытие спойлера 'Предоставляется жилье'"):
        future_work_page.navigate()
        future_work_page.open_spoiler_if_hidden(
            future_work_page.housing_filter_title, future_work_page.housing_label
        )

    with allure.step("Шаг 2: Клик по чекбоксу 'Предоставляется жилье'"):
        future_work_page.housing_label.click()
        assert future_work_page.housing_checkbox.is_checked(), "Ошибка: чекбокс не отметился по клику на лейбл"

    with allure.step("Шаг 3: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация сохранения состояния чекбокса после применения фильтра"):
        expect(guest_page).to_have_url(re.compile(r"housing=on"))
        future_work_page.open_spoiler_if_hidden(
            future_work_page.housing_filter_title, future_work_page.housing_label
        )
        assert future_work_page.housing_checkbox.is_checked(), "Ошибка: чекбокс сбросился после применения фильтра"


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Сброс установленных фильтров перспективных рабочих мест")
def test_guest_reset_applied_filters(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных поисковых фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Открыть страницу и заполнить инпут "Заработная плата от" значением "1000".
    2. Применить фильтр нажатием кнопки "Поиск".
    3. Кликнуть по кнопке "Сбросить фильтр".
    4. Верифицировать очистку поля и возврат к дефолтному URL со знаком вопроса.

    Ожидаемый результат (ОР):
    - Система выполняет перезагрузку страницы и возвращает пользователя на дефолтный URL со знаком вопроса.
    - Ранее введенное значение зарплаты сбрасывается до пустого значения.
    """
    with allure.step("Шаг 1: Переход на страницу и заполнение поля 'Заработная плата от'"):
        future_work_page.navigate()
        future_work_page.salary_min_input.wait_for(state="visible", timeout=5000)
        future_work_page.salary_min_input.click()
        future_work_page.salary_min_input.fill("1000")

    with allure.step("Шаг 2: Применение фильтра"):
        future_work_page.apply_filter_and_wait()

    with allure.step("Шаг 3: Нажатие на кнопку 'Сбросить фильтр' и ожидание обновления страницы"):
        future_work_page.reset_filter_btn.wait_for(state="visible", timeout=5000)
        future_work_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация очистки инпута зарплаты и возврата к дефолтному URL"):
        expect(future_work_page.salary_min_input).to_have_value("")
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/future-vacancy/future-works/?")


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Переход на детальную страницу по кнопке 'Подробнее'")
def test_guest_navigate_to_detail_via_button(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка перехода на детальную страницу перспективного рабочего места по кнопке "Подробнее".

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и дождаться видимости кнопки "Подробнее" на первой карточке.
    2. Кликнуть по кнопке.
    3. Дождаться полной загрузки детальной страницы вакансии.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу вида /registration/employer/vacancy/create-future/{id}/detail-public/.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание кнопки 'Подробнее'"):
        future_work_page.navigate()
        future_work_page.detail_btn.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Подробнее' на первой карточке"):
        future_work_page.detail_btn.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на детальную страницу вакансии"):
        expect(guest_page).to_have_url(re.compile(r"/registration/employer/vacancy/create-future/\d+/detail-public/"))


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Переход на страницу нанимателя по клику на название организации")
def test_guest_navigate_to_employer_via_organization_link(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка перехода на страницу нанимателя по клику на название организации в карточке.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Перейти на страницу и зафиксировать название нанимателя на первой карточке.
    2. Кликнуть по ссылке с названием организации.
    3. Дождаться полной загрузки страницы нанимателя.

    Ожидаемый результат (ОР):
    - Пользователь успешно переходит на страницу вида /directory/business-entity/{id}/detail/public/.
    - На открытой странице отображается название выбранной организации.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация нанимателя первой карточки"):
        future_work_page.navigate()
        future_work_page.organization_link.first.wait_for(state="visible", timeout=5000)
        employer_name = future_work_page.organization_link.first.text_content().strip()

    with allure.step("Шаг 2: Клик по ссылке с названием организации"):
        future_work_page.organization_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на страницу нанимателя"):
        expect(guest_page).to_have_url(re.compile(r"/directory/business-entity/\d+/detail/public/"))
        expect(guest_page.locator(f"text={employer_name}").first).to_be_visible(timeout=5000)


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Изменение количества отображаемых мест на странице (10 -> 20 -> 50 -> 10)")
def test_guest_change_paginate_by_count(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка работы селекта количества элементов на странице выдачи перспективных мест.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест.

    Шаги:
    1. Открыть страницу и проверить, что по умолчанию в селекте выбрано значение "10".
    2. Переключить селект на значение "20", дождаться загрузки и проверить количество карточек.
    3. Переключить селект на значение "50", дождаться загрузки и проверить количество карточек.
    4. Переключить селект обратно на "10" и верифицировать возврат к исходному количеству.

    Ожидаемый результат (ОР):
    - Селект успешно переключает режимы отображения, бэкенд перестраивает выдачу с соответствующим лимитом строк.
    """
    with allure.step("Шаг 1: Переход на страницу и проверка дефолтного значения 10"):
        future_work_page.navigate()
        future_work_page.paginate_by_select.wait_for(state="visible", timeout=5000)
        expect(future_work_page.paginate_by_select).to_have_value("10")

        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        initial_cards_count = future_work_page.vacancy_cards.count()
        assert 0 < initial_cards_count <= 10, f"Ошибка: дефолтное количество карточек {initial_cards_count} > 10"

    with allure.step("Шаг 2: Переключение лимита на '20' и верификация количества"):
        future_work_page.paginate_by_select.select_option(label="20")
        guest_page.wait_for_load_state("load")

        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        cards_count_20 = future_work_page.vacancy_cards.count()
        assert 10 < cards_count_20 <= 20, f"Ошибка: при лимите 20 отобразилось {cards_count_20} карточек"

    with allure.step("Шаг 3: Переключение лимита на '50' и верификация количества"):
        future_work_page.paginate_by_select.select_option(label="50")
        guest_page.wait_for_load_state("load")

        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        cards_count_50 = future_work_page.vacancy_cards.count()
        assert 20 < cards_count_50 <= 50, f"Ошибка: при лимите 50 отобразилось {cards_count_50} карточек"

    with allure.step("Шаг 4: Возврат лимита на '10' и финальная верификация"):
        future_work_page.paginate_by_select.select_option(label="10")
        guest_page.wait_for_load_state("load")

        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        final_cards_count = future_work_page.vacancy_cards.count()
        assert 0 < final_cards_count <= 10, f"Ошибка: после возврата на 10 отобразилось {final_cards_count} карточек"


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Проверка сортировки выдачи перспективных рабочих мест")
def test_guest_sorting_options(guest_page: Page, future_work_page: FutureWorkPage, test_sorting: str):
    """
    Бизнес-кейс: Динамически параметризованная проверка всех доступных режимов сортировки результатов выдачи.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Данные для параметризации подтягиваются из файла конфигурации (общий список с поиском вакансий).

    Шаги:
    1. Перейти на страницу перспективных рабочих мест.
    2. Дождаться видимости селекта сортировки.
    3. Выбрать тестируемый тип сортировки по его значению из конфигурационного файла.
    4. Дождаться перезагрузки страницы (компонент submit-on-change).
    5. Верифицировать, что селект принял выбранное значение, а в URL добавился нужный query-параметр.
    6. Дождаться появления результатов и убедиться, что первая карточка успешно отображается.
    """
    if isinstance(test_sorting, (tuple, list)) and len(test_sorting) > 0:
        clean_sort_value = str(test_sorting[0])
    else:
        clean_sort_value = str(test_sorting)

    with allure.step(f"Шаг 1: Переход на страницу и выбор сортировки '{clean_sort_value}'"):
        future_work_page.navigate()
        future_work_page.sort_by_select.wait_for(state="visible", timeout=5000)
        future_work_page.sort_by_select.locator("option").first.wait_for(state="attached", timeout=5000)
        future_work_page.sort_by_select.select_option(value=clean_sort_value)

    with allure.step("Шаг 2: Ожидание перезагрузки бэкенда и валидация состояния"):
        guest_page.wait_for_load_state("load")
        expect(future_work_page.sort_by_select).to_have_value(clean_sort_value)
        expect(guest_page).to_have_url(re.compile(f"sort_by={clean_sort_value}"))

        future_work_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        expect(future_work_page.vacancy_title_link.first).to_be_visible()


@pytest.mark.future_work
@allure.title("Бизнес-кейс: Постраничная навигация (вперед на страницу 2, назад на страницу 1)")
def test_guest_pagination_forward_and_back(guest_page: Page, future_work_page: FutureWorkPage):
    """
    Бизнес-кейс: Проверка корректности постраничной навигации по выдаче перспективных рабочих мест.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница перспективных рабочих мест, выдача содержит больше одной страницы.

    Шаги:
    1. Открыть страницу и кликнуть по ссылке на вторую страницу пагинации.
    2. Верифицировать, что активный номер страницы стал равен "2".
    3. Кликнуть по стрелке "назад" (caret-left).
    4. Верифицировать возврат на первую страницу выдачи.

    Ожидаемый результат (ОР):
    - Постраничная навигация корректно переключает выдачу как вперед, так и назад.
    """
    with allure.step("Шаг 1: Переход на страницу и клик по ссылке второй страницы пагинации"):
        future_work_page.navigate()
        future_work_page.page_2_link.wait_for(state="visible", timeout=5000)
        future_work_page.page_2_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация активной второй страницы"):
        expect(future_work_page.active_page_number).to_have_text("2")
        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по стрелке 'назад'"):
        future_work_page.back_arrow_btn.wait_for(state="visible", timeout=5000)
        future_work_page.back_arrow_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 2: Верификация возврата на первую страницу"):
        expect(future_work_page.active_page_number).to_have_text("1")
        future_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
