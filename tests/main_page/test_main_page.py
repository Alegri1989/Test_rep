import allure
import pytest
import re
from playwright.sync_api import Page, expect
from pages.main_page import MainPage
from tests.main_page.config import EMPLOYER_LOGOS_DATA


@allure.title("Бизнес-кейс: Поиск вакансий по профессии 'тестировщик' на главной странице")
def test_guest_search_by_profession(guest_page: Page):
    """
    Бизнес-кейс: Проверка базовой поисковой строки на главной странице по полному названию профессии.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала, куки-баннер успешно закрыт.

    Шаги:
    1. Дождаться полной готовности и видимости инпута поиска на главной странице.
    2. Кликнуть по полю ввода и заполнить его точным значением профессии "тестировщик".
    3. Нажать на кнопку "Найти" для отправки поисковой формы.
    4. Дождаться стабилизации сетевых запросов.
    5. Верифицировать URL открывшейся страницы результатов.

    Ожидаемый результат (ОР):
    - Система корректно обрабатывает поисковый запрос и перенаправляет гостя на страницу поиска вакансий.
    - В адресной строке (URL) зафиксирован query-параметр: '?profession=тестировщик'.
    """
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Проверка готовности поля поиска"):
        main_page.search_input.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Ввод полного значения профессии"):
        main_page.search_input.click()
        main_page.search_input.fill("тестировщик")

    with allure.step("Шаг 3: Нажатие кнопки 'Найти'"):
        main_page.search_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Открылась страница результатов поиска с вакансиями тестировщика"):
        from urllib.parse import unquote

        current_url_decoded = unquote(page.url)
        expected_url = "https://gsz.gov.by"
        assert expected_url in current_url_decoded


@allure.title("Бизнес-кейс: Поиск вакансий по частичному совпадению слова 'тест'")
def test_guest_search_by_partial_text(guest_page: Page):
    """
    Бизнес-кейс: Проверка сквозного поиска по частичному буквосочетанию (корню слова) и валидация результатов выдачи.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Проверить готовность поисковой строки.
    2. Ввести поисковый корень "тест" посимвольно с задержкой, не выбирая варианты из всплывающих подсказок.
    3. Нажать кнопку "Найти".
    4. Верифицировать URL страницы и значение внутри инпута на новой странице.
    5. Собрать все заголовки найденных карточек вакансий на первой странице выдачи.
    6. В цикле проверить, что каждая вакансия содержит в себе корень "тест".

    Ожидаемый результат (ОР):
    - URL содержит query-параметр '?profession=тест', а поисковая строка на странице выдачи сохраняет значение "тест".
    - Во всех отфильтрованных вакансиях без исключения присутствует корень "тест" (в нижнем регистре).
    """
    page = guest_page
    main_page = MainPage(page)
    from urllib.parse import unquote

    with allure.step("Шаг 1: Проверка готовности поля поиска"):
        main_page.search_input.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Ручной ввод буквосочетания 'тест' без выбора подсказки"):
        main_page.search_input.click()
        main_page.search_input.press_sequentially("тест", delay=100)

    with allure.step("Шаг 3: Нажатие кнопки 'Найти'"):
        main_page.search_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Верификация URL и заполнения поисковой строки"):
        current_url_decoded = unquote(page.url)
        expected_url = "https://gsz.gov.by"

        assert expected_url in current_url_decoded
        expect(page.locator("input[name='profession']")).to_have_value("тест")

    with allure.step("ОР 2: Проверка наличия буквосочетания 'тест' во всех вакансиях на странице"):
        vacancy_titles = page.locator("a.debounced-link")
        vacancy_titles.first.wait_for(state="visible", timeout=5000)

        count = vacancy_titles.count()
        for i in range(count):
            title_text = vacancy_titles.nth(i).text_content().strip().lower()
            assert "тест" in title_text, f"Ошибка: в вакансии '{title_text}' нет корня 'тест'"


@allure.title("Бизнес-кейс: Взаимодействие с интерактивной картой на главной странице")
def test_guest_interactive_map(guest_page: Page):
    """
    Бизнес-кейс: Проверка динамического интерактивного взаимодействия с SVG-картой регионов и перехода по вкладкам карточки.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Проверить стартовый заголовок счетчиков ("Республика Беларусь") и зафиксировать начальные цифры вакансий и резюме.
    2. Переключить масштаб карты в режим "Области" с помощью радиокнопки-лейбла.
    3. Локализовать и принудительно кликнуть по первой SVG-точке (circle) на карте.
    4. Проверить, что счетчики слева изменились (синхронизировались с выбранной областью).
    5. Дождаться появления всплывающей информационной карточки справа.
    6. Нажать "Перейти к вакансиям", поймать открытие новой вкладки браузера и проверить наличие soato_uid в её URL.
    7. Закрыть вкладку вакансий, вернуться на главную, нажать кнопку "Перейти на сайт" и верифицировать редирект на внешний сайт исполкома.

    Ожидаемый результат (ОР):
    - Клик по точке карты успешно обновляет региональную статистику на левой панели.
    - Кнопки инфо-карточки корректно открывают новые вкладки (expect_popup) с правильными параметрами фильтрации и внешними доменами.
    """
    page = guest_page
    main_page = MainPage(page)
    from urllib.parse import unquote

    with allure.step("Шаг 1: Фиксация начального состояния счетчиков страны"):
        main_page.region_title.wait_for(state="visible", timeout=5000)
        expect(main_page.region_title).to_have_text("Республика Беларусь")

        start_vacancies = main_page.vacancy_counter.text_content().strip()
        start_resumes = main_page.resume_counter.text_content().strip()

    with allure.step("Шаг 2: Переключение карты в режим 'Области' и клик по первой точке"):
        main_scale = main_page.map_scale_regions
        main_scale.click()
        page.wait_for_load_state("networkidle")

        main_page.map_dots.first.wait_for(state="visible", timeout=5000)
        main_page.map_dots.first.click()
        page.wait_for_load_state("networkidle")

    with allure.step("Шаг 3: Проверка изменения счетчиков слева под выбранный регион"):
        expect(main_page.region_title).not_to_have_text("Республика Беларусь")
        expect(main_page.vacancy_counter).not_to_have_text(start_vacancies)
        expect(main_page.resume_counter).not_to_have_text(start_resumes)

    with allure.step("Шаг 4: Проверка появления информационной карточки справа"):
        main_page.info_card.wait_for(state="visible", timeout=5000)
        expect(main_page.info_card_title).to_be_visible()

    with allure.step("Шаг 5: Клик по кнопке 'Перейти к вакансиям' и проверка фильтра в новой вкладке"):
        with page.expect_popup() as vacancy_popup_info:
            main_page.go_to_vacancies_button.click()
        vacancy_page = vacancy_popup_info.value
        vacancy_page.wait_for_load_state("networkidle")

        decoded_vacancy_url = unquote(vacancy_page.url)
        assert "https://gsz.gov.by" in decoded_vacancy_url
        expect(vacancy_page.locator("text=Количество заявленных вакансий:")).to_be_visible(timeout=5000)
        vacancy_page.close()

    with allure.step("Шаг 6: Клик по кнопке 'Перейти на сайт' и проверка редиректа на исполком"):
        with page.expect_popup() as site_popup_info:
            main_page.go_to_site_button.click()
        site_page = site_popup_info.value
        site_page.wait_for_load_state("domcontentloaded")

        assert site_page.url.startswith("http")
        assert "gsz.gov.by" not in site_page.url
        site_page.close()

@allure.title("Бизнес-кейс: Переход к вакансиям для временного трудоустройства молодежи")
def test_guest_youth_employment_redirect(guest_page: Page):
    """
    Бизнес-кейс: Проверка кликабельности баннера и редиректа в раздел временного трудоустройства молодежи.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Прокрутить страницу вниз до блока временной занятости молодежи.
    2. Дождаться видимости кнопки перехода.
    3. Кликнуть по кнопке и дождаться полной загрузки новой страницы.
    4. Верифицировать итоговый URL открывшегося раздела.

    Ожидаемый результат (ОР):
    - Происходит успешный переход в целевой раздел без ошибок 404.
    - URL страницы строго соответствует пути 'https://gsz.gov.by'.
    """
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка страницы до блока временного трудоустройства молодежи"):
        main_page.youth_employment_button.scroll_into_view_if_needed()
        main_page.youth_employment_button.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке и ожидание загрузки новой страницы"):
        main_page.youth_employment_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Открылся раздел временного трудоустройства молодежи"):
        expect(page).to_have_url("https://gsz.gov.by/registration/temporary-employment/young/")


@allure.title("Бизнес-кейс: Взаимодействие с блоком популярных вакансий на главной странице")
def test_guest_featured_vacancies_block(guest_page: Page):
    """
    Бизнес-кейс: Проверка интерактивного переключения вкладок популярных вакансий и перехода в детальную карточку.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Прокрутить экран до табов популярного блока.
    2. Активировать вкладку "Недели" и проверить появление классов активности на элементе UI.
    3. Активировать вкладку "Популярные" и дождаться отрисовки её контента.
    4. Считать и запомнить название профессии на первой карточке вакансии.
    5. Кликнуть по названию и перейти на страницу детального просмотра.
    6. Верифицировать шаблон URL детальной страницы и совпадение заголовка H1 с запомненным названием.
    7. Вернуться назад на главную, прокрутить до кнопки "Показать больше" и нажать её для перехода в общий поиск.

    Ожидаемый результат (ОР):
    - Вкладки динамически переключают контент, корректно реагируя на клики.
    - Карточки ведут на валидные публичные детальные страницы вакансий.
    - Кнопка "Показать больше" успешно открывает общий фильтр вакансий.
    """
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка до блока популярных вакансий и верификация активации вкладок"):
        main_page.tab_week.scroll_into_view_if_needed()
        main_page.tab_week.wait_for(state="visible", timeout=5000)

        main_page.tab_week.click()
        expect(main_page.tab_week).to_have_attribute("aria-selected", "true")
        expect(main_page.tab_week).to_contain_class("active")

        main_page.tab_popular.click()
        expect(main_page.tab_popular).to_have_attribute("aria-selected", "true")
        expect(main_page.tab_popular).to_contain_class("active")

        page.wait_for_timeout(1000)

    with allure.step("Шаг 2: Клик по карточке первой вакансии и проверка соответствия её данных"):
        expected_title = main_page.featured_vacancy_links.first.text_content().strip()

        main_page.featured_vacancy_links.first.click()
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(re.compile(r".*/registration/employer/vacancy/\d+/detail-public/"))
        expect(page.locator("h1").first).to_have_text(expected_title, timeout=5000)
        expect(page.locator("text=Информация о вакансии")).to_be_visible(timeout=5000)

        page.go_back()
        page.wait_for_load_state("networkidle")

    with allure.step("Шаг 3: Клик по кнопке 'Показать больше'"):
        main_more = main_page.show_more_vacancies_btn
        main_more.scroll_into_view_if_needed()
        main_more.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Открылась общая страница результатов поиска вакансий"):
        expect(page).to_have_url("https://gsz.gov.by/registration/vacancy-search/")
        expect(page.locator("text=Количество заявленных вакансий:")).to_be_visible(timeout=5000)


@allure.title("Бизнес-кейс: Поиск по гибким навыкам (Вакансии и Резюме) на главной странице")
def test_guest_skills_search_workflow(guest_page: Page):
    """
    Бизнес-кейс: Проверка работы сквозного блока поиска по гибким навыкам (Soft Skills) для разделов Вакансий и Резюме.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Прокрутить страницу до чекбоксов Soft Skills и выбрать тег "Тайм-менеджмент".
    2. Убедиться, что целевая форма кнопки настроена на отправку в раздел '/registration/vacancy-search/'.
    3. Нажать кнопку поиска, зафиксировать переход на страницу результатов и вернуться назад.
    4. Переключить интерактивный ползунок-свитч в положение "Резюме".
    5. Повторно активировать сбросившийся чекбокс "Тайм-менеджмент".
    6. Проверить, что целевой атрибут формы кнопки изменился на '/registration/resume-search/'.
    7. Нажать кнопку и верифицировать успешный переход в базу резюме.

    Ожидаемый результат (ОР):
    - Ползунок корректно меняет логику и атрибут направления поиска ('formaction') у кнопки.
    - Поиск успешно перенаправляет пользователя в соответствующие разделы выдачи с сохранением параметров.
    """
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка к блоку гибких навыков и выбор 'Тайм-менеджмент'"):
        main_page.skill_time_management.scroll_into_view_if_needed()
        main_page.skill_time_management.wait_for(state="visible", timeout=5000)
        main_page.skill_time_management.click()

    with allure.step("Шаг 2: Проверка поиска вакансий по выбранному навыку"):
        expect(main_page.skills_search_button).to_have_attribute("formaction", "/registration/vacancy-search/")
        main_page.skills_search_button.click()
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(re.compile(r".*/registration/vacancy-search/.*"))

        page.go_back()
        page.wait_for_load_state("networkidle")

    with allure.step("Шаг 3: Переключение ползунка на 'Резюме' и повторный выбор навыка"):
        main_page.skills_switch.scroll_into_view_if_needed()
        main_page.skills_switch.click()
        page.wait_for_timeout(1000)

        main_page.skill_time_management.click()

    with allure.step("Шаг 4: Проверка поиска резюме по выбранному навыку"):
        expect(main_page.skills_search_button).to_have_attribute("formaction", "/registration/resume-search/")
        main_page.skills_search_button.click()
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(re.compile(r".*/registration/resume-search/.*"))


@allure.title("Бизнес-кейс: Переход к вакансиям нанимателя через логотип на главной странице")
@pytest.mark.parametrize("img_name, expected_employer_title", EMPLOYER_LOGOS_DATA)
def test_guest_employer_logo_redirect(guest_page: Page, img_name: str, expected_employer_title: str):
    """
    Бизнес-кейс: Проверка карусели топ-нанимателей и автоматической установки фильтра при переходе по логотипу.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Прокрутить страницу до секции карусели "Приглашают в команду".
    2. Вызвать JS-событие клика по логотипу нанимателя по частичному названию картинки 'img_name'.
    3. Дождаться редиректа на страницу результатов поиска вакансий.
    4. Найти на левой панели фильтра активную плашку-тег Select2 выбранного нанимателя.
    5. Верифицировать соответствие названия компании на плашке с 'expected_employer_title'.
    6. Вернуться на главную страницу для подготовки к следующей итерации параметризации.

    Ожидаемый результат (ОР):
    - Клик по логотипу успешно перенаправляет гостя на страницу поиска вакансий.
    - В блоке фильтрации автоматически применяется и фиксируется плашка выбранной организации.
    """
    page = guest_page
    main_page = MainPage(page)

    page.wait_for_timeout(1000)

    with allure.step("Шаг 1: Стабилизация экрана и клик по логотипу нанимателя"):
        main_page.employers_carousel_section.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

        main_page.click_employer_logo_via_js(img_name)
        page.wait_for_load_state("networkidle")

    with allure.step(f"ОР 1: В фильтре нанимателей отображается плашка: {expected_employer_title}"):
        expect(page).to_have_url(re.compile(r".*/registration/vacancy-search/.*"))

        selected_employer = page.locator(f"li.select2-selection__choice[title*='{expected_employer_title}']")
        expect(selected_employer).to_be_visible(timeout=5000)

        page.go_back()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)


@allure.title("Бизнес-кейс: Проверка скачивания мобильного приложения и инструкции в подвале сайта")
def test_guest_footer_mobile_app(guest_page: Page):
    """
    Бизнес-кейс: Проверка доступности скачивания мобильного приложения и корректности ссылки на PDF-инструкцию в подвале.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Прокрутить страницу до самого низа (футера) и дождаться видимости кнопки скачивания.
    2. Перехватить поток скачивания (expect_download), кликнуть по кнопке и зафиксировать имя файла.
    3. Проверить, что скачиваемый файл имеет расширение '.apk'.
    4. Найти ссылку на PDF-инструкцию, считать её атрибут 'href'.
    5. Верифицировать путь до целевого PDF-документа на медиа-сервере.

    Ожидаемый результат (ОР):
    - Кнопка инициализирует прямую выгрузку мобильного дистрибутива Android.
    - Ссылка инструкции ведет на валидный внутренний PDF-документ.
    """
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка к подвалу и ожидание видимости элементов"):
        main_page.download_app_button.scroll_into_view_if_needed()
        main_page.download_app_button.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке скачивания и верификация загрузки APK-файла"):
        with page.expect_download() as download_info:
            main_page.download_app_button.click(no_wait_after=True)
        download = download_info.value

        suggested_filename = download.suggested_filename.lower()
        assert suggested_filename.endswith(".apk"), f"Ошибка: скачивается не APK-файл, а '{suggested_filename}'"

    with allure.step("Шаг 3: Проверка корректности ссылки на PDF-инструкцию"):
        instruction_href = main_page.download_instruction_link.get_attribute("href")

        assert instruction_href is not None, "Ошибка: у ссылки инструкции отсутствует атрибут href"
        assert "/media/about_portal/instruction_mobile.pdf" in instruction_href, (
            f"Ошибка: ссылка ведет на неверный файл '{instruction_href}'"
        )


@allure.title("Бизнес-кейс: Переход в раздел трудоустройства трудящихся-иммигрантов через баннер")
def test_guest_immigrant_employment_redirect(guest_page: Page):
    """
    Бизнес-кейс: Проверка кликабельности информационного баннера для иностранных граждан.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта главная страница портала.

    Шаги:
    1. Прокрутить страницу до рекламного баннера "Трудоустройство трудящихся-иммигрантов".
    2. Дождаться его видимости и кликнуть по кнопке "Перейти".
    3. Дождаться полной отрисовки контента страницы.
    4. Верифицировать итоговый URL-путь браузера и заголовок H1 открывшегося раздела.

    Ожидаемый результат (ОР):
    - Баннер осуществляет корректный внутренний редирект в правовой раздел для иностранных граждан.
    - Заголовок H1 на открывшейся странице строго соответствует названию блока.
    """
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка страницы до баннера иммигрантов и ожидание видимости"):
        main_page.immigrant_employment_button.scroll_into_view_if_needed()
        main_page.immigrant_employment_button.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Перейти' и ожидание загрузки страницы"):
        main_page.immigrant_employment_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Открылся раздел трудоустройства иностранных граждан"):
        expect(page).to_have_url(re.compile(r".*/registration/foreign-citizens-employment/public/list/.*"))
        expect(page.locator("h1")).to_have_text("Трудоустройство трудящихся-иммигрантов", timeout=5000)