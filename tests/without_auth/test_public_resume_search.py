import re
from urllib.parse import quote
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.public_resume_search_page import PublicResumeSearchPage


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Поиск по профессии")
@allure.title("Бизнес-кейс: Поиск резюме по названию профессии через верхнюю строку поиска")
def test_search_by_profession_filters_results(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Ввод текста в поле поиска и проверка, что результаты содержат
    карточки с указанной профессией.

    Прекондишены:
    1. Пользователь не авторизован.
    2. Открыта страница поиска резюме.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Ввести название профессии в поле "Профессия/Должность".
    3. Нажать кнопку "Найти".
    4. Дождаться обновления результатов.

    ОР:
    - URL содержит параметр resume_profession с введённым значением.
    - На странице присутствуют карточки резюме (результаты не пустые).
    """
    search_term = "Учитель"

    with allure.step("Шаг 1: Переход на страницу поиска резюме"):
        public_resume_search_page.navigate()

    with allure.step(f"Шаг 2: Ввод профессии '{search_term}' и нажатие 'Найти'"):
        public_resume_search_page.profession_input.fill(search_term)
        public_resume_search_page.search_btn_main.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит resume_profession (URL-encoded), результаты не пустые"):
        expect(guest_page).to_have_url(
            re.compile(rf"resume_profession={re.escape(quote(search_term))}", re.IGNORECASE)
        )
        expect(public_resume_search_page.resume_cards.first).to_be_visible()


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Фильтр по региону")
@allure.title("Бизнес-кейс: Фильтрация резюме по региону через Select2")
def test_filter_by_region_select2(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Выбор региона в Select2 и проверка применения фильтра.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Открыть Select2 региона и выбрать "Минск".
    3. Нажать кнопку "Поиск".

    ОР:
    - URL содержит параметр region с числовым значением.
    - На странице присутствуют карточки резюме.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("Шаг 2: Выбор региона 'Минск' через Select2"):
        public_resume_search_page.select_region("Минск")

    with allure.step("Шаг 3: Применение фильтра"):
        public_resume_search_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит параметр region, результаты не пустые"):
        expect(guest_page).to_have_url(re.compile(r"region=\d+"))
        expect(public_resume_search_page.resume_cards.first).to_be_visible()


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Фильтр по зарплате")
@allure.title("Бизнес-кейс: Фильтрация резюме по минимальной зарплате")
def test_filter_by_min_salary(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Ввод минимальной зарплаты и проверка применения фильтра в URL.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Ввести значение в поле "От" (минимальная зарплата).
    3. Нажать кнопку "Поиск".

    ОР:
    - URL содержит параметр salary_min с введённым значением.
    """
    salary = "1000"

    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step(f"Шаг 2: Ввод минимальной зарплаты {salary}"):
        public_resume_search_page.salary_min_input.fill(salary)

    with allure.step("Шаг 3: Применение фильтра"):
        public_resume_search_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит salary_min=1000"):
        expect(guest_page).to_have_url(re.compile(rf"salary_min={salary}"))


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Фильтр по статусу соискателя")
@allure.title("Бизнес-кейс: Раскрытие спойлера 'Статус соискателя' и применение фильтра")
def test_expand_status_filter_and_apply(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Раскрытие спойлера "Статус соискателя", выбор значения из
    нативного select и применение фильтра.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Кликнуть по заголовку спойлера "Статус соискателя" для его раскрытия.
    3. Выбрать значение "Активно ищу работу" из select.
    4. Нажать кнопку "Поиск".

    ОР:
    - Спойлер раскрывается: select статуса становится видимым.
    - URL содержит параметр status=0.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("Шаг 2: Раскрытие спойлера 'Статус соискателя'"):
        public_resume_search_page.expand_filter(public_resume_search_page.status_header)
        expect(public_resume_search_page.status_select).to_be_visible(timeout=3000)

    with allure.step("Шаг 3: Выбор статуса 'Активно ищу работу'"):
        public_resume_search_page.status_select.select_option("0")

    with allure.step("Шаг 4: Применение фильтра"):
        public_resume_search_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит status=0"):
        expect(guest_page).to_have_url(re.compile(r"status=0"))


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Дополнительные параметры")
@allure.title("Бизнес-кейс: Раскрытие 'Дополнительных параметров' и выбор чекбокса переезда")
def test_expand_additional_params_and_apply_relocate(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Раскрытие спойлера "Дополнительные параметры", установка
    чекбокса "Рассматривает вариант переезда" и применение фильтра.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Кликнуть по заголовку "Дополнительные параметры".
    3. Установить чекбокс "Рассматривает вариант трудоустройства в другой местности".
    4. Нажать "Поиск".

    ОР:
    - Чекбокс становится видимым после раскрытия спойлера.
    - URL содержит agree_to_relocate=on.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("Шаг 2: Раскрытие спойлера 'Дополнительные параметры'"):
        public_resume_search_page.expand_filter(public_resume_search_page.additional_header)
        expect(public_resume_search_page.agree_to_relocate_checkbox).to_be_visible(timeout=3000)

    with allure.step("Шаг 3: Установка чекбокса переезда"):
        # dispatch_event обходит перехват кликов лейблом и фиксированным хедером
        public_resume_search_page.agree_to_relocate_checkbox.dispatch_event("click")
        expect(public_resume_search_page.agree_to_relocate_checkbox).to_be_checked()

    with allure.step("Шаг 4: Применение фильтра"):
        public_resume_search_page.apply_filter_and_wait()

    with allure.step("ОР: URL содержит agree_to_relocate=on"):
        expect(guest_page).to_have_url(re.compile(r"agree_to_relocate=on"))


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Ограничения для гостя")
@allure.title("Бизнес-кейс: Кнопки 'Откликнуться' и 'Контакты' заблокированы для неавторизованного пользователя")
def test_action_buttons_disabled_for_guest(public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Проверка, что кнопки взаимодействия с резюме недоступны
    для неавторизованного пользователя.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Проверить первую карточку резюме.

    ОР:
    - Кнопка "Откликнуться" имеет класс disabled и недоступна для клика.
    - Кнопка "Контакты" имеет класс disabled и недоступна для клика.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("ОР 1: Кнопка 'Откликнуться' заблокирована"):
        first_apply = public_resume_search_page.apply_buttons.first
        expect(first_apply).to_be_visible()
        expect(first_apply).to_have_class(re.compile(r"\bdisabled\b"))

    with allure.step("ОР 2: Кнопка 'Контакты' заблокирована"):
        first_contacts = public_resume_search_page.contacts_buttons.first
        expect(first_contacts).to_be_visible()
        expect(first_contacts).to_have_class(re.compile(r"\bdisabled\b"))


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Ограничения для гостя")
@allure.title("Бизнес-кейс: Блок 'Контактное лицо по резюме' не отображается для неавторизованного пользователя")
def test_contact_person_block_hidden_for_guest(public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Проверка, что контактная информация соискателя скрыта
    для неавторизованного пользователя.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Убедиться, что на странице нет видимого блока "Контактное лицо по резюме".

    ОР:
    - Блок с заголовком "Контактное лицо по резюме" отсутствует в видимой
      части страницы (контактные данные не передаются в HTML для гостя).
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("ОР: Блок 'Контактное лицо по резюме' не виден"):
        expect(public_resume_search_page.contact_person_block).not_to_be_visible()


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Настройки отображения")
@allure.title("Бизнес-кейс: Изменение количества карточек на странице через select 'Показывать по'")
def test_paginate_by_select_changes_url(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Изменение количества отображаемых резюме на странице через
    выпадающий список "Показывать по" (submit-on-change).

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Изменить значение select с 10 до 20.

    ОР:
    - Страница перезагружается с параметром paginate_by=20 в URL.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("Шаг 2: Выбор 20 карточек на странице"):
        public_resume_search_page.paginate_select.select_option("20")
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит paginate_by=20"):
        expect(guest_page).to_have_url(re.compile(r"paginate_by=20"))


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Настройки отображения")
@allure.title("Бизнес-кейс: Изменение порядка сортировки результатов")
def test_sort_by_changes_url(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Выбор нового значения сортировки и проверка обновления URL
    (submit-on-change).

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Изменить сортировку на "зарплате по возрастанию".

    ОР:
    - URL содержит sort_by=salary_asc.
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("Шаг 2: Изменение сортировки на 'зарплате по возрастанию'"):
        public_resume_search_page.sort_select.select_option("salary_asc")
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL содержит sort_by=salary_asc"):
        expect(guest_page).to_have_url(re.compile(r"sort_by=salary_asc"))


@pytest.mark.public_resume_search
@allure.epic("Публичный поиск резюме")
@allure.feature("Сброс фильтров")
@allure.title("Бизнес-кейс: Сброс применённых фильтров по кнопке 'Сбросить фильтр'")
def test_reset_filter_clears_search(guest_page: Page, public_resume_search_page: PublicResumeSearchPage):
    """
    Бизнес-кейс: Применение фильтра по профессии, затем сброс через
    кнопку "Сбросить фильтр" — проверка возврата к чистому URL.

    Шаги:
    1. Перейти на страницу поиска резюме.
    2. Ввести значение в поле профессии и применить поиск.
    3. Нажать "Сбросить фильтр".

    ОР:
    - URL становится /registration/resume-search/? (все параметры сброшены).
    - На странице отображаются карточки резюме (список не пустой).
    """
    with allure.step("Шаг 1: Переход на страницу"):
        public_resume_search_page.navigate()

    with allure.step("Шаг 2: Применение фильтра по профессии"):
        public_resume_search_page.profession_input.fill("Программист")
        public_resume_search_page.search_btn_main.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("Шаг 3: Нажатие 'Сбросить фильтр'"):
        public_resume_search_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("domcontentloaded")

    with allure.step("ОР: URL сброшен, результаты отображаются"):
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/resume-search/?")
        expect(public_resume_search_page.resume_cards.first).to_be_visible()
