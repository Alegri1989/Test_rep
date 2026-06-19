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
    with allure.step("Шаг 1: Переход на страницу поиска вакансий"):
        vacancy_page.navigate()
        vacancy_page.region_dropdown.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Каскадный ручной выбор Витебской области, Полоцкого района и г. Полоцк"):
        # 1 уровень: Область
        vacancy_page.select_from_dropdown(vacancy_page.region_dropdown, "Витебская")
        guest_page.wait_for_timeout(1500)

        # 2 уровень: Район
        vacancy_page.select_from_dropdown(vacancy_page.district_dropdown, "Полоцкий")
        guest_page.wait_for_timeout(1500)

        # 3 уровень: Город
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
    with allure.step("Шаг 1: Переход на страницу поиска и заполнение поля 'Зарплата От'"):
        vacancy_page.navigate()
        vacancy_page.salary_min_input.wait_for(state="visible", timeout=5000)
        vacancy_page.salary_min_input.click()
        vacancy_page.salary_min_input.fill("1000")

    with allure.step("Шаг 2: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка соответствия уровня зарплаты на всех карточках страницы"):
        # Находим текстовые блоки с зарплатами на карточках
        salary_elements = guest_page.locator("text=/руб./").filter(visible=True)
        salary_elements.first.wait_for(state="visible", timeout=5000)

        count = salary_elements.count()
        assert count > 0, "Ошибка: фильтрация по зарплате вернула пустой список"

        for i in range(count):
            salary_text = salary_elements.nth(i).text_content().replace(" ", "")
            # Ищем все числа в блоке строки зарплаты (например, "1000–1500руб.")
            salary_numbers = [int(s) for s in re.findall(r"\d+", salary_text)]

            if salary_numbers:
                # Если указан диапазон, то максимальная планка должна быть не меньше 1000
                max_salary_on_card = max(salary_numbers)
                assert max_salary_on_card >= 1000, (
                    f"Ошибка: на позиции {i + 1} найдена вакансия с неподходящей зарплатой: {salary_numbers}"
                )


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по диапазону Ставки (0.25 - 0.5)")
def test_guest_filter_by_wage_rate_range(guest_page: Page, vacancy_page: VacancySearchPage):
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
        # Ищем строго тег параграфа с текстом "Одна смена" внутри детальной карточки
        detail_mode_paragraph = guest_page.locator("div.col-6 p:has-text('Одна смена')").first
        expect(detail_mode_paragraph).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по названию Нанимателя")
def test_guest_filter_by_employer_name(guest_page: Page, vacancy_page: VacancySearchPage, app_config):
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
        # Ищем строго тег параграфа с текстом "Постоянная" внутри детальной карточки по вашей вёрстке
        detail_nature_paragraph = guest_page.locator("div.col-6 p:has-text('Постоянная')").first
        expect(detail_nature_paragraph).to_be_visible(timeout=5000)

@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Уровню образования")
def test_guest_filter_by_education(guest_page: Page, vacancy_page: VacancySearchPage):
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
        # Проверяем, что внутри карточки в параграфе указано именно выбранное образование
        detail_education_paragraph = guest_page.locator("div.col-6 p:has-text('Высшее')").first
        expect(detail_education_paragraph).to_be_visible(timeout=5000)

@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий для категорий граждан (Инвалид III группы)")
def test_guest_filter_by_citizens_category(guest_page: Page, vacancy_page: VacancySearchPage):
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
        # Проверяем, что на детальной странице отображается текст выбранной категории граждан
        detail_category_text = guest_page.locator("text=Инвалид III группы").first
        expect(detail_category_text).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Гибким навыкам (Тайм-менеджмент)")
def test_guest_filter_by_soft_skills(guest_page: Page, vacancy_page: VacancySearchPage):
    with allure.step("Шаг 1: Переход на страницу поиска и раскрытие спойлера гибких навыков"):
        vacancy_page.navigate()
        vacancy_page.open_spoiler_if_hidden("Гибкие навыки", vacancy_page.soft_skills_dropdown)

    with allure.step("Шаг 2: Выбор навыка 'Тайм-менеджмент' через Select2"):
        vacancy_page.select_from_dropdown(vacancy_page.soft_skills_dropdown, "Тайм-менеджмент")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка сохранения выбранного тега на левой панели"):
        # Проверяем, что после обновления страницы тег навыка остался активным в блоке фильтра
        expect(vacancy_page.soft_skills_dropdown).to_have_text(re.compile("Тайм-менеджмент.*"))

        # Гарантируем, что система перестроила DOM и успешно вывела список результатов
        first_card = guest_page.locator("a.debounced-link").first
        expect(first_card).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Периоду публикации (Месяц)")
def test_guest_filter_by_search_period(guest_page: Page, vacancy_page: VacancySearchPage):
    with allure.step("Шаг 1: Переход на страницу поиска вакансий"):
        vacancy_page.navigate()
        vacancy_page.search_period_dropdown.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Выбор периода 'Месяц' в стандартном HTML-селекте"):
        # Работаем напрямую с нативным селектом по его видимому тексту
        vacancy_page.search_period_dropdown.select_option(label="Месяц")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Проверка соответствия периода публикации на первой карточке"):
        # Находим блок времени обновления на первой видимой карточке выдачи ГСЗ
        first_card_time = guest_page.locator("text=/назад/").first
        first_card_time.wait_for(state="visible", timeout=5000)

        time_text = first_card_time.text_content().strip()
        # Извлекаем число дней или минут (например, "21 дней назад" или "3 минут назад")
        numbers = [int(s) for s in re.findall(r"\d+", time_text)]

        if numbers and "дней" in time_text:
            days_ago = numbers[0]
            assert days_ago <= 31, f"Ошибка: найдена старая вакансия, обновленная {days_ago} дней назад"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Периоду публикации (Месяц)")
def test_guest_filter_by_search_period(guest_page: Page, vacancy_page: VacancySearchPage):
    with allure.step("Шаг 1: Переход на страницу поиска вакансий"):
        vacancy_page.navigate()
        # Ждем только прикрепления к DOM-структуре страницы, не дожидаясь видимости
        vacancy_page.search_period_dropdown.wait_for(state="attached", timeout=5000)

    with allure.step("Шаг 2: Принудительный выбор периода 'Месяц' в скрытом селекте"):
        # Выбираем опцию по значению "3" принудительно через флаг force=True
        vacancy_page.search_period_dropdown.select_option(value="3", force=True)
        # Генерируем JS-событие изменения, чтобы страница зафиксировала выбор
        vacancy_page.search_period_dropdown.dispatch_event("change")

    with allure.step("Шаг 3: Применение фильтра через хелпер"):
        apply_vacancy_filter_and_wait(guest_page, vacancy_page)

    with allure.step("ОР 1: Верификация передачи параметра периода в URL страницы"):
        # Декодируем текущий URL из адресной строки браузера
        current_url_decoded = unquote(guest_page.url)

        # Проверяем, что в URL зафиксировался правильный query-параметр
        assert "search_period=3" in current_url_decoded, (
            f"Ошибка: неверный параметр периода публикации в URL. Текущий URL: {current_url_decoded}"
        )

        # Убеждаемся, что новые результаты успешно отрисовались на экране
        first_card = guest_page.locator("a.debounced-link").first
        expect(first_card).to_be_visible(timeout=5000)

@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация вакансий по Сфере деятельности (Высший менеджмент)")
def test_guest_filter_by_activity_sphere(guest_page: Page, vacancy_page: VacancySearchPage):
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
        # Проверяем наличие точного тега параграфа с выбранной сферой на детальной странице
        detail_sphere_paragraph = guest_page.locator("div.col-6 p:has-text('Высший менеджмент')").first
        expect(detail_sphere_paragraph).to_be_visible(timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Фильтрация по дополнительным параметрам (Молодежь 14-16 лет)")
def test_guest_filter_by_additional_params_students(guest_page: Page, vacancy_page: VacancySearchPage):
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