import pytest
from playwright.sync_api import Page, expect
from pages.profile_page import ProfilePage
from utils.helpers import calculate_expected_age, generate_test_date
from datetime import datetime, timedelta


def test_check_profile_default_values(open_profile_page: Page, app_config):
    """Smoke-тест: проверяет корректность отображения дефолтных ФИО соискателя из конфига."""
    profile = ProfilePage(open_profile_page)
    profile_data = app_config["default_profile"]

    expect(profile.last_name_input).to_have_value(profile_data["last_name"])
    expect(profile.first_name_input).to_have_value(profile_data["first_name"])
    expect(profile.middle_name_input).to_have_value(profile_data["middle_name"])


def test_edit_fio_block(open_profile_page: Page, app_config):
    """Функциональный тест: изменяет ФИО соискателя, сохраняет и восстанавливает дефолт."""
    profile = ProfilePage(open_profile_page)
    profile_data = app_config["default_profile"]
    test_fio = app_config["profile_test_data"]["edit_fio"]

    # Шаг 1: Изменяем данные на тестовые
    profile.fill_field_safely(profile.last_name_input, test_fio["last_name"])
    profile.fill_field_safely(profile.first_name_input, test_fio["first_name"])
    profile.fill_field_safely(profile.middle_name_input, test_fio["middle_name"])
    profile.save_changes()

    # Проверка ОР 1: Значения в полях действительно изменились на тестовые
    expect(profile.last_name_input).to_have_value(test_fio["last_name"])
    expect(profile.first_name_input).to_have_value(test_fio["first_name"])
    expect(profile.middle_name_input).to_have_value(test_fio["middle_name"])

    # Шаг 2: Восстанавливаем исходные дефолтные данные назад
    profile.fill_field_safely(profile.last_name_input, profile_data["last_name"])
    profile.fill_field_safely(profile.first_name_input, profile_data["first_name"])
    profile.fill_field_safely(profile.middle_name_input, profile_data["middle_name"])
    profile.save_changes()

    # Проверка ОР 2: Данные на странице гарантированно вернулись к исходному состоянию
    expect(profile.last_name_input).to_have_value(profile_data["last_name"])
    expect(profile.first_name_input).to_have_value(profile_data["first_name"])
    expect(profile.middle_name_input).to_have_value(profile_data["middle_name"])


def test_edit_status_dropdown(open_profile_page: Page, test_status):
    """Функциональный тест: параметризованно изменяет статус соискателя, проверяет и восстанавливает дефолт."""
    profile = ProfilePage(open_profile_page)
    default_status = "Рассматриваю предложения"

    # Шаг 1: Честно выбираем тестовый статус (даже если он совпадает с текущим) и сохраняем
    profile.select_from_dropdown(profile.status_dropdown, test_status)
    profile.save_changes()

    # Проверка ОР 1: На странице после перезагрузки отображается новый статус
    expect(profile.status_dropdown).to_have_text(test_status)

    # Шаг 2: Восстанавливаем дефолтный статус
    profile.select_from_dropdown(profile.status_dropdown, default_status)
    profile.save_changes()

    # Проверка ОР 2: Статус успешно вернулся в исходное состояние
    expect(profile.status_dropdown).to_have_text(default_status)


def test_edit_gender_radio(open_profile_page: Page):
    """Функциональный тест: динамически изменяет пол соискателя и восстанавливает исходный."""
    profile = ProfilePage(open_profile_page)

    # 🎯 УМНОЕ ОПРЕДЕЛЕНИЕ: смотрим, какой пол сейчас реально выбран на странице
    if profile.gender_male_input.is_checked():
        initial_gender = "M"
        test_gender = "F"
    else:
        initial_gender = "F"
        test_gender = "M"

    # Шаг 1: Меняем пол на противоположный и сохраняем
    profile.select_gender(test_gender)
    profile.save_changes()

    # Проверка ОР 1: Радиокнопка тестового пола теперь выбрана на странице после перезагрузки
    if test_gender == "M":
        expect(profile.gender_male_input).to_be_checked()
    else:
        expect(profile.gender_female_input).to_be_checked()

    # Шаг 2: Восстанавливаем исходный пол обратно
    profile.select_gender(initial_gender)
    profile.save_changes()

    # Проверка ОР 2: Пол успешно вернулся к исходному состоянию
    if initial_gender == "M":
        expect(profile.gender_male_input).to_be_checked()
    else:
        expect(profile.gender_female_input).to_be_checked()


def test_edit_date_of_birth_manual(open_profile_page: Page, app_config):
    """Тест: ручной ввод даты рождения через точки и проверка изменения возраста."""
    profile = ProfilePage(open_profile_page)

    # 1. Данные из конфига и расчет исходного возраста
    default_date = app_config["default_profile"]["date_of_birth"]  # "05.02.2008"
    expected_default_age = calculate_expected_age(default_date)

    # 2. Генерируем тестовую дату через хелпер (на 5 лет старше)
    test_date = generate_test_date(default_date, years_diff=-5)  # "05.02.2003"
    expected_test_age = calculate_expected_age(test_date)

    # --- Шаг 1: Ручной ввод тестовой даты ---
    profile.date_of_birth_input.click()
    open_profile_page.keyboard.press("Control+A")
    open_profile_page.keyboard.press("Backspace")

    profile.date_of_birth_input.press_sequentially(test_date, delay=50)
    profile.age_display.click()
    profile.save_changes()

    # ПЕРЕВЕРТЫШИ ДЛЯ ПРОВЕРКИ: переводим ДД.ММ.ГГГГ в ГГГГ-ММ-ДД для браузера
    test_date_iso = "-".join(test_date.split(".")[::-1])  # Станет '2003-02-05'
    default_date_iso = "-".join(default_date.split(".")[::-1])  # Станет '2008-02-05'

    # Теперь проверяем значение в формате ISO
    expect(profile.date_of_birth_input).to_have_value(test_date_iso)
    expect(profile.age_display).to_have_text(expected_test_age)

    # --- Шаг 2: Восстановление исходного дефолта ---
    profile.date_of_birth_input.click()
    open_profile_page.keyboard.press("Control+A")
    open_profile_page.keyboard.press("Backspace")

    profile.date_of_birth_input.press_sequentially(default_date, delay=50)
    profile.age_display.click()
    profile.save_changes()

    # Проверяем возвращение к дефолту тоже в формате ISO
    expect(profile.date_of_birth_input).to_have_value(default_date_iso)
    expect(profile.age_display).to_have_text(expected_default_age)


def test_edit_date_of_birth_via_calendar_ui(open_profile_page: Page, app_config):
    """Функциональный тест: честное изменение даты через интерфейс всплывающего календаря."""
    profile = ProfilePage(open_profile_page)

    # Подготовка ожидаемых данных для проверки
    default_date_str = app_config["default_profile"]["date_of_birth"]  # "05.02.2008"
    default_date_obj = datetime.strptime(default_date_str, "%d.%m.%Y")
    default_date_iso = default_date_obj.strftime("%Y-%m-%d")

    # --- Шаг 1: Открытие календаря и выбор дня стрелками ---
    profile.date_of_birth_input.click()

    # Честно вызываем плашку встроенного календаря на экран
    open_profile_page.keyboard.press("Alt+ArrowDown")
    open_profile_page.wait_for_timeout(500)

    # Фокус уже на дате 05.02.2008. Нажимаем "Стрелку влево", чтобы выбрать 04.02.2008
    open_profile_page.keyboard.press("ArrowLeft")
    open_profile_page.wait_for_timeout(300)

    open_profile_page.keyboard.press("Enter")
    open_profile_page.wait_for_timeout(500)

    # Вместо клика мыши нажимаем Tab, чтобы просто убрать фокус из поля даты
    # Экран при этом останется абсолютно неподвижным!
    open_profile_page.keyboard.press("Tab")
    open_profile_page.wait_for_timeout(500)

    # Спокойно сохраняем изменения
    profile.save_changes()

    # --- Шаг 2: Восстановление исходного дефолта (ручным вводом для стабильности) ---
    profile.date_of_birth_input.click()
    open_profile_page.keyboard.press("Control+A")
    open_profile_page.keyboard.press("Backspace")

    profile.date_of_birth_input.press_sequentially(default_date_str, delay=50)
    profile.age_display.click()
    profile.save_changes()

    # Проверяем возвращение к исходному состоянию
    expect(profile.date_of_birth_input).to_have_value(default_date_iso)


def test_edit_education_dropdown(open_profile_page: Page, app_config, test_education):
    """Функциональный тест: параметризованно изменяет уровень образования и восстанавливает дефолт."""
    profile = ProfilePage(open_profile_page)
    default_education = app_config["default_profile"]["education"]

    # Шаг 1: Изменяем на тестовое значение из конфига
    profile.select_from_dropdown(profile.education_dropdown, test_education)
    profile.save_changes()
    expect(profile.education_dropdown).to_have_text(test_education)

    # Шаг 2: Возвращаем дефолтное значение обратно
    profile.select_from_dropdown(profile.education_dropdown, default_education)
    profile.save_changes()
    expect(profile.education_dropdown).to_have_text(default_education)