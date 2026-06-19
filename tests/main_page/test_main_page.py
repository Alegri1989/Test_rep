import allure
import pytest
import re
from playwright.sync_api import Page, expect
from pages.main_page import MainPage
from tests.main_page.config import EMPLOYER_LOGOS_DATA


@allure.title("Бизнес-кейс: Поиск вакансий по профессии 'тестировщик' на главной странице")
def test_guest_search_by_profession(guest_page: Page):
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

        expected_url = "https://gsz.gov.by/registration/vacancy-search/?profession=тестировщик"
        assert expected_url in current_url_decoded


@allure.title("Бизнес-кейс: Поиск вакансий по частичному совпадению слова 'тест'")
def test_guest_search_by_partial_text(guest_page: Page):
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
        expected_url = "https://gsz.gov.by/registration/vacancy-search/?profession=тест"

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
    page = guest_page
    main_page = MainPage(page)
    from urllib.parse import unquote

    with allure.step("Шаг 1: Фиксация начального состояния счетчиков страны"):
        main_page.region_title.wait_for(state="visible", timeout=5000)
        expect(main_page.region_title).to_have_text("Республика Беларусь")

        start_vacancies = main_page.vacancy_counter.text_content().strip()
        start_resumes = main_page.resume_counter.text_content().strip()

    with allure.step("Шаг 2: Переключение карты в режим 'Области' и клик по первой точке"):
        main_page.map_scale_regions.click()
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
        # Ловим открытие новой вкладки при клике
        with page.expect_popup() as vacancy_popup_info:
            main_page.go_to_vacancies_button.click()
        vacancy_page = vacancy_popup_info.value
        vacancy_page.wait_for_load_state("networkidle")

        # Проверяем, что в URL новой вкладки есть параметр региона soato_uid
        decoded_vacancy_url = unquote(vacancy_page.url)
        assert "https://gsz.gov.by/registration/vacancy-search/?soato_uid=".replace(" ", "") in decoded_vacancy_url

        # Убеждаемся, что на открывшейся странице виден блок фильтра региона
        expect(vacancy_page.locator("text=Количество заявленных вакансий:")).to_be_visible(timeout=5000)

        # Закрываем вкладку вакансий, чтобы вернуться на главную
        vacancy_page.close()

    with allure.step("Шаг 6: Клик по кнопке 'Перейти на сайт' и проверка редиректа на исполком"):
        # Ловим открытие второй новой вкладки при клике
        with page.expect_popup() as site_popup_info:
            main_page.go_to_site_button.click()
        site_page = site_popup_info.value
        site_page.wait_for_load_state("domcontentloaded")

        # Проверяем, что открылся полноценный внешний сайт и это не пустая страница
        assert site_page.url.startswith("http")
        assert "gsz.gov.by" not in site_page.url

        # Закрываем вкладку исполкома
        site_page.close()


@allure.title("Бизнес-кейс: Переход к вакансиям для временного трудоустройства молодежи")
def test_guest_youth_employment_redirect(guest_page: Page):
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка страницы до блока временного трудоустройства молодежи"):
        main_page.youth_employment_button.scroll_into_view_if_needed()
        main_page.youth_employment_button.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке и ожидание загрузки новой страницы"):
        main_page.youth_employment_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Открылся раздел временного трудоустройства молодежи"):
        # Проверяем успешный переход по уникальному хвосту URL без домена
        expect(page).to_have_url("https://gsz.gov.by/registration/temporary-employment/young/")


@allure.title("Бизнес-кейс: Взаимодействие с блоком популярных вакансий на главной странице")
def test_guest_featured_vacancies_block(guest_page: Page):
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка до блока популярных вакансий и верификация активации вкладок"):
        main_page.tab_week.scroll_into_view_if_needed()
        main_page.tab_week.wait_for(state="visible", timeout=5000)

        # Переключаемся на вкладку 'Недели' и проверяем её статус активности
        main_page.tab_week.click()
        expect(main_page.tab_week).to_have_attribute("aria-selected", "true")
        expect(main_page.tab_week).to_contain_class("active")

        # Переключаемся на вкладку 'Популярные' и проверяем её статус активности
        main_page.tab_popular.click()
        expect(main_page.tab_popular).to_have_attribute("aria-selected", "true")
        expect(main_page.tab_popular).to_contain_class("active")

        # Ждем, пока вкладка "Популярные" отобразит свои элементы на экране
        page.wait_for_timeout(1000)

    with allure.step("Шаг 2: Клик по карточке первой вакансии и проверка соответствия её данных"):

        # Запоминаем название профессии из первой карточки блока "Популярные"
        expected_title = main_page.featured_vacancy_links.first.text_content().strip()

        # Переходим на страницу детального просмотра вакансии
        main_page.featured_vacancy_links.first.click()
        page.wait_for_load_state("networkidle")

        # ОР: Проверяем URL с помощью скомпилированного регулярного выражения
        expect(page).to_have_url(re.compile(r".*/registration/employer/vacancy/\d+/detail-public/"))

        # Соотносим: берем именно первый h1 на странице для проверки названия
        expect(page.locator("h1").first).to_have_text(expected_title, timeout=5000)
        expect(page.locator("text=Информация о вакансии")).to_be_visible(timeout=5000)

        # Возвращаемся обратно на главную страницу
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
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка к блоку гибких навыков и выбор 'Тайм-менеджмент'"):
        main_page.skill_time_management.scroll_into_view_if_needed()
        main_page.skill_time_management.wait_for(state="visible", timeout=5000)
        main_page.skill_time_management.click()

    with allure.step("Шаг 2: Проверка поиска вакансий по выбранному навыку"):
        # Проверяем, что кнопка настроена на поиск вакансий
        expect(main_page.skills_search_button).to_have_attribute("formaction", "/registration/vacancy-search/")
        main_page.skills_search_button.click()
        page.wait_for_load_state("networkidle")

        # ОР: Проверяем URL через re.compile
        expect(page).to_have_url(re.compile(r".*/registration/vacancy-search/.*"))

        # Возвращаемся обратно на главную страницу
        page.go_back()
        page.wait_for_load_state("networkidle")

    with allure.step("Шаг 3: Переключение ползунка на 'Резюме' и повторный выбор навыка"):
        main_page.skills_switch.scroll_into_view_if_needed()
        main_page.skills_switch.click()
        page.wait_for_timeout(1000)  # Даем форме время обновить атрибуты кнопки

        # Заново активируем навык, так как состояние сбросилось
        main_page.skill_time_management.click()

    with allure.step("Шаг 4: Проверка поиска резюме по выбранному навыку"):
        # Проверяем, что кнопка изменила атрибут на поиск резюме
        expect(main_page.skills_search_button).to_have_attribute("formaction", "/registration/resume-search/")
        main_page.skills_search_button.click()
        page.wait_for_load_state("networkidle")

        # ОР: Проверяем URL через re.compile
        expect(page).to_have_url(re.compile(r".*/registration/resume-search/.*"))


@allure.title("Бизнес-кейс: Переход к вакансиям нанимателя через логотип на главной странице")
@pytest.mark.parametrize("img_name, expected_employer_title", EMPLOYER_LOGOS_DATA)
def test_guest_employer_logo_redirect(guest_page: Page, img_name: str, expected_employer_title: str):
    page = guest_page
    main_page = MainPage(page)

    # Небольшая пауза на старте цикла, чтобы дать карусели стабилизироваться после прошлого прогона
    page.wait_for_timeout(1000)

    with allure.step("Шаг 1: Стабилизация экрана и клик по логотипу нанимателя"):
        main_page.employers_carousel_section.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)  # Даем экрану замереть после прокрутки

        main_page.click_employer_logo_via_js(img_name)
        page.wait_for_load_state("networkidle")

    with allure.step(f"ОР 1: В фильтре нанимателей отображается плашка: {expected_employer_title}"):
        expect(page).to_have_url(re.compile(r".*/registration/vacancy-search/.*"))

        selected_employer = page.locator(f"li.select2-selection__choice[title*='{expected_employer_title}']")
        expect(selected_employer).to_be_visible(timeout=5000)

        # Возвращаемся на главную и даем ей время на полную отрисовку
        page.go_back()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)


@allure.title("Бизнес-кейс: Проверка скачивания мобильного приложения и инструкции в подвале сайта")
def test_guest_footer_mobile_app(guest_page: Page):
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
        # Получаем значение атрибута href у ссылки
        instruction_href = main_page.download_instruction_link.get_attribute("href")

        # ОР: Проверяем, что ссылка ведет на правильный PDF-файл инструкции
        assert instruction_href is not None, "Ошибка: у ссылки инструкции отсутствует атрибут href"
        assert "/media/about_portal/instruction_mobile.pdf" in instruction_href, (
            f"Ошибка: ссылка ведет на неверный файл '{instruction_href}'"
        )


@allure.title("Бизнес-кейс: Переход в раздел трудоустройства трудящихся-иммигрантов через баннер")
def test_guest_immigrant_employment_redirect(guest_page: Page):
    page = guest_page
    main_page = MainPage(page)

    with allure.step("Шаг 1: Прокрутка страницы до баннера иммигрантов и ожидание видимости"):
        main_page.immigrant_employment_button.scroll_into_view_if_needed()
        main_page.immigrant_employment_button.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Клик по кнопке 'Перейти' и ожидание загрузки страницы"):
        main_page.immigrant_employment_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Открылся раздел трудоустройства иностранных граждан"):
        # Делаем проверку URL гибкой через регулярное выражение, убирая падения из-за слешей
        expect(page).to_have_url(re.compile(r".*/registration/foreign-citizens-employment/public/list/.*"))
        expect(page.locator("h1")).to_have_text("Трудоустройство трудящихся-иммигрантов", timeout=5000)
