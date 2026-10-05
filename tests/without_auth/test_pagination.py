import pytest
import allure

from helpers.pagination_helper import verify_pagination_forward_back
from helpers.paginate_count_helper import verify_change_paginate_by_count


@pytest.mark.parametrize(
    "page_fixture",
    ["education_page", "future_work_page", "gpd_page"],
    ids=["education", "future_work", "gpd"],
)
@allure.title("Бизнес-кейс: Постраничная навигация (вперёд на стр. 2, назад на стр. 1)")
def test_guest_pagination_forward_and_back(guest_page, request, page_fixture):
    """
    Бизнес-кейс: Проверка корректности постраничной навигации по выдаче
    (вперёд на страницу 2, назад на страницу 1) на 3 страницах портала.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована целевая страница, выдача содержит больше одной страницы.

    Ожидаемый результат (ОР):
    - Постраничная навигация корректно переключает выдачу как вперёд, так и назад.
    """
    page_object = request.getfixturevalue(page_fixture)
    verify_pagination_forward_back(guest_page, page_object)


@pytest.mark.parametrize(
    "page_fixture, card_attr",
    [
        ("future_work_page", "vacancy_cards"),
        ("gpd_page", "vacancy_cards"),
        ("vacancy_page", "vacancy_title_link"),
        ("public_work_page", "vacancy_cards"),
    ],
    ids=["future_work", "gpd", "vacancy_search", "public_work"],
)
@allure.title("Бизнес-кейс: Изменение количества карточек на странице (10 -> 20 -> 50 -> 10)")
def test_guest_change_paginate_by_count(guest_page, request, page_fixture, card_attr):
    """
    Бизнес-кейс: Проверка работы селекта количества элементов на странице выдачи
    (10 -> 20 -> 50 -> 10) на 4 страницах портала.

    Прекондишены:
    1. Пользователь не авторизован в системе (гостевой сеанс).
    2. Инициализирована целевая страница.

    Ожидаемый результат (ОР):
    - Селект переключает режимы отображения, бэкенд перестраивает выдачу
      с соответствующим лимитом строк (не более выбранного лимита).
    """
    page_object = request.getfixturevalue(page_fixture)
    card_locator = getattr(page_object, card_attr)
    verify_change_paginate_by_count(guest_page, page_object, card_locator)
