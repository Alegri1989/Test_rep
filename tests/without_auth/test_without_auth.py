from urllib.parse import unquote
import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_search_page import VacancySearchPage


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Поиск вакансий по профессии 'тестировщик' на странице поиска")
def test_guest_search_by_profession_on_search_page(guest_page: Page):
    """
    Бизнес-кейс: Проверка работы текстовой строки поиска по полному названию профессии на самой странице поиска.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта страница поиска вакансий портала.

    Шаги:
    1. Проверить готовность поисковой строки на форме фильтров.
    2. Заполнить инпут точным текстовым значением "тестировщик".
    3. Нажать кнопку "Найти" для применения фильтра.
    4. Декодировать текущий URL-адрес из адресной строки браузера.
    5. Проверить наличие правильного хвостового query-параметра.

    Ожидаемый результат (ОР):
    - Поисковая форма успешно обрабатывает текстовый запрос.
    - URL-адрес содержит декодированную строку '/registration/vacancy-search/?profession=тестировщик'.
    """
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и проверка готовности поля"):
        vacancy_page.navigate()
        vacancy_page.search_input.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Ввод полного значения профессии"):
        vacancy_page.search_input.click()
        vacancy_page.search_input.fill("тестировщик")

    with allure.step("Шаг 3: Нажатие кнопки 'Найти'"):
        vacancy_page.search_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Верификация декодированного URL"):
        current_url_decoded = unquote(page.url)
        expected_url = "/registration/vacancy-search/?profession=тестировщик"
        assert expected_url in current_url_decoded, f"Ошибка: неверный URL '{current_url_decoded}'"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Поиск вакансий по частичному совпадению слова 'тест'")
def test_guest_search_by_partial_text_on_search_page(guest_page: Page):
    """
    Бизнес-кейс: Проверка работы текстового поиска по корню слова и валидация заголовков всей первой страницы выдачи.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта страница поиска вакансий портала.

    Шаги:
    1. Убедиться в видимости поисковой строки на странице.
    2. Ввести поисковый корень "тест" посимвольно с задержкой, не выбирая всплывающие подсказки.
    3. Нажать кнопку "Найти".
    4. Верифицировать query-параметры в декодированном URL и значение инпута на новой странице.
    5. Собрать заголовки всех найденных карточек вакансий в текущей выдаче.
    6. В цикле проверить, что каждая вакансия содержит в себе корень "тест".

    Ожидаемый результат (ОР):
    - URL содержит query-параметр '?profession=тест', а поле поиска на странице сохраняет значение "тест".
    - Во всех отфильтрованных вакансиях на странице присутствует корень "тест" в нижнем регистре.
    """
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и проверка готовности поля"):
        vacancy_page.navigate()
        vacancy_page.search_input.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Ручной ввод буквосочетания 'тест' без выбора подсказки"):
        vacancy_page.search_input.click()
        vacancy_page.search_input.press_sequentially("тест", delay=100)

    with allure.step("Шаг 3: Нажатие кнопки 'Найти'"):
        vacancy_page.search_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Верификация декодированного URL и заполнения поисковой строки"):
        current_url_decoded = unquote(page.url)
        expected_url = "/registration/vacancy-search/?profession=тест"

        assert expected_url in current_url_decoded, f"Ошибка: неверный URL '{current_url_decoded}'"
        expect(page.locator("input[name='profession']")).to_have_value("тест")

    with allure.step("ОР 2: Проверка наличия буквосочетания 'тест' во всех вакансиях на странице"):
        vacancy_titles = page.locator("a.debounced-link")
        vacancy_titles.first.wait_for(state="visible", timeout=5000)

        count = vacancy_titles.count()
        for i in range(count):
            title_text = vacancy_titles.nth(i).text_content().strip().lower()
            assert "тест" in title_text, f"Ошибка: в вакансии '{title_text}' нет корня 'тест'"


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Переход в карточку вакансии по клику на её название")
def test_guest_open_vacancy_detail_via_title(guest_page: Page):
    """
    Бизнес-кейс: Проверка сквозного перехода на детальную страницу вакансии по клику на её заголовок.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта страница поиска вакансий портала.

    Шаги:
    1. Перейти на страницу поиска и дождаться появления первой карточки результатов выдачи.
    2. Считать и запомнить точное текстовое название профессии на первой карточке.
    3. Кликнуть по ссылке названия вакансии.
    4. Дождаться полного обновления сети и загрузки детальной публичной страницы.
    5. Верифицировать шаблон URL-адреса и совпадение заголовка h1 с эталоном.

    Ожидаемый результат (ОР):
    - Ссылка корректно перенаправляет гостя на публичную страницу карточки вакансии.
    - Название профессии в h1 полностью идентично заголовку карточки из общего списка.
    """
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и ожидание результатов"):
        vacancy_page.navigate()
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Фиксация текста первой вакансии и переход по ссылке"):
        expected_title = vacancy_page.vacancy_title_link.first.text_content().strip()
        vacancy_page.vacancy_title_link.first.click()
        page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация URL карточки и заголовка вакансии"):
        expect(page).to_have_url(re.compile(r".*/registration/employer/vacancy/\d+/detail-public/"))
        expect(page.locator("h1").first).to_have_text(expected_title, timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Переход в контакты карточки вакансии по кнопке 'Контакты'")
def test_guest_open_vacancy_contacts(guest_page: Page):
    """
    Бизнес-кейс: Проверка перехода к блоку контактной информации вакансии по якорной ссылке.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта страница поиска вакансий портала.

    Шаги:
    1. Перейти на страницу поиска и дождаться готовности кнопки "Контакты" на первой карточке.
    2. Подняться по DOM-дереву до родительского контейнера карточки через ancestor, чтобы считать точный заголовок вакансии.
    3. Нажать кнопку "Контакты" для перехода на детальную страницу.
    4. Верифицировать, что URL содержит якорный хвост '#contact-info-anchor'.
    5. Проверить совпадение названия вакансии в заголовке h1.

    Ожидаемый результат (ОР):
    - Кнопка "Контакты" выполняет редирект на публичную страницу с автоматическим скроллом к блоку контактов.
    - В адресной строке зафиксирован якорь контакта выбранной вакансии.
    """
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и ожидание результатов"):
        vacancy_page.navigate()
        vacancy_page.vacancy_contacts_button.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Фиксация текста конкретной вакансии и клик по её кнопке 'Контакты'"):
        target_button = vacancy_page.vacancy_contacts_button.first

        xpath_selector = (
            "xpath=//a[contains(@href, 'detail-public/#contact-info-anchor')]"
            "/ancestor::div[contains(@class, 'col-md-9') or contains(@class, 'inner-box')]"
        )
        target_card = page.locator(xpath_selector).first
        expected_title = target_card.locator("a.debounced-link").text_content().strip()

        target_button.click()
        page.wait_for_load_state("load")
        page.locator("h1").first.wait_for(state="visible", timeout=10000)

    with allure.step("ОР 1: Верификация перехода на блок контактов именно выбранной вакансии"):
        expect(page).to_have_url(
            re.compile(r".*/registration/employer/vacancy/\d+/detail-public/#contact-info-anchor")
        )
        expect(page.locator("h1").first).to_have_text(expected_title, timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Проверка заблокированной кнопки 'Откликнуться' в списке вакансий")
def test_guest_apply_button_disabled_in_list(guest_page: Page):
    """
    Бизнес-кейс: Валидация недоступности кнопки отклика для неавторизованного гостя в общем списке вакансий.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта страница поиска вакансий портала.

    Шаги:
    1. Перейти на страницу поиска и локализовать первую видимую кнопку отклика.
    2. Убедиться, что кнопка содержит CSS-класс 'disabled'.
    3. Сверить значение атрибута 'title' на предмет вывода предупреждения.
    4. Проверить наличие нативного HTML-атрибута 'disabled'.

    Ожидаемый результат (ОР):
    - Система строго блокирует возможность отклика на вакансии для неавторизованных гостей в поисковой выдаче.
    - Кнопка полностью неактивна, подсказка содержит текст: "Только соискатель может откликнуться на вакансию".
    """
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и ожидание результатов"):
        vacancy_page.navigate()
        vacancy_page.apply_button_in_list.locator("visible=true").first.wait_for(state="visible", timeout=5000)

    with allure.step("ОР 1: Верификация заблокированного состояния кнопки в списке"):
        target_btn = vacancy_page.apply_button_in_list.locator("visible=true").first
        expect(target_btn).to_contain_class("disabled")
        expect(target_btn).to_have_attribute("title", "Только соискатель может откликнуться на вакансию")
        expect(target_btn).to_have_attribute("disabled", "")


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Проверка заблокированной кнопки 'Откликнуться' внутри карточки вакансии")
def test_guest_apply_button_disabled_in_detail_page(guest_page: Page):
    """
    Бизнес-кейс: Валидация недоступности кнопки отклика для неавторизованного гостя на детальной странице вакансии.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Открыта страница поиска вакансий портала.

    Шаги:
    1. Перейти на страницу поиска и дождаться результатов.
    2. Кликнуть по ссылке-заголовку первой вакансии для перехода внутрь карточки.
    3. Дождаться полной отрисовки детальной публичной страницы.
    4. Локализовать кнопку "Откликнуться" внутри страницы и дождаться её видимости.
    5. Проверить наличие CSS-класса 'disabled' на кнопке.
    6. Сверить значение атрибута 'title' всплывающей подсказки ограничения.
    7. Проверить наличие нативного HTML-атрибута 'disabled'.

    Ожидаемый результат (ОР):
    - Система строго блокирует отправку откликов внутри публичной карточки вакансии для гостей без авторизации.
    - Кнопка полностью неактивна, а подсказка содержит текст: "Только соискатель может откликнуться на вакансию".
    """
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и провал внутрь первой вакансии"):
        vacancy_page.navigate()
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        page.wait_for_load_state("load")

    with allure.step("ОР 1: Верификация заблокированного состояния кнопки внутри карточки"):
        target_btn = vacancy_page.apply_button_in_detail.locator("visible=true").first
        target_btn.wait_for(state="visible", timeout=5000)
        expect(target_btn).to_contain_class("disabled")
        expect(target_btn).to_have_attribute("title", "Только соискатель может откликнуться на вакансию")
        expect(target_btn).to_have_attribute("disabled", "")