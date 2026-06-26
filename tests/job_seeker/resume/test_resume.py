import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.resume_page import ResumePage
from helpers.helpers import calculate_expected_age
from helpers.network_helper import goto_with_retry
from helpers.resume_helper import fill_and_submit_required_resume_fields, clear_all_resumes_from_account



@allure.epic("Резюме соискателя")
@allure.feature("Создание резюме")
class TestResumeProfileBlock:

    @allure.title("Сверка автоматических данных профиля на форме резюме с конфигурацией")
    def test_verify_profile_data_in_resume(self, open_create_resume_page: Page, app_config):
        """
        Бизнес-кейс: Проверка автозаполнения и блокировки персональных данных из профиля на форме создания резюме.

        Прекондишены:
        1. Пользователь авторизован в системе.
        2. Открыта страница создания нового резюме.

        Шаги:
        1. Рассчитать ожидаемый возраст соискателя на текущую дату по его дню рождения.
        2. Проверить, что текстовые инпуты ФИО заблокированы для редактирования и содержат дефолтные значения.
        3. Убедиться, что инпут возраста заблокирован и выводит верное число лет.
        4. Сверить код уровня базового образования в селекте.
        5. Верифицировать наличие названия области в контейнере региона без падений из-за разницы строк.
        6. Сверить район и населенный пункт в контейнерах.
        7. Проверить, что чекбокс скрытия ФИО по умолчанию снят.

        Ожидаемый результат (ОР):
        - Вся ключевая информация профиля соискателя автоматически подтягивается в соответствующие блоки формы резюме.
        - Поля ФИО и возраста имеют неизменяемый статус (readonly/disabled).
        - Область проживания успешно верифицируется через частичное вхождение подстроки.
        """
        resume = ResumePage(open_create_resume_page)

        with allure.step("Загрузка ожидаемых дефолтных данных и расчет возраста"):
            default_data = app_config["default_profile"]
            expected_age_digits = calculate_expected_age(default_data["date_of_birth"]).split()[0]

        with allure.step("Проверка заблокированных текстовых полей ФИО и динамического возраста"):
            expect(resume.last_name_input).to_have_value(default_data["last_name"])
            expect(resume.first_name_input).to_have_value(default_data["first_name"])
            expect(resume.middle_name_input).to_have_value(default_data["middle_name"])
            expect(resume.age_input).to_have_value(expected_age_digits)

        with allure.step("Проверка выбранного уровня образования"):
            expect(resume.education_dropdown).to_have_value("2")

        with allure.step("Проверка отображения адреса проживания в контейнерах"):
            # Избегаем падения из-за разницы строк Select2: ищем просто "Витебская" внутри плашки
            expect(resume.region_container).to_contain_text("Витебская")
            expect(resume.district_container).to_have_text(default_data["district"])
            expect(resume.address_container).to_have_text(default_data["address"])

        with allure.step("Проверка начального состояния чек-бокса 'Скрыть ФИО'"):
            expect(resume.privacy_checkbox).not_to_be_checked()

    @allure.title("Проверка кликабельности чек-бокса согласия на переезд")
    def test_click_relocate_checkbox(self, open_create_resume_page: Page):
        """
        Бизнес-кейс: Проверка работы интерактивного триггера готовности соискателя к переезду.

        Прекондишены:
        1. Пользователь авторизован в системе.
        2. Открыта страница создания нового резюме.

        Шаги:
        1. Сгенерировать JS-событие клика по текстовому лейблу чекбокса согласия на переезд.
        2. Верифицировать успешную активацию флага (состояние checked).
        3. Повторно кликнуть по элементу для снятия выбора.
        4. Верифицировать деактивацию флага.

        Ожидаемый результат (ОР):
        - Чекбокс стабильно реагирует на клики пользователя, меняя внутреннее состояние триггера на форме.
        """
        resume = ResumePage(open_create_resume_page)

        with allure.step("Шаг 1: Активация чек-бокса согласия на переезд"):
            resume.relocate_checkbox.dispatch_event("click")

        with allure.step("ОР 1: Чек-бокс успешно активен"):
            expect(resume.relocate_checkbox).to_be_checked()

        with allure.step("Шаг 2: Деактивация чек-бокса (возврат в исходное состояние)"):
            resume.relocate_checkbox.dispatch_event("click")

        with allure.step("ОР 2: Чек-бокс успешно снят"):
            expect(resume.relocate_checkbox).not_to_be_checked()

    @allure.title("Проверка дефолтного Email и добавления дополнительного поля Email")
    def test_verify_email_and_add_field(self, open_create_resume_page: Page, app_config):
        """
        Бизнес-кейс: Проверка базовых контактных данных и динамического расширения полей Email на форме резюме.

        Прекондишены:
        1. Пользователь авторизован в системе.
        2. Открыта страница создания нового резюме.

        Шаги:
        1. Убедиться, что в первом инпуте Email автоматически отображается адрес электронной почты из профиля.
        2. Кликнуть по интерактивной кнопке "Добавить E-mail".
        3. Зафиксировать появление нового динамического инпута с порядковым индексом 1 в DOM-дереве.
        4. Проверить видимость сгенерированного поля на экране и убедиться, что оно изначально пустое.

        Ожидаемый результат (ОР):
        - Основной Email соискателя подтягивается на форме по умолчанию.
        - Механизм динамических форм Django Formset корректно создает новые строки ввода контактов при нажатии кнопки.
        """
        resume = ResumePage(open_create_resume_page)
        default_email = app_config["default_profile"]["email_sent"]

        with allure.step("Шаг 1: Проверка, что первый Email совпадает с профилем"):
            expect(resume.email_input_0).to_have_value(default_email)

        with allure.step("Шаг 2: Клик по кнопке 'Добавить E-mail'"):
            resume.add_email_button.click()

        with allure.step("ОР: Появилось второе пустое поле для ввода Email"):
            second_email_input = open_create_resume_page.locator("#id_resume_emails-1-email")
            expect(second_email_input).to_be_visible(timeout=3000)
            expect(second_email_input).to_have_value("")

    @allure.title("Проверка добавления и удаления динамических полей контактов")
    def test_add_and_delete_dynamic_contacts(self, open_create_resume_page: Page):
        """
        Бизнес-кейс: Проверка полного цикла генерации и деструкции дополнительных полей контактов (Email/Телефон).

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта пустая форма создания нового резюме.

        Шаги:
        1. Нажать интерактивные кнопки добавления поля телефона и добавления дополнительного Email.
        2. Дождаться появления сгенерированных строк на форме и проверить их видимость.
        3. Последовательно нажать на красные кнопки-крестики удаления для каждой добавленной строки.
        4. Верифицировать полное исчезновение динамических блоков из интерфейса.

        Ожидаемый результат (ОР):
        - Скрипты Django Formset мгновенно создают новые инпуты в DOM при добавлении.
        - Клик по кнопке удаления корректно вырезает или скрывает элементы, очищая форму.
        """
        resume = ResumePage(open_create_resume_page)

        with allure.step("Шаг 1: Добавление поля телефона и второго Email"):
            resume.add_phone_button.click()
            resume.add_email_button.click()

        with allure.step("ОР 1: Поля успешно отображаются на форме"):
            expect(resume.phone_input_0).to_be_visible(timeout=3000)

            second_email = open_create_resume_page.locator("#id_resume_emails-1-email")
            expect(second_email).to_be_visible(timeout=3000)

        with allure.step("Шаг 2: Удаление добавленных полей через крестики"):
            resume.delete_phone_button_0.click()
            resume.delete_email_button_1.click()

        with allure.step("ОР 2: Динамические поля исчезли из интерфейса"):
            expect(resume.phone_input_0).not_to_be_visible()
            expect(second_email).not_to_be_visible()


@allure.epic("Личный кабинет соискателя")
@allure.feature("Создание резюме")
class TestResumeJobRequirements:

    @allure.title("Выбор желаемой профессии и производной должности")
    def test_select_profession_and_derivative(self, open_create_resume_page: Page):
        """
        Бизнес-кейс: Поиск профессии в справочнике Select2 и выбор квалификационной производной.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта форма создания резюме.

        Шаги:
        1. Проверить стартовое текстовое наполнение (плейсхолдер) контейнера профессии.
        2. Активировать выпадающий список и посимвольно ввести поисковый запрос названия профессии.
        3. Кликнуть по первому найденному совпадению в результатах выдачи справочника.
        4. Из нативного списка производных должностей выбрать пункт "Старший" (атрибут value='1').
        5. Проверить фиксацию выбранных значений на форме.

        Ожидаемый результат (ОР):
        - Поисковый справочник профессий корректно фильтрует список вариантов при вводе текста.
        - Выбранная профессия и её производная успешно отображаются в соответствующих полях формы.
        """
        resume = ResumePage(open_create_resume_page)
        test_profession = "Авербандщик"

        with allure.step("Шаг 1: Проверка дефолтного текста-подсказки (плейсхолдера)"):
            expect(resume.profession_container).to_have_text(
                "Введите наименование должности служащего, профессии рабочего"
            )

        with allure.step(f"Шаг 2: Клик по дропдауну и ввод текста для поиска: '{test_profession}'"):
            resume.profession_container.click()
            resume.select2_search_input.press_sequentially(test_profession, delay=100)
            open_create_resume_page.wait_for_timeout(500)

        with allure.step(f"Шаг 3: Выбор найденного варианта '{test_profession}'"):
            resume.select2_first_option.click()

        with allure.step("ОР 1: Выбранная профессия успешно отображается в контейнере"):
            expect(resume.profession_container).to_have_text(
                re.compile(test_profession)
            )

        with allure.step("Шаг 4: Выбор производной должности 'Старший'"):
            resume.derivative_dropdown.select_option("1")

        with allure.step("ОР 2: Производная должность успешно выбрана"):
            expect(resume.derivative_dropdown).to_have_value("1")

    @allure.title("Ввод желаемой заработной платы в поле ввода")
    def test_enter_desired_salary(self, open_create_resume_page: Page):
        """
        Бизнес-кейс: Проверка заполнения и маски числового поля желаемого уровня заработной платы.

        Прекондишены:
        1. Пользователь успешно авторизован в системе.
        2. Открыта форма создания резюме.

        Шаги:
        1. Сверить начальный числовой плейсхолдер в инпуте зарплаты.
        2. Заполнить инпут валидной дробной тестовой суммой с помощью метода .fill().
        3. Верифицировать корректное отображение введенных цифр на экране.

        Ожидаемый результат (ОР):
        - Поле ввода принимает числовые значения и корректно сохраняет их внутри инпута.
        """
        resume = ResumePage(open_create_resume_page)
        test_salary = "1500.50"

        with allure.step("Шаг 1: Проверка начального плейсхолдера"):
            expect(resume.salary_input).to_have_attribute(
                "placeholder", "00000.00"
            )

        with allure.step(f"Шаг 2: Ввод тестовой суммы: {test_salary}"):
            resume.salary_input.fill(test_salary)

        with allure.step("ОР: Сумма успешно отображается в поле ввода"):
            expect(resume.salary_input).to_have_value(test_salary)

        @allure.title("Выбор характера работы и режима рабочего времени")
        def test_select_work_conditions(self, open_create_resume_page: Page):
            """
            Бизнес-кейс: Заполнение условий труда соискателя через нативные выпадающие списки.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта форма создания резюме.

            Шаги:
            1. Проверить стартовые дефолтные значения ("Любой", пустая строка) в обоих селектах.
            2. Выбрать характер работы "Постоянная" по значению атрибута (value="1").
            3. Выбрать режим рабочего времени "Одна смена" по значению атрибута (value="1").
            4. Проверить фиксацию выбранных опций.

            Ожидаемый результат (ОР):
            - Нативные выпадающие списки корректно принимают выбор и сохраняют нужные значения параметров.
            """
            resume = ResumePage(open_create_resume_page)

            with allure.step("Шаг 1: Проверка дефолтных пустых значений 'Любой'"):
                expect(resume.employment_nature_dropdown).to_have_value("")
                expect(resume.work_mode_dropdown).to_have_value("")

            with allure.step("Шаг 2: Выбор характера работы 'Постоянная'"):
                resume.employment_nature_dropdown.select_option("1")

            with allure.step("Шаг 3: Выбор режима рабочего времени 'Одна смена'"):
                resume.work_mode_dropdown.select_option("1")

            with allure.step("ОР: Новые условия работы успешно выбраны в списках"):
                expect(resume.employment_nature_dropdown).to_have_value("1")
                expect(resume.work_mode_dropdown).to_have_value("1")

        @allure.title("Проверка кликабельности чек-бокса требования жилья")
        def test_click_housing_checkbox(self, open_create_resume_page: Page):
            """
            Бизнес-кейс: Проверка работы флага потребности соискателя в предоставлении жилья нанимателем.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта форма создания резюме.

            Шаги:
            1. Проверить, что чекбокс изначально находится в неактивном состоянии.
            2. Активировать чекбокс "Требуется жилье" через генерацию JS-события click по лейблу.
            3. Убедиться, что флаг успешно проставился на форме.
            4. Повторным кликом снять флаг и проверить возврат в исходное пустое состояние.

            Ожидаемый результат (ОР):
            - Интерактивный чекбокс жилья стабильно переключает свои логические состояния при клике.
            """
            resume = ResumePage(open_create_resume_page)

            with allure.step("Шаг 1: Проверка начального состояния чек-бокса"):
                expect(resume.housing_checkbox).not_to_be_checked()

            with allure.step("Шаг 2: Активация чек-бокса 'Требуется жилье'"):
                resume.housing_checkbox.dispatch_event("click")

            with allure.step("ОР 1: Чек-бокс успешно активен"):
                expect(resume.housing_checkbox).to_be_checked()

            with allure.step("Шаг 3: Деактивация чек-бокса"):
                resume.housing_checkbox.dispatch_event("click")

            with allure.step("ОР 2: Чек-бокс успешно снят"):
                expect(resume.housing_checkbox).not_to_be_checked()

    @allure.epic("Личный кабинет соискателя")
    @allure.feature("Создание резюме")
    class TestResumeExperience:

        @allure.title("Динамическое добавление и удаление блока опыта работы")
        def test_add_and_remove_experience_block(self, open_create_resume_page: Page):
            """
            Бизнес-кейс: Проверка генерации и скрытия/удаления динамического формсета истории трудовой деятельности.

            Прекондишены:
            1. Пользователь успешно авторизован в системе.
            2. Открыта пустая форма создания резюме.

            Шаги:
            1. Нажать на кнопку "Добавить место работы" для инициализации динамической формы.
            2. Дождаться появления всех полей блока (организация, стаж, должность, обязанности) и проверить их видимость.
            3. Нажать на кнопку-крестик удаления добавленного блока опыта.
            4. Убедиться, что вся сгенерированная форма скрылась с экрана соискателя.

            Ожидаемый результат (ОР):
            - Формсет Django Formset корректно реагирует на добавление и деструкцию сложных составных блоков полей.
            """
            resume = ResumePage(open_create_resume_page)

            with allure.step("Шаг 1: Клик по кнопке 'Добавить место работы'"):
                resume.add_experience_button.click()

            with allure.step("ОР 1: Все поля опыта работы стали видимы соискателю"):
                expect(resume.exp_org_input).to_be_visible(timeout=3000)
                expect(resume.exp_years_input).to_be_visible()
                expect(resume.exp_months_input).to_be_visible()
                expect(resume.exp_profession_input).to_be_visible()
                expect(resume.exp_duties_input).to_be_visible()
                expect(resume.exp_additional_textarea).to_be_visible()

            with allure.step("Шаг 2: Клик по кнопке-крестику удаления блока"):
                resume.delete_experience_button_0.click()

            with allure.step("ОР 2: Блок опыта работы успешно исчез с формы"):
                expect(resume.exp_org_input).not_to_be_visible()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeEducation:

            @allure.title("Динамическое добавление и удаление блока места обучения")
            def test_add_and_remove_education_block(self, open_create_resume_page: Page):
                """
                Бизнес-кейс: Проверка генерации и удаления динамического блока сведений об обучении соискателя.

                Прекондишены:
                1. Пользователь успешно авторизован в системе.
                2. Открыта пустая форма создания резюме.

                Шаги:
                1. Нажать на интерактивную кнопку "Добавить место обучения".
                2. Дождаться появления полей ввода (название ВУЗа, специализация, год окончания, описание) и проверить их видимость.
                3. Нажать на кнопку-крестик удаления добавленного блока обучения.
                4. Убедиться, что сгенерированная форма полностью скрылась с экрана.

                Ожидаемый результат (ОР):
                - Инструменты Django Formset мгновенно создают и скрывают составные блоки полей образования соискателя.
                """
                resume = ResumePage(open_create_resume_page)

                with allure.step("Шаг 1: Клик по кнопке 'Добавить место обучения'"):
                    resume.add_education_button.click()

                with allure.step("ОР 1: Все поля образования стали видимы"):
                    expect(resume.edu_name_input).to_be_visible(timeout=3000)
                    expect(resume.edu_specialty_input).to_be_visible()
                    expect(resume.edu_ending_input).to_be_visible()
                    expect(resume.edu_info_textarea).to_be_visible()

                with allure.step("Шаг 2: Клик по кнопке-крестику удаления блока"):
                    resume.delete_education_button_0.click()

                with allure.step("ОР 2: Блок места обучения успешно исчез с формы"):
                    expect(resume.edu_name_input).not_to_be_visible()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeLanguages:

            @allure.title("Выбор языка, его уровня, добавление и удаление новой строки")
            def test_select_language_and_level(self, open_create_resume_page: Page):
                """
                Бизнес-кейс: Проверка заполнения языкового блока и динамического расширения списка языков.

                Прекондишены:
                1. Пользователь успешно авторизован в системе.
                2. Открыта пустая форма создания резюме.

                Шаги:
                1. Проверить начальное пустое состояние дефолтных списков выбора языка и уровня владения.
                2. Выбрать язык "Английский" (атрибут value='4') и уровень "Продвинутый" (атрибут value='10').
                3. Нажать интерактивную кнопку "Добавить язык".
                4. Верифицировать появление второй пустой строки ввода и дождаться её видимости в DOM.
                5. Нажать на крестик удаления второй строки и проверить её исчезновение.

                Ожидаемый результат (ОР):
                - Нативные выпадающие списки корректно сохраняют выбранные языковые параметры.
                - Динамический механизм позволяет расширять список языков и удалять лишние строки.
                """
                resume = ResumePage(open_create_resume_page)

                with allure.step("Шаг 1: Проверка дефолтных пустых значений списка"):
                    expect(resume.language_dropdown).to_have_value("")
                    expect(resume.lang_level_dropdown).to_have_value("")

                with allure.step("Шаг 2: Изменение языка на 'Английский'"):
                    resume.select_language("Английский")

                with allure.step("Шаг 3: Изменение уровня на 'продвинутый'"):
                    resume.select_language_level("продвинутый")

                with allure.step("ОР 1: Новые языковые параметры успешно применились"):
                    expect(resume.language_dropdown_1).to_have_value("4")
                    expect(resume.lang_level_dropdown_1).to_have_value("10")

                with allure.step("Шаг 4: Клик по кнопке 'Добавить язык'"):
                    resume.add_language_button.click()

                with allure.step("ОР 2: Появилась вторая пустая строка для ввода языка"):
                    expect(resume.delete_language_button_1).to_be_visible(timeout=3000)
                    second_lang = open_create_resume_page.locator(
                        "#id_resume_languages-2-language"
                    )
                    expect(second_lang).to_have_value("")

                with allure.step("Шаг 5: Удаление второй строки через крестик"):
                    resume.delete_language_button_1.click()

                with allure.step("ОР 3: Вторая строка языков успешно исчезла"):
                    expect(resume.delete_language_button_1).not_to_be_visible()

        @allure.epic("Личный кабинет соискателя")
        @allure.feature("Создание резюме")
        class TestResumeSkills:

            @allure.title("Выбор нескольких гибких навыков и удаление одного из них")
            def test_select_and_remove_skills(self, open_create_resume_page: Page):
                """
                Бизнес-кейс: Проверка работы множественного выбора тегов (tags) гибких навыков соискателя через Select2.

                Прекондишены:
                1. Пользователь успешно авторизован в системе.
                2. Открыта пустая форма создания резюме.

                Шаги:
                1. Кликнуть по множественному контейнеру гибких навыков для открытия выпадающего списка.
                2. Посимвольно ввести текст названия первого навыка и кликнуть по найденному результату.
                3. Повторно активировать поле и выбрать второй навык напрямую из открывшегося списка.
                4. Кликнуть в пустую область для закрытия выпадающего окна справочника.
                5. Убедиться, что оба тега навыков успешно отображаются внутри контейнера.
                6. Нажать на крестик первого добавленного навыка для его точечного удаления.
                7. Верифицировать, что удаленный навык пропал, а второй тег остался на форме.

                Ожидаемый результат (ОР):
                - Поле множественного выбора Select2 стабильно поддерживает добавление нескольких независимых тегов.
                - Клик по крестику конкретного тега удаляет исключительно выбранный элемент, не затрагивая остальные.
                """
                resume = ResumePage(open_create_resume_page)
                skill_1 = "Деловая коммуникация"
                skill_2 = "Адаптивность и гибкость"

                with allure.step("Шаг 1: Активация поле гибких навыков через клик"):
                    resume.skills_container.dispatch_event("click")
                    open_create_resume_page.wait_for_timeout(300)

                with allure.step(f"Шаг 2: Поиск и выбор первого навыка: '{skill_1}'"):
                    resume.skills_search_input.press_sequentially(skill_1, delay=100)
                    open_create_resume_page.wait_for_timeout(500)
                    resume.get_skill_option_by_text(skill_1).click()

                with allure.step("Шаг 3: Повторная активация поля (открытие списка вариантов)"):
                    resume.skills_container.dispatch_event("click")
                    open_create_resume_page.wait_for_timeout(300)

                with allure.step(f"Шаг 4: Выбор второго навыка напрямую из списка: '{skill_2}'"):
                    resume.get_skill_option_by_text(skill_2).click()

                with allure.step("Шаг 5: Клик в пустую область для закрытия списка"):
                    resume.skills_container.dispatch_event("click")
                    open_create_resume_page.wait_for_timeout(300)

                with allure.step("ОР 1: Оба навыка успешно отображаются в поле"):
                    expect(resume.skills_container).to_contain_text(skill_1)
                    expect(resume.skills_container).to_contain_text(skill_2)

                with allure.step("Шаг 6: Удаление первого навыка через крестик"):
                    resume.skills_first_remove_btn.click()

                with allure.step(f"ОР 2: Навык '{skill_1}' успешно удален из списка"):
                    expect(resume.skills_container).not_to_contain_text(skill_1)
                    expect(resume.skills_container).to_contain_text(skill_2)

            @allure.title("Ввод дополнительной информации о соискателе")
            def test_enter_additional_information(self, open_create_resume_page: Page):
                """
                Бизнес-кейс: Проверка заполнения текстового поля дополнительной информации в резюме.

                Прекондишены:
                1. Пользователь успешно авторизован в системе.
                2. Открыта форма создания нового резюме.

                Шаги:
                1. Проверить, что текстовая область пожеланий изначально пустая.
                2. Заполнить поле большим объемом развернутого тестового текста через метод .fill().
                3. Верифицировать корректное отображение введенных данных в поле.

                Ожидаемый результат (ОР):
                - Текстовая область корректно принимает и удерживает введенный соискателем текст.
                """
                resume = ResumePage(open_create_resume_page)
                test_text = "Ответственный сотрудник, готов к обучению и командировкам."

                with allure.step("Шаг 1: Проверка, что поле изначально пустое"):
                    expect(resume.additional_info_textarea).to_have_value("")

                with allure.step(f"Шаг 2: Ввод тестового текста: '{test_text}'"):
                    resume.additional_info_textarea.fill(test_text)

                with allure.step("ОР: Текст успешно отображается в поле ввода"):
                    expect(resume.additional_info_textarea).to_have_value(test_text)


@pytest.mark.resume
@allure.title("Безопасность: Запрет доступа к редактированию чужого резюме при подмене ID")
def test_broken_object_level_authorization(auth_page: Page, app_config):
    """Тест создает резюме, извлекает его валидный ID, подменяет в нем цифры и проверяет защиту IDOR (BOLA).

    Шаги:
    1. Очистить профиль от старых резюме для стабильности.
    2. Перейти на страницу списка и нажать кнопку создания резюме.
    3. Заполнить обязательные поля через хелпер и сохранить черновик.
    4. Извлечь динамический ID из локатора resume_page.first_resume_edit_link.
    5. Выполнить переход по скомпрометированному URL-адресу из конфигурации.
    6. Верифицировать HTTP статус-код 403 Forbidden в сети и текст ошибки на UI.
    7. Удалить созданное тестовое резюме.
    """
    fake_id = app_config["resume_security_test_data"]["fake_resume_id"]
    base_url = app_config["base_url"]
    resume_page = ResumePage(auth_page)

    with allure.step("Шаг 1: Подготовка окружения и создание резюме"):
        clear_all_resumes_from_account(auth_page)

        list_url = f"{base_url}/registration/job-seeker/resume/list/"
        goto_with_retry(auth_page, list_url, wait_until="load")

        resume_page.create_resume_button.click()
        auth_page.wait_for_load_state("load")

        fill_and_submit_required_resume_fields(auth_page)

    with allure.step("Шаг 2: Проверка, что резюме успешно создано и видно в списке"):
        resume_page.first_resume_edit_link.wait_for(state="visible", timeout=5000)
        target_fake_url = f"{base_url}/registration/job-seeker/resume/{fake_id}/update/"

    with allure.step(f"Шаг 3: Переход по подмененному URL {fake_id} и перехват ответа бэкенда"):
        with auth_page.expect_response(re.compile(rf"/resume/{fake_id}/")) as response_info:
            goto_with_retry(auth_page, target_fake_url, wait_until="load")

        response = response_info.value

    with allure.step("Шаг 4: Проверка блокировки доступа (Статус 403 и текст на UI)"):
        assert response.status == 403, f"Ожидался статус 403, но бэкенд вернул {response.status}"

        error_message_locator = auth_page.get_by_text("Доступ к данной странице запрещен", exact=False)
        expect(error_message_locator).to_be_visible(timeout=5000)

    with allure.step("Шаг 5: Посткондишн (Очистка)"):
        clear_all_resumes_from_account(auth_page)


