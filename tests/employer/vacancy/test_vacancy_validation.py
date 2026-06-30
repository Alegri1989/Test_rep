import allure
import pytest
from playwright.sync_api import Page, expect
from pages.vacancy_create_page import VacancyCreatePage


@pytest.mark.validation
class TestVacancyFieldValidation:

    @allure.title("Свободно рабочих мест < сумма 'Из них' → ошибка под полем")
    def test_available_places_less_than_sub_total(
        self, open_create_vacancy_page: Page
    ):
        """
        Если «Свободно рабочих мест» < суммы полей «Из них»,
        после нажатия «Сохранить» появляется сообщение
        «Недостаточно свободных рабочих мест» под полем.
        """
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        with allure.step("Ввести Свободно рабочих мест = 2"):
            form.available_places_input.fill("2")

        with allure.step("Ввести одно из полей 'Из них' = 3 (итого > 2)"):
            form.budget_places_input.fill("3")

        with allure.step("Нажать 'Сохранить вакансию'"):
            form.submit_button.click()

        with allure.step("ОР: под полем 'Свободно' видна ошибка валидации"):
            error = page.locator(
                "#id_available_places ~ .invalid-feedback, "
                "#id_available_places + .invalid-feedback"
            )
            expect(error).to_be_visible(timeout=5000)
            expect(error).to_contain_text("Недостаточно свободных рабочих мест")

    @allure.title("Зарплата 'от' > 'до' → ошибка валидации")
    def test_salary_from_exceeds_salary_to(
        self, open_create_vacancy_page: Page
    ):
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        with allure.step("Ввести зарплату 'от' = 5000, 'до' = 3000"):
            form.salary_input.fill("5000")
            form.salary_limit_input.fill("3000")

        with allure.step("Нажать 'Сохранить вакансию'"):
            form.submit_button.click()

        with allure.step("ОР: видна ошибка валидации диапазона зарплат"):
            error = page.locator(
                "#id_salary ~ .invalid-feedback, "
                "#id_salary + .invalid-feedback, "
                "#id_salary_limit ~ .invalid-feedback, "
                "#id_salary_limit + .invalid-feedback"
            ).first
            expect(error).to_be_visible(timeout=5000)
            expect(error).to_contain_text(
                "Минимальная заработная плата не может превышать максимальную."
            )

    @allure.title("Зарплата с тремя знаками после запятой → ошибка формата")
    def test_salary_too_many_decimal_places(
        self, open_create_vacancy_page: Page
    ):
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        with allure.step("Ввести зарплату с тремя знаками после запятой"):
            form.salary_input.fill("1000.123")

        with allure.step("Нажать 'Сохранить вакансию'"):
            form.submit_button.click()

        with allure.step("ОР: под полем зарплаты ошибка про 2 знака после запятой"):
            error = page.locator(
                "#id_salary ~ .invalid-feedback, "
                "#id_salary + .invalid-feedback"
            )
            expect(error).to_be_visible(timeout=5000)
            expect(error).to_contain_text(
                "Убедитесь, что вы ввели не более 2 цифр после запятой."
            )
