import pytest
import allure
from pages.job_seeker_vacancy_search_page import JobSeekerVacancySearchPage
from helpers.network_helper import goto_with_retry
from helpers.resume_helper import login_as_job_seeker

@pytest.fixture(scope="function")
def vacancy_search_page(page) -> JobSeekerVacancySearchPage:
    login_as_job_seeker(page)
    vacancy_page = JobSeekerVacancySearchPage(page)
    goto_with_retry(page, vacancy_page.url)
    vacancy_page.page.wait_for_load_state("networkidle")
    return vacancy_page

@allure.epic("Поиск вакансий для соискателя")
@allure.feature("Управление избранными вакансиями")
class TestVacancySearchFavorites:
    @allure.title("Добавление вакансии в избранное")
    def test_add_to_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        initial_fav_state = vacancy_page.get_favorite_state(0)
        
        vacancy_page.toggle_favorite(0)
        vacancy_page.page.wait_for_timeout(500)
        new_fav_state = vacancy_page.get_favorite_state(0)
        
        assert initial_fav_state != new_fav_state, "Состояние избранного не изменилось"

    @allure.title("Отображение только избранных вакансий")
    def test_show_favorites_only(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        
        # Добавляем две вакансии в избранное
        vacancy_page.toggle_favorite(0)
        vacancy_page.toggle_favorite(1)
        vacancy_page.page.wait_for_timeout(500)
        
        # Включаем фильтр избранного
        vacancy_page.check_show_favorites()
        vacancy_page.page.wait_for_timeout(1000)
        
        # Проверяем количество отображаемых вакансий
        vacancy_page.page.wait_for_selector(".job-block", state="visible")
        assert vacancy_page.get_vacancy_count() == 2, "Отображаются не только избранные вакансии"

    @allure.title("Печать избранных вакансий")
    def test_print_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        vacancy_page.toggle_favorite(0)
        vacancy_page.page.wait_for_timeout(500)
        
        with vacancy_page.page.context.expect_page() as new_page_info:
            vacancy_page.click_print_favorites()
        print_page = new_page_info.value
        print_page.wait_for_load_state("networkidle")
        
        assert "/registration/print-vacancy-list/" in print_page.url, "Открыта не страница печати"
        print_page.close()

    @allure.title("Очистка избранных вакансий")
    def test_clear_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        vacancy_page.toggle_favorite(0)
        vacancy_page.page.wait_for_timeout(500)
        initial_fav_state = vacancy_page.get_favorite_state(0)
        
        vacancy_page.confirm_clear_favorites()
        vacancy_page.page.wait_for_timeout(1000)
        new_fav_state = vacancy_page.get_favorite_state(0)
        
        assert initial_fav_state and not new_fav_state, "Состояние избранного не сброшено"
