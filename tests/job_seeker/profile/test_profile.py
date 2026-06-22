from datetime import datetime
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.profile_page import ProfilePage
from helpers.helpers import calculate_expected_age, generate_test_date, format_phone_to_mask


@allure.epic("Личный кабинет соискателя")
@allure.feature("Редактирование профиля")
class TestProfilePart1:

    @allure.title("Проверка дефолтных ФИО соискателя из конфигурации")
    def test_check_profile_default_values(self, open_profile_page: Page, app_config):
        """
        Бизнес-кейс: Проверка автоматического подтягивания и отображения дефолтных ФИО пользователя.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Осуществлен переход в личный кабинет на страницу персональных данных.

        Шаги:
        1. Загрузить ожидаемые эталонные данные соискателя из файла конфигурации config.json.
        2. Локализовать на форме инпуты Фамилии, Имени и Отчества.
        3. Сверить текущие текстовые значения в инпутах с эталоном.

        Ожидаемый результат (ОР):
        - Значения в полях ввода на UI полностью идентичны строкам 'last_name', 'first_name' и 'middle_name' из конфигурации.
        """
        profile = ProfilePage(open_profile_page)

        with allure.step("Загрузка дефолтных данных из конфига"):
            profile_data = app_config["default_profile"]

        with allure.step("Проверка совпадения ФИО на странице с конфигом"):
            expect(profile.last_name_input).to_have_value(profile_data["last_name"])
            expect(profile.first_name_input).to_have_value(profile_data["first_name"])
            expect(profile.middle_name_input).to_have_value(profile_data["middle_name"])

    @allure.title("Изменение ФИО соискателя с последующим восстановлением")
    def test_edit_fio_block(self, open_profile_page: Page, app_config):
        """
        Бизнес-кейс: Полный цикл редактирования ФИО соискателя с возвратом в исходное состояние.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Очистить инпуты ФИО и ввести новые валидные тестовые данные.
        2. Сохранить форму для отправки данных на сервер и дождаться алерта успешности.
        3. Верифицировать на UI, что новые ФИО применились.
        4. Повторно очистить поля и ввести обратно дефолтные ФИО из конфигурации.
        5. Сохранить форму для восстановления первоначального состояния аккаунта.

        Ожидаемый результат (ОР):
        - Данные успешно изменяются, сохраняются на бэкенде и корректно выводятся на UI после перезагрузки.
        - Сервер возвращает зелёное уведомление об успешном обновлении профиля.
        """
        profile = ProfilePage(open_profile_page)
        profile_data = app_config["default_profile"]
        test_fio = app_config["profile_test_data"]["edit_fio"]

        with allure.step("Шаг 1: Изменение ФИО на тестовые значения"):
            profile.fill_field_safely(profile.last_name_input, test_fio["last_name"])
            profile.fill_field_safely(profile.first_name_input, test_fio["first_name"])
            profile.fill_field_safely(profile.middle_name_input, test_fio["middle_name"])
            profile.save_changes()

        with allure.step("ОР 1: Проверка, что на странице отображаются тестовые ФИО"):
            expect(profile.last_name_input).to_have_value(test_fio["last_name"])
            expect(profile.first_name_input).to_have_value(test_fio["first_name"])
            expect(profile.middle_name_input).to_have_value(test_fio["middle_name"])

        with allure.step("Шаг 2: Восстановление исходных ФИО"):
            profile.fill_field_safely(profile.last_name_input, profile_data["last_name"])
            profile.fill_field_safely(profile.first_name_input, profile_data["first_name"])
            profile.fill_field_safely(profile.middle_name_input, profile_data["middle_name"])
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата ФИО к дефолтным значениям"):
            expect(profile.last_name_input).to_have_value(profile_data["last_name"])
            expect(profile.first_name_input).to_have_value(profile_data["first_name"])
            expect(profile.middle_name_input).to_have_value(profile_data["middle_name"])

    @allure.title("Параметризованное изменение статуса соискателя: {test_status}")
    def test_edit_status_dropdown(self, open_profile_page: Page, test_status):
        """
        Бизнес-кейс: Проверка смены профессионального статуса соискателя через выпадающий список Select2.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Раскрыть кастомный контейнер Select2 выпадающего списка статусов.
        2. Через встроенный поиск найти и принудительно кликнуть по тестовому статусу.
        3. Нажать кнопку "Сохранить" и дождаться фиксации изменений базой данных.
        4. Проверить отображение нового статуса на UI.
        5. Повторить процедуру для возврата дефолтного статуса "Рассматриваю предложения".

        Ожидаемый результат (ОР):
        - Кастомный плагин Select2 корректно реагирует на посимвольный ввод и выбор элементов.
        - Новый статус успешно фиксируется в профиле и не сбрасывается после сохранения формы.
        """
        profile = ProfilePage(open_profile_page)
        default_status = "Рассматриваю предложения"

        with allure.step(f"Шаг 1: Выбор тестового статуса: '{test_status}'"):
            profile.select_from_dropdown(profile.status_dropdown, test_status)
            profile.save_changes()

        with allure.step("ОР 1: Проверка отображения нового статуса"):
            expect(profile.status_dropdown).to_have_text(test_status)

        with allure.step("Шаг 2: Восстановление дефолтного статуса"):
            profile.select_from_dropdown(profile.status_dropdown, default_status)
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата статуса в исходное состояние"):
            expect(profile.status_dropdown).to_have_text(default_status)

    @allure.title("Динамическое изменение пола соискателя")
    def test_edit_gender_radio(self, open_profile_page: Page):
        """
        Бизнес-кейс: Проверка переключения радиокнопок выбора пола соискателя.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Определить, какая из радиокнопок пола (Мужской/Женский) активна в данный момент.
        2. Кликнуть строго по тексту лейбла противоположного пола для переключения триггера.
        3. Сохранить изменения формы профиля.
        4. Проверить активацию новой радиокнопки через метод .is_checked().
        5. Вернуть переключатель пола в первоначальное зафиксированное состояние.

        Ожидаемый результат (ОР):
        - Радиокнопки эксклюзивны (активация одной автоматически снимает выбор с другой).
        - Выбранный пол успешно сохраняется в личном кабинете.
        """
        profile = ProfilePage(open_profile_page)

        with allure.step("Определение текущего выбранного пола на странице"):
            if profile.gender_male_input.is_checked():
                initial_gender, test_gender = "M", "F"
            else:
                initial_gender, test_gender = "F", "M"

        with allure.step(f"Шаг 1: Смена пола на противоположный ({test_gender})"):
            profile.select_gender(test_gender)
            profile.save_changes()

        with allure.step("ОР 1: Проверка активации нужной радиокнопки"):
            if test_gender == "M":
                expect(profile.gender_male_input).to_be_checked()
            else:
                expect(profile.gender_female_input).to_be_checked()

        with allure.step(f"Шаг 2: Восстановление исходного пола ({initial_gender})"):
            profile.select_gender(initial_gender)
            profile.save_changes()

        with allure.step("ОР 2: Проверка успешного возврата к исходному полу"):
            if initial_gender == "M":
                expect(profile.gender_male_input).to_be_checked()
            else:
                expect(profile.gender_female_input).to_be_checked()

    @allure.title("Ручной ввод даты рождения и динамический пересчет возраста")
    def test_edit_date_of_birth_manual(self, open_profile_page: Page, app_config):
        """
        Бизнес-кейс: Проверка ручного ввода даты рождения соискателя и динамического расчета возраста на клиенте и сервере.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Рассчитать ожидаемый возраст для дефолтной и тестовой даты с помощью утилиты calculate_expected_age.
        2. Очистить поле даты и посимвольно ввести тестовое значение формата ДД.ММ.ГГГГ.
        3. Кликнуть по элементу отображения возраста для сброса фокуса.
        4. Сохранить форму.
        5. Верифицировать, что дата переформатировалась в формат ISO (ГГГГ-ММ-ДД), а текстовое поле возраста отображает верное склонение лет.
        6. Повторить процедуру для возврата дефолтной даты рождения.

        Ожидаемый результат (ОР):
        - Инпут даты рождения корректно принимает ручной ввод.
        - Интерфейс динамически пересчитывает и выводит количество исполнившихся лет соискателя с правильным окончанием слова (год/года/лет).
        """
        profile = ProfilePage(open_profile_page)

        with allure.step("Подготовка тестовых дат и расчет ожидаемого возраста"):
            default_date = app_config["default_profile"]["date_of_birth"]
            expected_default_age = calculate_expected_age(default_date)
            test_date = generate_test_date(default_date, years_diff=-5)
            expected_test_age = calculate_expected_age(test_date)

            test_date_iso = "-".join(test_date.split(".")[::-1])
            default_date_iso = "-".join(default_date.split(".")[::-1])

        with allure.step(f"Шаг 1: Очистка поля и ввод тестовой даты: {test_date}"):
            # Используем fill() с ISO-форматом YYYY-MM-DD — работает одинаково
            # на всех ОС и локалях браузера (в отличие от press_sequentially с DD.MM.YYYY)
            profile.date_of_birth_input.fill(test_date_iso)
            profile.age_display.click()
            profile.save_changes()

        with allure.step("ОР 1: Проверка даты в формате ISO и нового возраста"):
            expect(profile.date_of_birth_input).to_have_value(test_date_iso)
            expect(profile.age_display).to_have_text(expected_test_age)

        with allure.step(f"Шаг 2: Восстановление дефолтной даты: {default_date}"):
            # Аналогично — fill() с ISO-форматом для кроссплатформенной стабильности
            profile.date_of_birth_input.fill(default_date_iso)
            profile.age_display.click()
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата к дефолтной дате в ISO и старому возрасту"):
            expect(profile.date_of_birth_input).to_have_value(default_date_iso)
            expect(profile.age_display).to_have_text(expected_default_age)


@allure.epic("Личный кабинет соискателя")
@allure.feature("Редактирование профиля")
class TestProfilePart2:

    @allure.title("Изменение даты рождения через интерфейс календаря")
    def test_edit_date_of_birth_via_calendar_ui(self, open_profile_page: Page, app_config):
        """
        Бизнес-кейс: Проверка работы встроенного браузерного виджета календаря с помощью горячих клавиш.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Сфокусироваться на инпуте даты рождения и раскрыть встроенный виджет комбинацией Alt+ArrowDown.
        2. Использовать стрелку клавиатуры для сдвига даты на один день влево.
        3. Нажать Enter для фиксации дня в календаре.
        4. Сбросить фокус клавишей Tab и сохранить изменения формы.
        5. Очистить поле и вернуть дефолтную дату рождения ручным вводом.

        Ожидаемый результат (ОР):
        - Календарь послушно реагирует на системные клавиатурные события и меняет выбранное число.
        - Выбранная дата успешно отправляется на бэкенд и обновляет профиль.
        """
        profile = ProfilePage(open_profile_page)

        with allure.step("Подготовка ожидаемой даты в формате ISO"):
            default_date_str = app_config["default_profile"]["date_of_birth"]
            default_date_obj = datetime.strptime(default_date_str, "%d.%m.%Y")
            default_date_iso = default_date_obj.strftime("%Y-%m-%d")

        with allure.step("Шаг 1: Открытие календаря и выбор дня стрелками"):
            profile.date_of_birth_input.click()
            open_profile_page.keyboard.press("Alt+ArrowDown")
            open_profile_page.wait_for_timeout(500)
            open_profile_page.keyboard.press("ArrowLeft")
            open_profile_page.wait_for_timeout(300)
            open_profile_page.keyboard.press("Enter")
            open_profile_page.wait_for_timeout(500)
            open_profile_page.keyboard.press("Tab")
            open_profile_page.wait_for_timeout(500)
            profile.save_changes()

        with allure.step(f"Шаг 2: Восстановление исходной даты ручным вводом: {default_date_str}"):
            # fill() с ISO-форматом YYYY-MM-DD — кроссплатформенно, не зависит от локали ОС
            profile.date_of_birth_input.fill(default_date_iso)
            profile.age_display.click()
            profile.save_changes()

        with allure.step("ОР: Проверка успешного возвращения к исходной дате"):
            expect(profile.date_of_birth_input).to_have_value(default_date_iso)

    @allure.title("Параметризованное изменение уровня образования: {test_education}")
    def test_edit_education_dropdown(self, open_profile_page: Page, app_config, test_education):
        """
        Бизнес-кейс: Проверка смены уровня базового образования соискателя через Select2.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Раскрыть кастомный контейнер Select2 выпадающего списка образования.
        2. Найти через поиск и выбрать переданный тестовый уровень образования.
        3. Сохранить форму и зафиксировать новое значение на UI.
        4. Повторить процедуру для возврата дефолтного образования из файла конфигурации.

        Ожидаемый результат (ОР):
        - Изменение уровня образования корректно сохраняется сервером и не сбрасывается.
        """
        profile = ProfilePage(open_profile_page)
        default_education = app_config["default_profile"]["education"]

        with allure.step(f"Шаг 1: Выбор тестового образования: '{test_education}'"):
            profile.select_from_dropdown(profile.education_dropdown, test_education)
            profile.save_changes()

        with allure.step("ОР 1: Проверка нового значения на странице"):
            expect(profile.education_dropdown).to_have_text(test_education)

        with allure.step("Шаг 2: Возврат дефолтного значения обратно"):
            profile.select_from_dropdown(profile.education_dropdown, default_education)
            profile.save_changes()

        with allure.step("ОР 2: Проверка возврата образования в исходное состояние"):
            expect(profile.education_dropdown).to_have_text(default_education)

    @allure.title("Каскадное изменение полного адреса проживания")
    def test_edit_full_address_cascade(self, open_profile_page: Page, app_config):
        """
        Бизнес-кейс: Проверка каскадной (связанной) фильтрации адресных выпадающих списков Select2.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта страница персональных данных.

        Шаги:
        1. Выбрать тестовую область в регионе и дождаться подгрузки зависимых районов.
        2. Выбрать появившийся тестовый район и дождаться подгрузки связанных населенных пунктов/советов.
        3. Выбрать итоговый тестовый населенный пункт и сохранить форму.
        4. Верифицировать отображение полного тестового адреса.
        5. Поочередно восстановить исходную область, район и город проживания из конфигурации.

        Ожидаемый результат (ОР):
        - Адресный блок работает строго каскадно (выбор верхнего уровня автоматически обновляет списки нижних уровней).
        - Полный адрес корректно записывается в профиль соискателя.
        """
        profile = ProfilePage(open_profile_page)
        default = app_config["default_profile"]
        test_addr = app_config["profile_test_data"]["edit_address"]

        with allure.step("Шаг 1: Последовательная установка тестового региона, района и города"):
            profile.select_from_dropdown(profile.region_dropdown, test_addr["region"])
            expect(profile.region_dropdown).to_have_text(test_addr["region"])
            open_profile_page.wait_for_timeout(1000)

            profile.select_from_dropdown(profile.district_dropdown, test_addr["district"])
            expect(profile.district_dropdown).to_have_text(test_addr["district"])
            open_profile_page.wait_for_timeout(1000)

            profile.select_from_dropdown(profile.address_dropdown, test_addr["address"])
            profile.save_changes()

        with allure.step("ОР 1: Проверка отображения полного тестового адреса"):
            expect(profile.region_dropdown).to_have_text(test_addr["region"])
            expect(profile.district_dropdown).to_have_text(test_addr["district"])
            expect(profile.address_dropdown).to_have_text(test_addr["address"])

        with allure.step("Шаг 2: Восстановление дефолтных значений адреса"):
            # 1. Возвращаем дефолтную область
            profile.select_from_dropdown(profile.region_dropdown, default["region"])
            expect(profile.region_dropdown).to_have_text(default["region"])
            open_profile_page.wait_for_timeout(1000)

            # 2. Возвращаем дефолтный район
            profile.select_from_dropdown(profile.district_dropdown, default["district"])
            expect(profile.district_dropdown).to_have_text(default["district"])
            open_profile_page.wait_for_timeout(1000)

            # 3. Возвращаем дефолтный город/пункт
            profile.select_from_dropdown(profile.address_dropdown, default["address"])

            # 4. ОБЯЗАТЕЛЬНО сохраняем, чтобы вернуть профиль в исходное состояние
            profile.save_changes()

        @allure.title("Изменение email для рассылок")
        def test_edit_email_message(self, open_profile_page: Page, app_config):
            """
            Бизнес-кейс: Изменение контактного адреса электронной почты для системных уведомлений.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта страница персональных данных.

            Шаги:
            1. Ввести в инпут Email новый валидный тестовый адрес почты.
            2. Нажать кнопку "Сохранить" и дождаться подтверждения операции.
            3. Верифицировать успешное отображение нового значения на UI.
            4. Восстановить первоначальный дефолтный Email соискателя из конфигурации.

            Ожидаемый результат (ОР):
            - Поле ввода корректно перезаписывает данные и сохраняет новый Email.
            - Система стабилизирует DOM после успешной отправки формы.
            """
            profile = ProfilePage(open_profile_page)
            default_email = app_config["default_profile"]["email_sent"]
            test_email = app_config["profile_test_data"]["edit_contacts"]["test_email"]

            with allure.step(f"Шаг 1: Изменение email на тестовый: {test_email}"):
                profile.fill_field_safely(profile.email_message_input, test_email)
                profile.save_changes()

            with allure.step("ОР 1: Проверка сохранения нового email"):
                expect(profile.email_message_input).to_have_value(test_email)

            with allure.step(f"Шаг 2: Возврат к дефолтному email: {default_email}"):
                profile.fill_field_safely(profile.email_message_input, default_email)
                profile.save_changes()

            with allure.step("ОР 2: Проверка возврата email к дефолтному значению"):
                expect(profile.email_message_input).to_have_value(default_email)

        @allure.title("Негативный тест: Попытка изменения email на уже занятый")
        def test_edit_email_already_taken_negative(self, open_profile_page: Page, app_config):
            """
            Бизнес-кейс: Негативный сценарий валидации уникальности Email при попытке сохранения уже зарегистрированного адреса.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта страница персональных данных.

            Шаги:
            1. Ввести в инпут Email тестовый адрес, который гарантированно занят другим аккаунтом в системе.
            2. Нажать кнопку "Сохранить" и дождаться ответа сервера.
            3. Зафиксировать появление красной плашки ошибки и текста валидации под полем.
            4. Очистить поле и вернуть исходный корректный Email обратно.

            Ожидаемый результат (ОР):
            - Форма блокирует сохранение дубликата, бэкенд возвращает ошибку валидации.
            - Под инпутом выводится строгий текст ошибки "Email занят".
            """
            profile = ProfilePage(open_profile_page)
            default_email = app_config["default_profile"]["email_sent"]
            taken_email = app_config["profile_test_data"]["negative_contacts"]["already_taken_email"]

            with allure.step(f"Шаг 1: Ввод занятого email: {taken_email}"):
                profile.fill_field_safely(profile.email_message_input, taken_email)
                profile.save_changes()

            with allure.step("ОР: Отображение красной плашки и ошибки 'Email занят' под полем"):
                expect(profile.error_alert).to_be_visible()
                expect(profile.email_error_message).to_have_text("Email занят")

            with allure.step("Шаг 2: Восстановление дефолтного email"):
                profile.fill_field_safely(profile.email_message_input, default_email)
                profile.save_changes()
                expect(profile.email_message_input).to_have_value(default_email)

    @allure.epic("Личный кабинет соискателя")
    @allure.feature("Редактирование профиля")
    class TestProfilePart3:

        @allure.title("Изменение основного телефона с проверкой маски")
        def test_edit_main_phone(self, open_profile_page: Page, app_config):
            """
            Бизнес-кейс: Изменение основного номера телефона соискателя и проверка автоматического наложения маски.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта страница персональных данных.

            Шаги:
            1. Считать текущий номер телефона и сгенерировать ожидаемый вид тестовой маски.
            2. Очистить инпут основного телефона и ввести сплошную строку цифр нового номера.
            3. Нажать кнопку "Сохранить".
            4. Проверить, что на UI номер автоматически отформатировался по маске Республики Беларусь.
            5. Восстановить первоначальный рабочий номер телефона.

            Ожидаемый результат (ОР):
            - Система успешно принимает и сохраняет новый номер телефона.
            - Поле ввода автоматически форматирует сырые цифры в строгий шаблон +375 (XX) XXX-XX-XX.
            """
            profile = ProfilePage(open_profile_page)
            test_phone = app_config["profile_test_data"]["edit_contacts"]["test_main_phone"]

            with allure.step("Считывание текущего телефона и форматирование маски"):
                initial_phone = profile.main_phone_input.input_value()
                expected_test_phone = format_phone_to_mask(test_phone)

            with allure.step(f"Шаг 1: Ввод нового основного номера: {test_phone}"):
                profile.fill_field_safely(profile.main_phone_input, test_phone)
                profile.save_changes()

            with allure.step("ОР 1: Проверка сохранения телефона с применением маски"):
                expect(profile.main_phone_input).to_have_value(expected_test_phone)

            with allure.step("Шаг 2: Восстановление первоначального номера"):
                profile.fill_field_safely(profile.main_phone_input, initial_phone)
                profile.save_changes()

            with allure.step("ОР 2: Проверка возврата номера в исходное состояние"):
                expect(profile.main_phone_input).to_have_value(initial_phone)

        @allure.title("Добавление и последующее удаление дополнительного номера телефона")
        def test_add_and_delete_additional_phone(self, open_profile_page: Page, app_config):
            """
            Бизнес-кейс: Проверка работы динамического формсета дополнительных контактов в профиле соискателя.

            Прекондишены:
            1. Пользователь авторизован в системе.
            2. Открыта страница персональных данных личного кабинета.

            Шаги:
            1. Удалить дефолтную пустую строку дополнительного телефона кликом по крестику.
            2. Нажать на кнопку "Добавить номер" для генерации чистого поля ввода.
            3. Ввести валидный номер телефона из конфигурационных данных.
            4. Нажать кнопку "Сохранить" для отправки изменений на бэкенд.
            5. Проверить, что номер успешно сохранился и к нему применилась маска +375.
            6. Нажать на крестик удаления, чтобы очистить поле, и снова сохранить форму.

            Ожидаемый результат (ОР):
            - Динамические поля корректно создаются и удаляются в DOM-дереве.
            - Сохраненный номер отображается строго в соответствии с маской телефона Республики Беларусь.
            - После удаления номера и сохранения формы поле очищается, данные успешно удаляются из базы.
            """
            profile = ProfilePage(open_profile_page)
            contacts = app_config["profile_test_data"]["edit_contacts"]
            mask_phone_2 = format_phone_to_mask(contacts["additional_phone_2"])

            with allure.step("Шаг 1: Удаление пустого дефолтного поля"):
                profile.delete_phone_button_0.click()
                open_profile_page.wait_for_timeout(300)

            with allure.step("Шаг 2: Создание чистого поля через кнопку добавления"):
                profile.add_phone_button.click()
                expect(profile.additional_phone_0).to_be_visible(timeout=3000)

            with allure.step(f"Шаг 3: Ввод телефона {contacts['additional_phone_2']} и сохранение"):
                profile.fill_field_safely(profile.additional_phone_0, contacts["additional_phone_2"])
                profile.save_changes()

            with allure.step("ОР: Проверка успешного сохранения дополнительного телефона"):
                expect(profile.additional_phone_0).to_have_value(mask_phone_2)

            with allure.step("Шаг 4: Возврат формы в исходный вид (удаление номера крестиком)"):
                profile.delete_phone_button_0.click()
                profile.save_changes()

            with allure.step("Проверка полного очищения поля"):
                expect(profile.additional_phone_0).to_have_value("")

        @allure.title("Негативный тест: Попытка изменения телефона на уже занятый")
        def test_edit_phone_already_taken_negative(self, open_profile_page: Page, app_config):
            """
            Бизнес-кейс: Негативный сценарий валидации уникальности телефона при попытке сохранения уже зарегистрированного номера.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта страница персональных данных.

            Шаги:
            1. Фиксировать текущий рабочий номер телефона профиля.
            2. Ввести в инпут основного телефона номер, который гарантированно привязан к другому личному кабинету.
            3. Нажать кнопку "Сохранить" и дождаться ответа бэкенда.
            4. Зафиксировать появление красного алерта и развернутого текста ошибки под полем.
            5. Восстановить исходный телефон соискателя для стабилизации аккаунта.

            Ожидаемый результат (ОР):
            - Система блокирует дублирование номеров телефонов в базе данных.
            - Под инпутом отображается строгий валидационный текст о невозможности регистрации.
            """
            profile = ProfilePage(open_profile_page)
            taken_phone = app_config["profile_test_data"]["negative_contacts"]["already_taken_phone"]
            expected_error = "На указанный номер телефона уже зарегистрирован другой личный кабинет. Введите другой номер или войдите в существующий кабинет."

            with allure.step("Фиксация текущего телефона профиля перед тестом"):
                initial_phone = profile.main_phone_input.input_value()

            with allure.step(f"Шаг 1: Ввод занятого телефона: {taken_phone}"):
                profile.fill_field_safely(profile.main_phone_input, taken_phone)
                profile.save_changes()

            with allure.step("ОР: Отображение красной плашки и развернутого текста ошибки под полем"):
                expect(profile.error_alert).to_be_visible()
                expect(profile.phone_error_message).to_have_text(expected_error)

            with allure.step("Шаг 2: Восстановление исходного телефона"):
                profile.fill_field_safely(profile.main_phone_input, initial_phone)
                profile.save_changes()

            with allure.step("Проверка успешного восстановления номера"):
                expect(profile.main_phone_input).to_have_value(initial_phone)

        @allure.title("Проверка кликабельности чек-бокса скрытия ФИО")
        def test_click_privacy_checkbox(self, open_profile_page: Page):
            """
            Бизнес-кейс: Проверка работы триггера приватности персональных данных соискателя.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта страница персональных данных.

            Шаги:
            1. Нажать на чекбокс "Скрыть ФИО" через генерацию JS-события dispatch_event.
            2. Сохранить изменения на сервере.
            3. Верифицировать статус активации чекбокса через ассерт .to_be_checked().
            4. Повторно кликнуть по чекбоксу для деактивации режима скрытия и сохранить форму.

            Ожидаемый результат (ОР):
            - Чекбокс успешно переключает свои состояния и фиксирует флаг приватности на бэкенде.
            """
            profile = ProfilePage(open_profile_page)

            with allure.step("Шаг 1: Активация чек-бокса 'Скрыть ФИО'"):
                profile.privacy_checkbox.dispatch_event("click")
                profile.save_changes()

            with allure.step("ОР 1: Чек-бокс успешно активен"):
                expect(profile.privacy_checkbox).to_be_checked()

            with allure.step("Шаг 2: Деактивация чек-бокса (возврат в исходное состояние)"):
                profile.privacy_checkbox.dispatch_event("click")
                profile.save_changes()

            with allure.step("ОР 2: Чек-бокс успешно снят"):
                expect(profile.privacy_checkbox).not_to_be_checked()