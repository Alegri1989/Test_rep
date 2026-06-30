import json
import allure
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect
from pages.vacancy_create_page import VacancyCreatePage

_MIN_WAGE = json.loads(
    (Path(__file__).parents[3] / "config.json").read_text(encoding="utf-8")
)["belarus_min_wage"]


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

    @allure.title("Зарплата 'до' превышает 'от' более чем в 3 раза → ошибка")
    def test_salary_limit_exceeds_triple_salary(
        self, open_create_vacancy_page: Page
    ):
        """salary_limit > salary * 3 → ошибка под полем 'до'."""
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        salary = "1000"
        salary_limit = "3001"

        with allure.step(f"Ввести зарплату 'от' = {salary}, 'до' = {salary_limit}"):
            form.salary_input.fill(salary)
            form.salary_limit_input.fill(salary_limit)

        with allure.step("Нажать 'Сохранить вакансию'"):
            form.submit_button.click()

        with allure.step(f"ОР: ошибка «превышает {salary} более чем в 3 раза»"):
            error = page.locator("#salary-limit-error")
            expect(error).to_be_visible(timeout=5000)
            expect(error).to_contain_text(
                f"Максимальная заработная плата превышает {salary} более чем в 3 раза"
            )

    @allure.title("Зарплата 'от' > 10× минимальной для ставки {wage_rate} → confirm-диалог")
    @pytest.mark.parametrize("wage_rate,salary", [
        ("1", "9000"),
        ("0.5", "5000"),
    ])
    def test_salary_exceeds_10x_minimum_shows_confirm(
        self, open_create_vacancy_page: Page, wage_rate: str, salary: str
    ):
        """
        Зарплата > min_wage * rate * 10 → браузерный confirm с предупреждением.
        Тест принимает диалог (OK) и проверяет текст.
        """
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        expected_text = (
            f"Внимание! Зарплата ({salary}) более чем в 10 раз превышает "
            f"размер минимальной заработной платы для ставки {wage_rate}. Продолжить?"
        )

        with allure.step(f"Ввести ставку {wage_rate}, зарплату {salary}"):
            form.wage_rate_input.fill(wage_rate)
            form.salary_input.fill(salary)

        with allure.step("Нажать 'Сохранить' и дождаться confirm-диалога"):
            captured = []
            # Регистрируем обработчик ДО клика: JS confirm() синхронно блокирует браузер,
            # поэтому handler должен быть уже установлен в момент появления диалога.
            page.once("dialog", lambda d: (captured.append(d.message), d.accept()))
            form.submit_button.click()
            page.wait_for_timeout(1000)

        with allure.step(f"ОР: диалог содержит предупреждение"):
            assert captured, "Confirm-диалог не появился"
            assert expected_text in captured[0], (
                f"Ожидали текст:\n{expected_text}\nПолучили:\n{captured[0]}"
            )

    @allure.title("Зарплата ниже минимальной для ставки {wage_rate}")
    @pytest.mark.parametrize("wage_rate,salary_below", [
        ("1", "857"),
        ("0.125", "100"),
    ])
    def test_salary_below_minimum_for_wage_rate(
        self, open_create_vacancy_page: Page, wage_rate: str, salary_below: str
    ):
        """
        При ставке wage_rate зарплата не может быть ниже min_wage * wage_rate.
        Ожидаемое сообщение вычисляется из belarus_min_wage в config.json.
        """
        page = open_create_vacancy_page
        form = VacancyCreatePage(page)

        expected_min = _MIN_WAGE * float(wage_rate)
        expected_text = (
            f"Для ставки {wage_rate} уровень зарплаты не должен быть ниже "
            f"минимальной {expected_min:.2f}"
        )

        with allure.step(f"Ввести ставку {wage_rate}, зарплату {salary_below}"):
            form.wage_rate_input.fill(wage_rate)
            form.salary_input.fill(salary_below)

        with allure.step("Нажать 'Сохранить вакансию'"):
            form.submit_button.click()

        with allure.step(f"ОР: ошибка «{expected_text}»"):
            error = page.locator(
                "#id_salary ~ .invalid-feedback, "
                "#id_salary + .invalid-feedback"
            )
            expect(error).to_be_visible(timeout=5000)
            expect(error).to_contain_text(expected_text)
