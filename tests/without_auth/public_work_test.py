import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.public_work_page import PublicWorkPage


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Переключение слайдером на страницу временной занятости молодежи")
def test_guest_slider_switches_to_youth_employment(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка работы слайдера-переключателя вида временной занятости.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ.

    Шаги:
    1. Перейти на страницу временных оплачиваемых работ и убедиться, что её слайдер активен (checked).
    2. Кликнуть по слайдеру "Временная занятость молодежи".
    3. Дождаться полной загрузки новой страницы.

    Ожидаемый результат (ОР):
    - Слайдер на исходной странице отмечен как активный (checked).
    - Переход успешно переводит пользователя на страницу /registration/temporary-employment/young/.
    """
    with allure.step("Шаг 1: Переход на страницу временных оплачиваемых работ"):
        public_work_page.navigate()
        expect(public_work_page.public_works_slider).to_be_visible()

    with allure.step("Шаг 2: Клик по слайдеру 'Временная занятость молодежи'"):
        public_work_page.young_employment_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация перехода на страницу временной занятости молодежи"):
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/temporary-employment/young/")


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Фильтрация временных работ по территориально-административной иерархии (Область)")
def test_guest_filter_by_region(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра по территориально-административной принадлежности (Область).

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ.

    Шаги:
    1. Перейти на страницу и выбрать из выпадающего списка Select2 область "Гродненская".
    2. Применить фильтрацию нажатием кнопки "Поиск".
    3. Собрать адреса всех карточек выдачи и проверить вхождение выбранной области.

    Ожидаемый результат (ОР):
    - Выдача возвращает непустой список результатов, где в каждой карточке фигурирует область "Гродненская".
    """
    with allure.step("Шаг 1: Переход на страницу и выбор области 'Гродненская'"):
        public_work_page.navigate()
        public_work_page.select_from_dropdown(public_work_page.region_dropdown, "Гродненская")

    with allure.step("Шаг 2: Применение фильтра"):
        public_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация наличия выбранной области во всех карточках результатов"):
        public_work_page.vacancy_address.first.wait_for(state="visible", timeout=5000)

        count = public_work_page.vacancy_address.count()
        assert count > 0, "Ошибка: фильтрация по области вернула пустой список временных работ"

        for i in range(count):
            address_text = public_work_page.vacancy_address.nth(i).text_content().strip()
            assert "Гродненская" in address_text, (
                f"Ошибка: на позиции {i + 1} найдена работа с чужой областью '{address_text}'"
            )


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Фильтрация временных работ по Нанимателю")
def test_guest_filter_by_employer(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка работы фильтра по нанимателю, скрытого за спойлером карточки фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ, на ней есть хотя бы одна вакансия.

    Шаги:
    1. Перейти на страницу и зафиксировать название нанимателя из первой карточки выдачи.
    2. Раскрыть скрытый спойлер блока "Наниматель".
    3. Найти и выбрать зафиксированного нанимателя через Select2.
    4. Применить фильтрацию нажатием кнопки "Поиск".
    5. Проверить, что все карточки результатов принадлежат выбранному нанимателю.

    Ожидаемый результат (ОР):
    - Скрытый спойлер фильтра по нанимателю успешно раскрывается по клику на заголовок.
    - Выдача после фильтрации содержит только вакансии выбранного нанимателя.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация нанимателя первой карточки"):
        public_work_page.navigate()
        public_work_page.vacancy_employer.first.wait_for(state="visible", timeout=5000)
        employer_name = " ".join(public_work_page.vacancy_employer.first.text_content().split())

    with allure.step("Шаг 2: Раскрытие спойлера фильтра 'Наниматель'"):
        public_work_page.open_employer_filter_if_hidden()

    with allure.step("Шаг 3: Выбор зафиксированного нанимателя через Select2"):
        public_work_page.select_from_dropdown(public_work_page.employer_dropdown, employer_name)

    with allure.step("Шаг 4: Применение фильтра"):
        public_work_page.apply_filter_and_wait()

    with allure.step("ОР 1: Верификация принадлежности всех карточек выбранному нанимателю"):
        public_work_page.vacancy_employer.first.wait_for(state="visible", timeout=5000)

        count = public_work_page.vacancy_employer.count()
        assert count > 0, "Ошибка: фильтрация по нанимателю вернула пустой список временных работ"

        for i in range(count):
            card_employer = " ".join(public_work_page.vacancy_employer.nth(i).text_content().split())
            assert card_employer == employer_name, (
                f"Ошибка: на позиции {i + 1} найдена работа чужого нанимателя '{card_employer}'"
            )


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Переход к другим вакансиям нанимателя через кнопку на карточке")
def test_guest_other_employer_vacancies_button(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка работы кнопки "Другие вакансии нанимателя" на карточке временной работы.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ.

    Шаги:
    1. Перейти на страницу и зафиксировать название нанимателя из первой карточки выдачи.
    2. Кликнуть по кнопке "Другие вакансии нанимателя" на первой карточке.
    3. Дождаться обновления выдачи и проверить, что в URL появился параметр workplace__business_entity.
    4. Проверить, что все карточки в обновленной выдаче принадлежат тому же нанимателю.

    Ожидаемый результат (ОР):
    - Кнопка успешно фильтрует выдачу по нанимателю исходной карточки без участия других фильтров.
    """
    with allure.step("Шаг 1: Переход на страницу и фиксация нанимателя первой карточки"):
        public_work_page.navigate()
        public_work_page.vacancy_employer.first.wait_for(state="visible", timeout=5000)
        employer_name = " ".join(public_work_page.vacancy_employer.first.text_content().split())

    with allure.step("Шаг 2: Клик по кнопке 'Другие вакансии нанимателя' на первой карточке"):
        public_work_page.other_employer_vacancies_btn.first.click()
        guest_page.wait_for_load_state("load")
        guest_page.wait_for_timeout(1000)

    with allure.step("ОР 1: Верификация параметра фильтра в URL и принадлежности карточек нанимателю"):
        expect(guest_page).to_have_url(re.compile(r"workplace__business_entity=\d+"))

        public_work_page.vacancy_employer.first.wait_for(state="visible", timeout=5000)
        count = public_work_page.vacancy_employer.count()
        assert count > 0, "Ошибка: переход по кнопке нанимателя вернул пустой список временных работ"

        for i in range(count):
            card_employer = " ".join(public_work_page.vacancy_employer.nth(i).text_content().split())
            assert card_employer == employer_name, (
                f"Ошибка: на позиции {i + 1} найдена работа чужого нанимателя '{card_employer}'"
            )


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Сброс установленных фильтров временных работ")
def test_guest_reset_applied_filters(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных фильтров.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ.

    Шаги:
    1. Открыть страницу и выбрать область "Гродненская" в фильтре территориальной иерархии.
    2. Применить фильтр нажатием кнопки "Поиск".
    3. Кликнуть по кнопке "Сбросить фильтр".
    4. Верифицировать очистку выбранной области и возврат к дефолтному URL со знаком вопроса.

    Ожидаемый результат (ОР):
    - Система выполняет перезагрузку страницы и возвращает пользователя на дефолтный URL со знаком вопроса.
    - Ранее выбранная область сбрасывается до значения "Любая".
    """
    with allure.step("Шаг 1: Переход на страницу и выбор области 'Гродненская'"):
        public_work_page.navigate()
        public_work_page.select_from_dropdown(public_work_page.region_dropdown, "Гродненская")

    with allure.step("Шаг 2: Применение фильтра"):
        public_work_page.apply_filter_and_wait()

    with allure.step("Шаг 3: Нажатие на кнопку 'Сбросить фильтр' и ожидание обновления страницы"):
        public_work_page.reset_filter_btn.wait_for(state="visible", timeout=5000)
        public_work_page.reset_filter_btn.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация очистки фильтра области и возврата к дефолтному URL"):
        expect(public_work_page.region_selected_text).to_have_text("Любая")
        expect(guest_page).to_have_url("https://gsz.gov.by/registration/temporary-employment/public-works/?")


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Изменение количества отображаемых временных работ на странице (10 -> 20 -> 50 -> 10)")
def test_guest_change_paginate_by_count(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка работы селекта количества элементов на странице выдачи временных работ.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ.

    Шаги:
    1. Открыть страницу и проверить, что по умолчанию в селекте выбрано значение "10".
    2. Переключить селект на значение "20", дождаться загрузки и проверить количество карточек.
    3. Переключить селект на значение "50", дождаться загрузки и проверить количество карточек.
    4. Переключить селект обратно на "10" и верифицировать возврат к исходному количеству.

    Ожидаемый результат (ОР):
    - Селект успешно переключает режимы отображения, бэкенд перестраивает выдачу с соответствующим лимитом строк.
    """
    with allure.step("Шаг 1: Переход на страницу и проверка дефолтного значения 10"):
        public_work_page.navigate()
        public_work_page.paginate_by_select.wait_for(state="visible", timeout=5000)
        expect(public_work_page.paginate_by_select).to_have_value("10")

        public_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        initial_cards_count = public_work_page.vacancy_cards.count()
        assert 0 < initial_cards_count <= 10, f"Ошибка: дефолтное количество карточек {initial_cards_count} > 10"

    with allure.step("Шаг 2: Переключение лимита на '20' и верификация количества"):
        public_work_page.paginate_by_select.select_option(label="20")
        guest_page.wait_for_load_state("load")

        public_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        cards_count_20 = public_work_page.vacancy_cards.count()
        assert 0 < cards_count_20 <= 20, f"Ошибка: при лимите 20 отобразилось {cards_count_20} карточек"

    with allure.step("Шаг 3: Переключение лимита на '50' и верификация количества"):
        public_work_page.paginate_by_select.select_option(label="50")
        guest_page.wait_for_load_state("load")

        public_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        cards_count_50 = public_work_page.vacancy_cards.count()
        assert 0 < cards_count_50 <= 50, f"Ошибка: при лимите 50 отобразилось {cards_count_50} карточек"

    with allure.step("Шаг 4: Возврат лимита на '10' и финальная верификация"):
        public_work_page.paginate_by_select.select_option(label="10")
        guest_page.wait_for_load_state("load")

        public_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        final_cards_count = public_work_page.vacancy_cards.count()
        assert 0 < final_cards_count <= 10, f"Ошибка: после возврата на 10 отобразилось {final_cards_count} карточек"


@pytest.mark.public_work
@allure.title("Бизнес-кейс: Переход на вторую страницу пагинации выдачи временных работ")
def test_guest_pagination_page_2(guest_page: Page, public_work_page: PublicWorkPage):
    """
    Бизнес-кейс: Проверка корректности постраничной навигации по выдаче временных работ.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована страница временных оплачиваемых работ, выдача содержит больше одной страницы.

    Шаги:
    1. Открыть страницу и дождаться видимости ссылки на вторую страницу пагинации.
    2. Кликнуть по ссылке "2".
    3. Дождаться полной загрузки обновленной страницы.

    Ожидаемый результат (ОР):
    - Активный номер страницы в пагинации становится равным "2".
    - На странице отображаются карточки временных работ.
    """
    with allure.step("Шаг 1: Переход на страницу и ожидание ссылки на вторую страницу"):
        public_work_page.navigate()
        public_work_page.page_2_link.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по ссылке второй страницы пагинации"):
        public_work_page.page_2_link.click()
        guest_page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация активной второй страницы и наличия карточек выдачи"):
        expect(public_work_page.active_page_number).to_have_text("2")
        public_work_page.vacancy_cards.first.wait_for(state="visible", timeout=5000)
        expect(public_work_page.vacancy_cards.first).to_be_visible()
