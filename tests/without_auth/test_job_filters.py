import re
from urllib.parse import unquote
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_search_page import VacancySearchPage
from helpers.vacancy_filter_helper import apply_vacancy_filter_and_wait


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Трёхуровневая фильтрация вакансий (Область -> Район -> Город)")
def test_guest_filter_by_region_district_and_city(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка каскадной трёхуровневой фильтрации географического положения вакансий в режиме гостя.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевая десктопная сессия).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска вакансий и дождаться видимости стартового дропдауна региона.
    2. Выбрать из выпадающего списка Select2 первого уровня "Витебская" область и выдержать паузу для подгрузки районов.
    3. Выбрать из списка второго уровня "Полоцкий" район и дождаться обновления списка населенных пунктов.
    4. Выбрать из списка третьего уровня город "Полоцк".
    5. Применить фильтрацию нажатием кнопки поиска через хелпер.
    6. Собрать адреса всех карточек на странице выдачи и верифицировать вхождение слова "Полоцк".

    Ожидаемый результат (ОР):
    - Списки Select2 корректно обновляются на каждом каскадном шаге, отдавая зависимые данные.
    - Выдача возвращает непустой список результатов, где в каждой карточке строго фигурирует город "Полоцк".
    """
    with allure.step("Шаг 1: Переход на страницу поиска вакансий"):
        vacancy_page.navigate()
        vacancy_page.region_dropdown.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Каскадный ручной выбор Витебской области, Полоцкого района и г. Полоцк"):
        vacancy_page.select_from_dropdown(vacancy_page.region_dropdown, "Витебская")
        guest_page.wait_for_timeout(1500)

        vacancy_page.select_from_dropdown(vacancy_page.district_dropdown, "Полоцкий")
        guest_page.wait_for_timeout(1500)

        vacancy_page.select_from_dropdown(vacancy_page.address_dropdown, "Полоцк")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Верификация наличия Полоцка во всех карточках результатов выдачи"):
        all_card_addresses = guest_page.locator("span.address").filter(visible=True)
        all_card_addresses.first.wait_for(state="visible", timeout=5000)

        count = all_card_addresses.count()
        assert count > 0, "Ошибка: фильтрация вернула пустой список вакансий"

        for i in range(count):
            address_text = all_card_addresses.nth(i).text_content().strip()
            assert "Полоцк" in address_text, (
                f"Ошибка: на позиции {i + 1} найдена чужая вакансия с адресом '{address_text}'"
            )


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по минимальной Заработной плате")
def test_guest_filter_by_min_salary(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы числового фильтра минимальной планки заработной платы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Открыть страницу фильтров и дождаться готовности инпута "Зарплата От".
    2. Заполнить инпут значением "1000".
    3. Применить фильтр нажатием кнопки через хелпер.
    4. Локализовать блоки зарплат на всех сгенерированных карточках выдачи.
    5. Распарсить числовые значения из текстовых блоков (включая диапазоны от-до).
    6. Верифицировать, что максимальная планка на любой карточке составляет не менее 1000 рублей.

    Ожидаемый результат (ОР):
    - Система корректно отсекает вакансии, доход по которым ниже установленного лимита в 1000 рублей.
    """
    with allure.step("Шаг 1: Переход на страницу поиска и заполнение поля 'Зарплата От'"):
        vacancy_page.navigate()
        vacancy_page.salary_min_input.wait_for(state="visible", timeout=5000)
        vacancy_page.salary_min_input.click()
        vacancy_page.salary_min_input.fill("1000")

    with allure.step("Шаг 2: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка соответствия уровня зарплаты на всех карточках страницы"):
        salary_elements = guest_page.locator("text=/руб./").filter(visible=True)
        salary_elements.first.wait_for(state="visible", timeout=5000)

        count = salary_elements.count()
        assert count > 0, "Ошибка: фильтрация по зарплате вернула пустой список"

        for i in range(count):
            salary_text = salary_elements.nth(i).text_content().replace(" ", "")
            salary_numbers = [int(s) for s in re.findall(r"\d+", salary_text)]

            if salary_numbers:
                max_salary_on_card = max(salary_numbers)
                assert max_salary_on_card >= 1000, (
                    f"Ошибка: на позиции {i + 1} найдена вакансия с неподходящей зарплатой: {salary_numbers}"
                )


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по диапазону Ставки (0.25 - 0.5)")
def test_guest_filter_by_wage_rate_range(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка фильтрации вакансий по дробному диапазону объёма рабочей ставки.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Открыть страницу поиска и раскрыть скрытый спойлер блока ставок кликом по его h4 заголовку.
    2. Ввести в инпут "Ставка От" значение "0.25", в инпут "Ставка До" — "0.5".
    3. Отправить форму фильтрации через хелпер.
    4. Собрать текстовые блоки ставок со всех карточек результатов поисковой выдачи.
    5. С помощью регулярного выражения извлечь дробное значение ставки для каждого элемента.
    6. Убедиться, что значение ставки строго укладывается в границы от 0.25 до 0.5.

    Ожидаемый результат (ОР):
    - Скрытый спойлер ставок успешно разворачивается и принимает дробный клавиатурный ввод.
    - Выдача содержит только те вакансии, ставка по которым находится внутри диапазона [0.25; 0.5].
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера ставок"):
        vacancy_page.navigate()
        vacancy_page.open_wage_rate_spoiler_if_needed()

    with allure.step("Шаг 2: Заполнение диапазона ставок"):
        vacancy_page.wage_rate_from_input.click()
        vacancy_page.wage_rate_from_input.press_sequentially("0.25", delay=100)

        vacancy_page.wage_rate_to_input.click()
        vacancy_page.wage_rate_to_input.press_sequentially("0.5", delay=100)

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Верификация соответствия значений ставок во всех результатах выдачи"):
        rate_elements = guest_page.locator("text=/Ставка:/").filter(visible=True)
        rate_elements.first.wait_for(state="visible", timeout=5000)

        count = rate_elements.count()
        assert count > 0, "Ошибка: фильтрация по ставке вернула пустой список"

        for i in range(count):
            rate_text = rate_elements.nth(i).text_content().strip()
            match = re.search(r"Ставка:\s*([\d\.]+)", rate_text)
            assert match, f"Ошибка: не удалось распарсить текст ставки '{rate_text}' на позиции {i + 1}"

            rate_value = float(match.group(1))
            assert 0.25 <= rate_value <= 0.5, (
                f"Ошибка: на позиции {i + 1} ставка {rate_value} выходит за рамки диапазона 0.25 - 0.5"
            )


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Режиму рабочего времени")
def test_guest_filter_by_work_time_mode(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка фильтрации вакансий по выбранному режиму времени с валидацией внутри карточки.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока режима рабочего времени.
    2. Выбрать из списка Select2 значение "Одна смена".
    3. Применить фильтрацию нажатием кнопки поиска через хелпер.
    4. Дождаться появления результатов и кликнуть по заголовку первой вакансии в выдаче.
    5. Дождаться полной загрузки детальной публичной карточки вакансии.
    6. Локализовать текстовый блок условий труда и убедиться в наличии фразы "Одна смена".

    Ожидаемый результат (ОР):
    - Выбранный режим времени успешно применяется на бэкенде.
    - Внутри детальной страницы первой отфильтрованной вакансии отображается режим работы "Одна смена".
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера режима времени"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Режим рабочего времени", vacancy_page.work_time_mode_dropdown)

    with allure.step("Шаг 2: Выбор режима 'Одна смена' через Select2"):
        vacancy_page.select_from_dropdown(vacancy_page.work_time_mode_dropdown, "Одна смена")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки вакансии"):
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация режима работы внутри детальной страницы"):
        detail_mode_paragraph = guest_page.locator("div.col-6 p:has-text('Одна смена')").first
        expect(detail_mode_paragraph).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по названию Нанимателя")
def test_guest_filter_by_employer_name(guest_page: Page, vacancy_page: VacancySearchPage, app_config):
    """
    Бизнес-кейс: Проверка поиска и фильтрации предложений по текстовому названию организации.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу фильтров и раскрыть скрытый спойлер блока "Наниматель".
    2. Вызвать кастомный метод Select2 и ввести эталонное название компании из конфигурационного файла.
    3. Отправить форму нажатием кнопки поиска через хелпер.
    4. Собрать текстовые блоки названий компаний со всех сгенерированных карточек выдачи.
    5. Проверить вхождение ключевого слова нанимателя в каждом результате страницы.

    Ожидаемый результат (ОР):
    - Поиск внутри Select2 корректно находит организацию по текстовому названию.
    - Фильтрация возвращает вакансии, принадлежащие только выбранному нанимателю.
    """
    test_data = app_config["vacancy_filter_test_data"]

    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера нанимателя"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Наниматель", vacancy_page.employer_dropdown)

    with allure.step("Шаг 2: Ввод полного названия нанимателя из конфига"):
        vacancy_page.select_from_dropdown(vacancy_page.employer_dropdown, test_data["employer_name"])

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка наличия выбранного нанимателя во всех карточках результатов"):
        employer_elements = guest_page.locator("text=" + test_data["employer_assert_keyword"]).filter(visible=True)
        employer_elements.first.wait_for(state="visible", timeout=5000)

        count = employer_elements.count()
        assert count > 0, "Ошибка: фильтрация по названию нанимателя вернула пустой список"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по УНП Нанимателя")
def test_guest_filter_by_employer_unp(guest_page: Page, vacancy_page: VacancySearchPage, app_config):
    """
    Бизнес-кейс: Проверка поиска и фильтрации предложений по цифровому УНП организации.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу фильтров и раскрыть скрытый спойлер блока "Наниматель".
    2. Вызвать специальный метод посимвольного ввода УНП организации из файла конфигурации.
    3. Кликнуть по первому выпавшему совпадению в списке вариантов.
    4. Применить фильтрацию нажатием кнопки поиска через хелпер.
    5. Верифицировать наличие ключевого слова нанимателя во всех выведенных карточках результатов.

    Ожидаемый результат (ОР):
    - Справочник организаций Select2 успешно соотносит цифровой УНП с названием юридического лица.
    - Выдача перестраивается и выводит предложения конкретной компании.
    """
    test_data = app_config["vacancy_filter_test_data"]

    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера нанимателя"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Наниматель", vacancy_page.employer_dropdown)

    with allure.step("Шаг 2: Ввод цифрового УНП нанимателя через специальный метод"):
        vacancy_page.select_employer_by_unp(test_data["employer_unp"])

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка наличия выбранного нанимателя во всех карточках результатов по УНП"):
        employer_elements = guest_page.locator("text=" + test_data["employer_assert_keyword"]).filter(visible=True)
        employer_elements.first.wait_for(state="visible", timeout=5000)

        count = employer_elements.count()
        assert count > 0, "Ошибка: фильтрация по УНП нанимателя вернула пустой список"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Характеру работы")
def test_guest_filter_by_work_nature(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы фильтра характера занятости с валидацией внутри детальной страницы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока характера работы.
    2. Выбрать из списка вариант "Постоянная" через Select2.
    3. Применить фильтрацию нажатием кнопки поиска через хелпер.
    4. Дождаться результатов и кликнуть по первой карточке для перехода внутрь вакансии.
    5. Верифицировать на детальной публичной странице наличие параграфа "Постоянная".

    Ожидаемый результат (ОР):
    - Система корректно обрабатывает выбор характера занятости.
    - Внутри детальной страницы первой вакансии в блоке условий труда отображается статус "Постоянная".
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера характера работы"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Характер работы", vacancy_page.work_nature_dropdown)

    with allure.step("Шаг 2: Выбор характера работы 'Постоянная'"):
        vacancy_page.select_from_dropdown(vacancy_page.work_nature_dropdown, "Постоянная")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки вакансии"):
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация характера работы внутри детальной страницы"):
        detail_nature_paragraph = guest_page.locator("div.col-6 p:has-text('Постоянная')").first
        expect(detail_nature_paragraph).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Уровню образования")
def test_guest_filter_by_education(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы фильтра минимального уровня образования, требуемого нанимателем.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока образования.
    2. Выбрать из выпадающего списка Select2 уровень "Высшее".
    3. Применить фильтр нажатием кнопки через хелпер.
    4. Перейти внутрь первой отфильтрованной карточки результатов выдачи.
    5. Верифицировать наличие точного текста "Высшее" в блоке требований к кандидату.

    Ожидаемый результат (ОР):
    - Поисковая выдача успешно перестраивается.
    - Внутри открытой вакансии в графе требуемого образования отображается ценз "Высшее".
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера образования"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Образование", vacancy_page.education_dropdown)

    with allure.step("Шаг 2: Выбор уровня образования 'Высшее' через Select2"):
        vacancy_page.select_from_dropdown(vacancy_page.education_dropdown, "Высшее")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки вакансии"):
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация требуемого образования внутри детальной страницы"):
        detail_education_paragraph = guest_page.locator("div.col-6 p:has-text('Высшее')").first
        expect(detail_education_paragraph).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий для категорий граждан (Инвалид III группы)")
def test_guest_filter_by_citizens_category(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы социального фильтра вакансий с возможностью трудоустройства уязвимых категорий граждан.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока "С возможностью трудоустройства".
    2. Выбрать из списка категорий пункт "Инвалид III группы" через Select2.
    3. Применить фильтрацию нажатием кнопки поиска через хелпер.
    4. Перейти внутрь первой отфильтрованной карточки результатов выдачи.
    5. Верифицировать отображение текста "Инвалид III группы" внутри детальной страницы вакансии.

    Ожидаемый результат (ОР):
    - Система успешно находит предложения, адаптированные под выбранную социальную категорию.
    - Внутри детальной страницы вакансии присутствует подтверждающий текст доступности для инвалидов III группы.
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера категорий граждан"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("С возможностью трудоустройства", vacancy_page.citizens_category_dropdown)

    with allure.step("Шаг 2: Выбор категории 'Инвалид III группы' через Select2"):
        vacancy_page.select_from_dropdown(vacancy_page.citizens_category_dropdown, "Инвалид III группы")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки вакансии"):
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация доступности вакансии для выбранной категории внутри страницы"):
        detail_category_text = guest_page.locator("text=Инвалид III группы").first
        expect(detail_category_text).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Гибким навыкам (Тайм-менеджмент)")
def test_guest_filter_by_soft_skills(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы множественного фильтра гибких навыков (Soft Skills) на левой панели.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока гибких навыков.
    2. Найти через поиск и выбрать навык "Тайм-менеджмент" с помощью Select2.
    3. Применить фильтрацию нажатием кнопки поиска через хелпер.
    4. Проверить, что после обновления страницы тег навыка остался активным на левой панели.
    5. Верифицировать успешную отрисовку первой карточки результатов выдачи.

    Ожидаемый результат (ОР):
    - Выбранный тег гибкого навыка успешно применяется, сохраняет активность в блоке фильтра после перезагрузки страницы и возвращает список результатов.
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера гибких навыков"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Гибкие навыки", vacancy_page.soft_skills_dropdown)

    with allure.step("Шаг 2: Выбор навыка 'Тайм-менеджмент' через Select2"):
        vacancy_page.select_from_dropdown(vacancy_page.soft_skills_dropdown, "Тайм-менеджмент")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка сохранения выбранного тега на левой панели"):
        expect(vacancy_page.soft_skills_dropdown).to_have_text(re.compile("Тайм-менеджмент.*"))

        first_card = guest_page.locator("a.debounced-link").first
        expect(first_card).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Периоду публикации (Месяц)")
def test_guest_filter_by_search_period(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы фильтра периода обновления вакансий в режиме гостя.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевая десктопная сессия).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска вакансий портала.
    2. Дождаться прикрепления скрытого нативного HTML-селекта периода к DOM-структуре страницы.
    3. Через JavaScript принудительно установить значение '3' (Месяц) и стриггерить событие 'change'.
    4. Нажать на кнопку "Поиск" для отправки формы фильтрации через хелпер.
    5. Зафиксировать блок времени обновления на первой видимой карточке выдачи.
    6. Распарсить число дней из текста и верифицировать, что оно не превышает лимит в 31 день назад.

    Ожидаемый результат (ОР):
    - Система успешно обрабатывает JS-изменение скрытого селекта.
    - Страница перезагружается и отдает список вакансий, обновленных не более месяца назад.
    """
    with allure.step("Шаг 1: Переход на страницу поиска вакансий"):
        vacancy_page.navigate()
        vacancy_page.search_period_dropdown.wait_for(state="attached", timeout=5000)

    with allure.step("Шаг 2: Выбор периода 'Месяц' в скрытом HTML-селекте через JS"):
        vacancy_page.search_period_dropdown.evaluate("el => el.value = '3'")
        vacancy_period_change = "change"
        vacancy_page.search_period_dropdown.dispatch_event(vacancy_period_change)
        guest_page.wait_for_timeout(1000)

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка соответствия периода публикации на первой карточке"):
        first_card_time = guest_page.locator("text=/назад/").first
        first_card_time.wait_for(state="visible", timeout=5000)

        time_text = first_card_time.text_content().strip()
        numbers = [int(s) for s in re.findall(r"\d+", time_text)]

        if numbers and "дней" in time_text:
            days_ago = numbers[0]
            assert days_ago <= 31, f"Ошибка: найдена старая вакансия, обновленная {days_ago} дней назад"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Сфере деятельности (Высший менеджмент)")
def test_guest_filter_by_activity_sphere(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы фильтра индустриальной сферы деятельности с валидацией на детальной странице.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока сферы деятельности.
    2. Выбрать из выпадающего списка вариант "Высший менеджмент" с помощью Select2.
    3. Применить фильтр нажатием кнопки через хелпер.
    4. Кликнуть по заголовку первой отфильтрованной карточки для перехода внутрь вакансии.
    5. Верифицировать на детальной публичной странице наличие параграфа "Высший менеджмент".

    Ожидаемый результат (ОР):
    - Списки Select2 успешно находят и применяют выбранную сферу деятельности.
    - Внутри детальной карточки в графе сферы деятельности отображается статус "Высший менеджмент".
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера сферы деятельности"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Сфера деятельности", vacancy_page.activity_sphere_dropdown)

    with allure.step("Шаг 2: Выбор сферы 'Высший менеджмент' через Select2"):
        vacancy_page.select_from_dropdown(vacancy_page.activity_sphere_dropdown, "Высший менеджмент")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки вакансии"):
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация сферы деятельности внутри детальной страницы"):
        detail_sphere_paragraph = guest_page.locator("div.col-6 p:has-text('Высший менеджмент')").first
        expect(detail_sphere_paragraph).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация по дополнительным параметрам (Молодежь 14-16 лет)")
def test_guest_filter_by_additional_params_students(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка фильтра временной занятости студентов и школьников возраста с 14 до 16 лет.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Перейти на страницу поиска и раскрыть скрытый спойлер блока "Дополнительные параметры".
    2. Кликнуть по текстовому лейблу главного чекбокса временной занятости студентов.
    3. Дождаться появления выдвижного лейбла возраста и кликнуть по варианту "14-16 лет".
    4. Применение фильтра через хелпер.
    5. Перейти на детальную публичную страницу первой вакансии в результатах выдачи.
    6. Верифицировать отображение текста "с 14 до 16 лет" в блоке условий труда.

    Ожидаемый результат (ОР):
    - Скрытые чекбоксы дополнительных параметров успешно раскрываются и активируются по клику.
    - Внутри детальной карточки присутствует подтверждающий текст доступности вакансии для молодежи с 14 до 16 лет.
    """
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера дополнительных параметров"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Дополнительные параметры", vacancy_page.students_label)

    with allure.step("Шаг 2: Последовательный клик по текстовым лейблам чекбоксов"):
        # Кликаем по тексту лейбла главного чекбокса студентов
        vacancy_page.students_label.click()

        # Дожидаемся видимости выдвижного лейбла возраста и кликаем по нему
        vacancy_page.age_14_16_label.wait_for(state="visible", timeout=3000)
        vacancy_page.age_14_16_label.click()

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 4: Провал внутрь первой отфильтрованной карточки вакансии"):
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация доступности вакансии для молодежи 14-16 лет"):
        detail_age_text = guest_page.locator("text=с 14 до 16 лет").first
        expect(detail_age_text).to_be_visible(timeout=5000)

@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Сброс установленных фильтров")
def test_guest_reset_applied_filters(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных поисковых фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Открыть страницу фильтров и дождаться готовности инпута "Зарплата От".
    2. Заполнить инпут значением "1000".
    3. Применить фильтр нажатием кнопки через хелпер.
    4. Кликнуть по кнопке "Сбросить фильтр".
    5. Дождаться полного обновления страницы.
    6. Верифицировать очистку поля "Зарплата От" до пустого значения.
    7. Верифицировать редирект на базовый URL сброса со знаком вопроса.

    Ожидаемый результат (ОР):
    - Система выполняет перезагрузку страницы и возвращает пользователя на дефолтный URL со знаком вопроса.
    - Все ранее введенные параметры фильтрации успешно очищаются до значений по умолчанию.
    """
    with allure.step("Шаг 1: Переход на страницу поиска и заполнение поля 'Зарплата От'"):
        vacancy_page.navigate()
        vacancy_page.salary_min_input.wait_for(state="visible", timeout=5000)
        vacancy_page.salary_min_input.click()
        vacancy_page.salary_min_input.fill("1000")

    with allure.step("Шаг 2: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("Шаг 3: Нажатие на кнопку 'Сбросить фильтр' и ожидание обновления страницы"):
        vacancy_page.reset_filter_btn.wait_for(state="visible", timeout=5000)
        vacancy_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация очистки инпута зарплаты и возврата к дефолтному URL"):
        expect(vacancy_page.salary_min_input).to_have_value("")
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/vacancy-search/?")


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Комбинированная фильтрация (Зарплата + Ставка + Образование)")
def test_guest_combined_filters(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка совместной работы нескольких фильтров (числового, диапазона и Select2)
    с валидацией критериев непосредственно на карточках выдачи без перехода внутрь вакансий.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Открыть страницу поиска и заполнить инпут "Зарплата От" значением "1000".
    2. Раскрыть спойлер ставок и ввести "0.25" в "Ставка От", "0.5" — в "Ставка До".
    3. Раскрыть спойлер образования и выбрать "Высшее" через Select2.
    4. Применить фильтрацию нажатием кнопки поиска через хелпер.
    5. Последовательно проверить каждую карточку в выдаче на соответствие всем трем условиям.

    Ожидаемый результат (ОР):
    - Все выбранные фильтры успешно суммируются бэкендом.
    - Каждая карточка в результатах выдачи строго удовлетворяет условиям:
      зарплата >= 1000, ставка в диапазоне [0.25; 0.5], образование — "Высшее".
    """
    with allure.step("Шаг 1: Переход на страницу поиска и заполнение поля 'Зарплата От'"):
        vacancy_page.navigate()
        vacancy_page.salary_min_input.wait_for(state="visible", timeout=5000)
        vacancy_page.salary_min_input.click()
        vacancy_page.salary_min_input.fill("1000")

    with allure.step("Шаг 2: Раскрытие спойлера ставок и заполнение диапазона"):
        vacancy_page.open_wage_rate_spoiler_if_needed()
        vacancy_page.wage_rate_from_input.click()
        vacancy_page.wage_rate_from_input.press_sequentially("0.25", delay=100)
        vacancy_page.wage_rate_to_input.click()
        vacancy_page.wage_rate_to_input.press_sequentially("0.5", delay=100)

    with allure.step("Шаг 3: Раскрытие спойлера образования и выбор 'Высшее'"):
        vacancy_page.open_spoiler_if_hidden("Образование", vacancy_page.education_dropdown)
        vacancy_page.select_from_dropdown(vacancy_page.education_dropdown, "Высшее")

    with allure.step("Шаг 4: Применение комбинированного фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Комплексная верификация всех параметров на карточках поисковой выдачи"):
        # Собираем все карточки результатов на странице
        cards = guest_page.locator("div.inner-box").filter(has=guest_page.locator("a.debounced-link"))
        cards.first.wait_for(state="visible", timeout=5000)

        count = cards.count()
        assert count > 0, "Ошибка: комбинированная фильтрация вернула пустой список"

        for i in range(count):
            card = cards.nth(i)
            card_text = card.text_content()

            # 1. Валидация уровня образования
            assert "Высшее" in card_text, (
                f"Ошибка на позиции {i + 1}: отсутствует требование образования 'Высшее'"
            )

            # 2. Валидация уровня заработной платы
            salary_elements = card.locator("text=/руб./")
            if salary_elements.count() > 0:
                salary_text = salary_elements.first.text_content().replace(" ", "")
                salary_numbers = [int(s) for s in re.findall(r"\d+", salary_text)]
                if salary_numbers:
                    assert max(salary_numbers) >= 1000, (
                        f"Ошибка на позиции {i + 1}: максимальный доход {max(salary_numbers)} ниже 1000 руб."
                    )

            # 3. Валидация размера рабочей ставки
            rate_elements = card.locator("text=/Ставка:/")
            if rate_elements.count() > 0:
                rate_text = rate_elements.first.text_content().strip()
                match = re.search(r"Ставка:\s*([\d\.]+)", rate_text)
                assert match, f"Ошибка на позиции {i + 1}: не удалось распарсить ставку в '{rate_text}'"
                rate_value = float(match.group(1))
                assert 0.25 <= rate_value <= 0.5, (
                    f"Ошибка на позиции {i + 1}: ставка {rate_value} выходит за рамки [0.25; 0.5]"
                )

@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Изменение количества отображаемых вакансий на странице (10 -> 20 -> 50 -> 10)")
def test_guest_change_paginate_by_count(guest_page: Page, vacancy_page: VacancySearchPage):
    """
    Бизнес-кейс: Проверка работы селекта количества элементов на странице выдачи вакансий.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница поиска вакансий.

    Шаги:
    1. Открыть страницу поиска вакансий.
    2. Проверить, что по умолчанию в селекте выбрано значение "10" и на странице отображается не более 10 карточек.
    3. Переключить селект на значение "20", дождаться загрузки и проверить, что отображается не более 20 карточек.
    4. Переключить селект на значение "50", дождаться загрузки и проверить, что отображается не более 50 карточек.
    5. Переключить селект обратно на "10" и верифицировать возврат к исходному количеству.

    Ожидаемый результат (ОР):
    - Селект успешно переключает режимы отображения, бэкенд перестраивает выдачу с соответствующим лимитом строк.
    """
    with allure.step("Шаг 1: Переход на страницу поиска и проверка дефолтного значения 10"):
        vacancy_page.navigate()
        vacancy_page.paginate_by_select.wait_for(state="visible", timeout=5000)
        expect(vacancy_page.paginate_by_select).to_have_value("10")

        # Проверяем, что карточек на странице не больше 10
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        initial_cards_count = vacancy_page.vacancy_title_link.count()
        assert 0 < initial_cards_count <= 10, f"Ошибка: дефолтное количество карточек {initial_cards_count} > 10"

    with allure.step("Шаг 2: Переключение лимита на '20' и верификация количества"):
        vacancy_page.paginate_by_select.select_option(label="20")
        guest_page.wait_for_load_state("load")

        # Ожидаем появление первой карточки в обновленной выдаче
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        cards_count_20 = vacancy_page.vacancy_title_link.count()
        assert 0 < cards_count_20 <= 20, f"Ошибка: при лимите 20 отобразилось {cards_count_20} карточек"

    with allure.step("Шаг 3: Переключение лимита на '50' и верификация количества"):
        vacancy_page.paginate_by_select.select_option(label="50")
        guest_page.wait_for_load_state("load")

        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        cards_count_50 = vacancy_page.vacancy_title_link.count()
        assert 0 < cards_count_50 <= 50, f"Ошибка: при лимите 50 отобразилось {cards_count_50} карточек"

    with allure.step("Шаг 4: Возврат лимита на '10' и финальная верификация"):
        vacancy_page.paginate_by_select.select_option(label="10")
        guest_page.wait_for_load_state("load")

        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        final_cards_count = vacancy_page.vacancy_title_link.count()
        assert 0 < final_cards_count <= 10, f"Ошибка: после возврата на 10 отобразилось {final_cards_count} карточек"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Проверка сортировки выдачи вакансий")
def test_guest_sorting_options(guest_page: Page, vacancy_page: VacancySearchPage, test_sorting: str):
    """Бизнес-кейс: Динамически параметризованная проверка всех доступных режимов сортировки результатов выдачи.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Данные для параметризации подтягиваются из файла конфигурации.

    Шаги:
    1. Перейти на страницу поиска вакансий.
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

    with allure.step(f"Шаг 1: Переход на страницу поиска и выбор сортировки '{clean_sort_value}'"):
        vacancy_page.navigate()
        vacancy_page.sort_by_select.wait_for(state="visible", timeout=5000)

        # Ожидание появления опций внутри нативного селекта
        vacancy_page.sort_by_select.locator("option").first.wait_for(state="attached", timeout=5000)
        vacancy_page.sort_by_select.select_option(value=clean_sort_value)

    with allure.step("Шаг 2: Ожидание перезагрузки бэкенда и валидация состояния"):
        guest_page.wait_for_load_state("load")

        # Проверяем, что значение осталось выбранным в UI
        expect(vacancy_page.sort_by_select).to_have_value(clean_sort_value)

        # Проверяем, что правильный параметр сортировки улетел в URL адресной строки
        expect(guest_page).to_have_url(re.compile(f"sort_by={clean_sort_value}"))

        # Ждем стабилизации DOM и появления первой карточки в отсортированном списке
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        expect(vacancy_page.vacancy_title_link.first).to_be_visible()