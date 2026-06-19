from urllib.parse import unquote
import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_search_page import VacancySearchPage


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Поиск вакансий по профессии 'тестировщик' на странице поиска")
def test_guest_search_by_profession_on_search_page(auth_page: Page):
    page = auth_page
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
def test_guest_search_by_partial_text_on_search_page(auth_page: Page):
    page = auth_page
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
def test_guest_open_vacancy_detail_via_title(auth_page: Page):
    page = auth_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и ожидание результатов"):
        vacancy_page.navigate()
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Фиксация текста первой вакансии и переход по ссылке"):
        expected_title = vacancy_page.vacancy_title_link.first.text_content().strip()
        vacancy_page.vacancy_title_link.first.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Верификация URL карточки и заголовка вакансии"):
        expect(page).to_have_url(re.compile(r".*/registration/employer/vacancy/\d+/detail-public/"))
        expect(page.locator("h1").first).to_have_text(expected_title, timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Переход в контакты карточки вакансии по кнопке 'Контакты'")
def test_guest_open_vacancy_contacts(auth_page: Page):
    page = auth_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и ожидание результатов"):
        vacancy_page.navigate()
        vacancy_page.vacancy_contacts_button.first.wait_for(state="visible", timeout=5000)

    with allure.step("Шаг 2: Фиксация текста конкретной вакансии и клик по её кнопке 'Контакты'"):
        target_button = vacancy_page.vacancy_contacts_button.first

        # Находим родительский контейнер карточки для считывания точного названия
        xpath_selector = (
            "xpath=//a[contains(@href, 'detail-public/#contact-info-anchor')]"
            "/ancestor::div[contains(@class, 'col-md-9') or contains(@class, 'inner-box')]"
        )
        target_card = page.locator(xpath_selector).first
        expected_title = target_card.locator("a.debounced-link").text_content().strip()

        target_button.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Верификация перехода на блок контактов именно выбранной вакансии"):
        expect(page).to_have_url(
            re.compile(r".*/registration/employer/vacancy/\d+/detail-public/#contact-info-anchor")
        )
        expect(page.locator("h1").first).to_have_text(expected_title, timeout=5000)


@pytest.mark.vacancy_search
@allure.title("Бизнес-кейс: Проверка заблокированной кнопки 'Откликнуться' в списке вакансий")
def test_guest_apply_button_disabled_in_list(guest_page: Page):
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
    page = guest_page
    vacancy_page = VacancySearchPage(page)

    with allure.step("Шаг 1: Переход на страницу поиска и провал внутрь первой вакансии"):
        vacancy_page.navigate()
        vacancy_page.vacancy_title_link.first.wait_for(state="visible", timeout=5000)
        vacancy_page.vacancy_title_link.first.click()
        page.wait_for_load_state("networkidle")

    with allure.step("ОР 1: Верификация заблокированного состояния кнопки внутри карточки"):
        target_btn = vacancy_page.apply_button_in_detail.locator("visible=true").first
        target_btn.wait_for(state="visible", timeout=5000)
        expect(target_btn).to_contain_class("disabled")
        expect(target_btn).to_have_attribute("title", "Только соискатель может откликнуться на вакансию")
        expect(target_btn).to_have_attribute("disabled", "")