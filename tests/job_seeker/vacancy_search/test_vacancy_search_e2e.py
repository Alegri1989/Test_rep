import pytest
import allure
from pages.job_seeker_vacancy_search_page import JobSeekerVacancySearchPage
from helpers.network_helper import goto_with_retry
from helpers.resume_helper import login_as_job_seeker
'''
@pytest.fixture(scope="function")
def vacancy_search_page(open_vacancy_search_page) -> JobSeekerVacancySearchPage:
    """Фикстура возвращает инициализированную страницу поиска вакансий"""
    return JobSeekerVacancySearchPage(open_vacancy_search_page)

@allure.epic("Поиск вакансий для соискателя")
@allure.feature("Управление избранными вакансиями")
class TestVacancySearchFavorites:
    @allure.title("Добавление рабочего места в избранное")
    def test_add_to_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        
        # Получаем начальное состояние избранного
        initial_fav_state = vacancy_page.get_favorite_state(0)
        
        # Переключаем состояние избранного
        vacancy_page.toggle_favorite(0)
        new_fav_state = vacancy_page.get_favorite_state(0)
        
        # Проверяем, что состояние изменилось
        assert initial_fav_state != new_fav_state, "Состояние избранного не изменилось"

    @allure.title("Отображение только избранных рабочих мест")
    def test_show_favorites_only(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        
        # Добавляем два рабочих места в избранное
        vacancy_page.toggle_favorite(0)
        vacancy_page.toggle_favorite(1)
        
        # Включаем фильтр избранного
        vacancy_page.check_show_favorites()
        
        # Проверяем количество отображаемых рабочих мест
        assert vacancy_page.get_vacancy_count() == 2, "Отображаются не только избранные рабочие места"

    @allure.title("Печать избранных рабочих мест") 
    def test_print_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        vacancy_page.toggle_favorite(0)
        
        # Инициируем печать
        vacancy_page.click_print_favorites()
        
        # Проверяем, что кнопка печати сработала
        expect(vacancy_page.print_favorites_btn).to_be_enabled()

    @allure.title("Очистка избранных рабочих мест")
    def test_clear_favorites(self, vacancy_search_page: JobSeekerVacancySearchPage):
        vacancy_page = vacancy_search_page
        
        # Добавляем рабочее место в избранное
        vacancy_page.toggle_favorite(0)
        
        # Очищаем избранное
        vacancy_page.confirm_clear_favorites()
        
        # Проверяем, что избранное очищено
        assert not vacancy_page.get_favorite_state(0), "Рабочее место осталось в избранном"
        '''
