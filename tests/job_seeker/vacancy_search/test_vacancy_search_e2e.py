import allure
import pytest
from pages.job_seeker_vacancy_search_page import JobSeekerVacancySearchPage


@pytest.mark.vacancy_search
@allure.epic("Поиск вакансий для соискателя")
@allure.feature("Управление избранными вакансиями")
class TestVacancySearchFavorites:

    @allure.title("Добавление рабочего места в избранное меняет состояние иконки")
    def test_add_to_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        """
        Бизнес-кейс: соискатель добавляет вакансию в избранное со страницы поиска.

        Шаги:
        1. Зафиксировать начальное состояние избранного у первой вакансии.
        2. Переключить избранное у этой вакансии.
        3. Убедиться, что состояние иконки сменилось на противоположное.
        """
        vacancy_page = vacancy_search_page

        with allure.step("Получить начальное состояние избранного"):
            initial_fav_state = vacancy_page.get_favorite_state(0)

        with allure.step("Переключить состояние избранного"):
            vacancy_page.toggle_favorite(0)
            new_fav_state = vacancy_page.get_favorite_state(0)

        with allure.step("Проверить, что состояние изменилось"):
            assert initial_fav_state != new_fav_state, "Состояние избранного не изменилось"

    @allure.title("Фильтр «только избранное» показывает лишь избранные рабочие места")
    def test_show_favorites_only(self, vacancy_search_page: JobSeekerVacancySearchPage):
        """
        Бизнес-кейс: включение фильтра избранного оставляет в списке
        только ранее отмеченные вакансии.

        Шаги:
        1. Добавить две вакансии в избранное.
        2. Включить фильтр «Показать только избранное».
        3. Убедиться, что в списке отображаются ровно две вакансии.
        """
        vacancy_page = vacancy_search_page

        with allure.step("Добавить две вакансии в избранное"):
            added = vacancy_page.add_favorites(2)
            assert added == 2, f"Не удалось добавить 2 вакансии в избранное, добавлено: {added}"

        with allure.step("Включить фильтр избранного"):
            vacancy_page.check_show_favorites()

        with allure.step("Проверить количество отображаемых вакансий"):
            assert vacancy_page.get_vacancy_count() == 2, "В списке отображаются не только избранные вакансии"

    @allure.title("Печать избранных рабочих мест формирует файл")
    def test_print_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        """
        Бизнес-кейс: соискатель может выгрузить список избранного на печать.

        Шаги:
        1. Добавить вакансию в избранное.
        2. Нажать кнопку печати и дождаться скачивания.
        3. Убедиться, что файл сформирован.
        """
        vacancy_page = vacancy_search_page

        with allure.step("Добавить вакансию в избранное"):
            vacancy_page.add_favorites(1)

        with allure.step("Инициировать печать избранного"):
            response = vacancy_page.click_print_favorites()

        with allure.step("Проверить, что страница печати сформирована успешно"):
            assert response.ok, f"Печать избранного вернула статус {response.status}"

    @allure.title("Очистка избранного убирает все отметки")
    def test_clear_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        """
        Бизнес-кейс: кнопка «Очистить избранное» снимает отметки со всех вакансий.

        Шаги:
        1. Добавить вакансию в избранное.
        2. Нажать «Очистить избранное» и подтвердить диалог.
        3. Убедиться, что избранных вакансий на странице не осталось.
        """
        vacancy_page = vacancy_search_page

        with allure.step("Добавить вакансию в избранное"):
            vacancy_page.add_favorites(1)

        with allure.step("Очистить избранное"):
            vacancy_page.clear_all_favorites()

        with allure.step("Проверить, что избранное очищено"):
            assert vacancy_page.count_favorited() == 0, "На странице остались избранные вакансии"
