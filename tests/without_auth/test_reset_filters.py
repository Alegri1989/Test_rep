import pytest
import allure
from playwright.sync_api import Page

from helpers.filter_reset_helper import verify_filter_reset
from pages.education_page import EducationPage
from pages.future_work_page import FutureWorkPage
from pages.gpd_page import GpdPage
from pages.vacancy_search_page import VacancySearchPage
from pages.opfr_page import OpfrPage
from pages.public_work_page import PublicWorkPage
from pages.departments_page import DepartmentsPage
from pages.public_resume_search_page import PublicResumeSearchPage


@pytest.mark.parametrize(
    "page_fixture, default_url",
    [
        ("education_page", "https://gsz.gov.by/registration/training-course/public/list/?"),
        ("future_work_page", "https://gsz.gov.by/registration/future-vacancy/future-works/?"),
        ("gpd_page", "https://gsz.gov.by/registration/gpd/public-works/?"),
        ("vacancy_page", "https://gsz.gov.by/registration/vacancy-search/?"),
        ("opfr_page", "https://gsz.gov.by/registration/opfr_organisations/public-list/?"),
        ("public_work_page", "https://gsz.gov.by/registration/temporary-employment/public-works/?"),
        ("departments_page", "https://gsz.gov.by/directory/information/employment-departments/?"),
        ("public_resume_search_page", "https://gsz.gov.by/registration/resume-search/?"),
    ],
    ids=[
        "education", "future_work", "gpd", "vacancy_search",
        "opfr", "public_work", "departments", "public_resume_search",
    ],
)
@allure.title("Бизнес-кейс: Сброс установленных фильтров (параметризованный)")
def test_guest_reset_applied_filters(
    guest_page: Page,
    request,
    page_fixture: str,
    default_url: str,
):
    """
    Бизнес-кейс: Проверка работоспособности функционала сброса установленных
    поисковых фильтров на 8 страницах портала.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована целевая страница.

    Шаги:
    1. Открыть страницу.
    2. Применить демо-фильтр (уникальный для каждой страницы).
    3. Кликнуть по кнопке "Сбросить фильтр".
    4. Дождаться полной загрузки страницы.

    Ожидаемый результат (ОР):
    - Система выполняет перезагрузку страницы и возвращает пользователя
      на дефолтный URL со знаком вопроса.
    - Ранее применённый демо-фильтр сбрасывается до значения по умолчанию.
    """
    page_object = request.getfixturevalue(page_fixture)
    verify_filter_reset(guest_page, page_object, default_url)
