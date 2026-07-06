import pytest
import re
from pages.job_seeker_vacancy_search_page import JobSeekerVacancySearchPage
from helpers.network_helper import goto_with_retry

@pytest.fixture(scope="function")
def open_vacancy_search_page(auth_page) -> JobSeekerVacancySearchPage:
    page = auth_page
    vacancy_page = JobSeekerVacancySearchPage(page)
    goto_with_retry(page, vacancy_page.url)
    return vacancy_page

@allure.epic("Поиск вакансий для соискателя")
@allure.feature("Управление избранными вакансиями")
class TestVacancySearchFavorites:
    @allure.title("Добавление вакансии в избранное")
    def test_add_to_favorites(self, open_vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = open_vacancy_search_page
        initial_fav_state = vacancy_page.get_favorite_state(0)
        
        vacancy_page.toggle_favorite(0)
        new_fav_state = vacancy_page.get_favorite_state(0)
        
        assert initial_fav_state != new_fav_state, "Состояние избранного не изменилось"

    @allure.title("Отображение только избранных вакансий")
    def test_show_favorites_only(self, open_vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = open_vacancy_search_page
        total_vacancies = vacancy_page.get_vacancy_count()
        
        # Добавляем две вакансии в избранное
        vacancy_page.toggle_favorite(0)
        vacancy_page.toggle_favorite(1)
        
        # Включаем фильтр избранного
        vacancy_page.check_show_favorites()
        vacancy_page.page.wait_for_timeout(1000)
        
        # Проверяем количество отображаемых вакансий
        assert vacancy_page.get_vacancy_count() == 2, "Отображаются не только избранные вакансии"

    @allure.title("Печать избранных вакансий")
    def test_print_favorites(self, open_vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = open_vacancy_search_page
        vacancy_page.toggle_favorite(0)
        
        print_page = vacancy_page.click_print_favorites()
        print_page.wait_for_load_state("networkidle")
        
        assert "/registration/print-vacancy-list/" in print_page.url, "Открыта не страница печати"
        print_page.close()

    @allure.title("Очистка избранных вакансий")
    def test_clear_favorites(self, open_vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = open_vacancy_search_page
        vacancy_page.toggle_favorite(0)
        initial_fav_state = vacancy_page.get_favorite_state(0)
        
        vacancy_page.confirm_clear_favorites()
        vacancy_page.page.wait_for_timeout(1000)
        new_fav_state = vacancy_page.get_favorite_state(0)
        
        assert initial_fav_state and not new_fav_state, "Состояние избранного не сброшено"
