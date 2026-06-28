import allure
import pytest
from playwright.sync_api import Page, expect
from pages.employer_info_page import EmployerInfoPage
from pages.employer_create_workplace_page import EmployerCreateWorkplacePage
from pages.employer_edit_info_page import EmployerEditInfoPage
from helpers.network_helper import goto_with_retry

EMPLOYER_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/"
EMPLOYER_EDIT_INFO_URL = "https://gsz.gov.by/registration/employer/business-entity-info/edit/"
CREATE_WORKPLACE_URL = "https://gsz.gov.by/registration/employer/business-entity/create-workplace/"


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Страница сведений о юридическом лице")
class TestBusinessEntityInfoPageElements:

    @allure.title("Кнопка 'Редактировать' сведения о ЮЛ видима на странице")
    def test_edit_employer_info_btn_visible(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: Наниматель должен видеть кнопку перехода к редактированию сведений.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта страница /registration/employer/business-entity-info/.

        Шаги:
        1. Найти кнопку «Редактировать» сведения о ЮЛ.
        2. Проверить её видимость.

        Ожидаемый результат (ОР):
        - Кнопка редактирования отображается на странице.
        """
        info_page = EmployerInfoPage(open_employer_info_page)

        with allure.step("Проверка видимости кнопки 'Редактировать' сведения о ЮЛ"):
            expect(info_page.edit_info_btn).to_be_visible()

    @allure.title("Кнопка 'Редактировать' сведения о ЮЛ ведёт на страницу редактирования")
    def test_edit_employer_info_btn_navigates(self, open_employer_info_page: Page):
        """
        Бизнес-кейс: Клик по кнопке редактирования должен открывать форму изменения сведений.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта страница сведений о ЮЛ.

        Шаги:
        1. Кликнуть по кнопке «Редактировать».
        2. Дождаться загрузки страницы редактирования.

        Ожидаемый результат (ОР):
        - URL страницы содержит /business-entity-info/edit/.
        """
        info_page = EmployerInfoPage(open_employer_info_page)

        with allure.step("Клик по кнопке 'Редактировать' сведения о ЮЛ"):
            info_page.edit_info_btn.click()
            open_employer_info_page.wait_for_load_state("networkidle")

        with allure.step("ОР: URL содержит /business-entity-info/edit/"):
            expect(open_employer_info_page).to_have_url(
                "https://gsz.gov.by/registration/employer/business-entity-info/edit/"
            )

    @allure.title("Кнопка создания адреса рабочего места видима на странице")
    def test_create_workplace_btn_visible(self, open_employer_info_page: Page):
        """
        Бизнес-кейс: Наниматель должен видеть кнопку добавления нового рабочего места.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта страница сведений о ЮЛ.

        Шаги:
        1. Найти кнопку создания рабочего места.
        2. Проверить её видимость.

        Ожидаемый результат (ОР):
        - Кнопка создания рабочего места отображается.
        """
        info_page = EmployerInfoPage(open_employer_info_page)

        with allure.step("Проверка видимости кнопки создания рабочего места"):
            expect(info_page.create_workplace_btn).to_be_visible()

    @allure.title("Постоянная карточка рабочего места 'Филиал тест' присутствует на странице")
    def test_permanent_workplace_card_present(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: На странице должен быть предсозданный «Филиал тест» как эталонная сущность.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. На странице создан постоянный «Филиал тест» (не удаляется автотестами).

        Шаги:
        1. Найти карточку с заголовком «Филиал тест».

        Ожидаемый результат (ОР):
        - Заголовок карточки «Филиал тест» виден на странице.
        """
        permanent_name = app_config["employer"]["permanent_workplace_name"]

        with allure.step(f"Проверка наличия карточки '{permanent_name}'"):
            card_title = open_employer_info_page.locator("h4.job-title", has_text=permanent_name)
            expect(card_title).to_be_visible()

    @allure.title("Кнопка 'Редактировать' присутствует на постоянной карточке рабочего места")
    def test_permanent_workplace_edit_btn(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: У каждого рабочего места должна быть кнопка редактирования.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. На странице присутствует карточка «Филиал тест».

        Шаги:
        1. Найти кнопку «Редактировать» на карточке «Филиал тест».

        Ожидаемый результат (ОР):
        - Кнопка «Редактировать» видима на постоянной карточке.
        """
        info_page = EmployerInfoPage(open_employer_info_page)
        permanent_name = app_config["employer"]["permanent_workplace_name"]

        with allure.step(f"Проверка наличия кнопки 'Редактировать' на карточке '{permanent_name}'"):
            edit_btn = info_page.get_workplace_edit_btn(permanent_name)
            expect(edit_btn).to_be_visible()

    @allure.title("Кнопка 'Редактировать координаты' присутствует на постоянной карточке рабочего места")
    def test_permanent_workplace_edit_coords_btn(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: У каждого рабочего места должна быть кнопка редактирования координат.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. На странице присутствует карточка «Филиал тест».

        Шаги:
        1. Найти кнопку «Редактировать координаты» на карточке «Филиал тест».

        Ожидаемый результат (ОР):
        - Кнопка «Редактировать координаты» видима на постоянной карточке.
        """
        info_page = EmployerInfoPage(open_employer_info_page)
        permanent_name = app_config["employer"]["permanent_workplace_name"]

        with allure.step(f"Проверка наличия кнопки 'Редактировать координаты' на карточке '{permanent_name}'"):
            coords_btn = info_page.get_workplace_edit_coords_btn(permanent_name)
            expect(coords_btn).to_be_visible()

    @allure.title("Кнопка 'Удалить' присутствует на постоянной карточке рабочего места")
    def test_permanent_workplace_delete_btn(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: У каждого рабочего места должна быть кнопка удаления.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. На странице присутствует карточка «Филиал тест».

        Шаги:
        1. Найти кнопку «Удалить» на карточке «Филиал тест».
        2. Проверить её видимость — клик не производить.

        Ожидаемый результат (ОР):
        - Кнопка «Удалить» видима на постоянной карточке.
        """
        info_page = EmployerInfoPage(open_employer_info_page)
        permanent_name = app_config["employer"]["permanent_workplace_name"]

        with allure.step(f"Проверка наличия кнопки 'Удалить' на карточке '{permanent_name}' без клика"):
            delete_btn = info_page.get_workplace_delete_btn(permanent_name)
            expect(delete_btn).to_be_visible()


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Поиск рабочих мест")
class TestWorkplaceSearch:

    @allure.title("Поиск по названию находит постоянное рабочее место")
    def test_search_finds_permanent_workplace(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: Поиск по точному названию должен показывать только совпадающие карточки.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. На странице присутствует «Филиал тест».

        Шаги:
        1. Ввести «Филиал тест» в поле поиска.
        2. Дождаться фильтрации результатов.
        3. Проверить, что заголовок «Филиал тест» виден.

        Ожидаемый результат (ОР):
        - Карточка «Филиал тест» отображается после поиска.
        """
        info_page = EmployerInfoPage(open_employer_info_page)
        permanent_name = app_config["employer"]["permanent_workplace_name"]

        with allure.step(f"Ввод '{permanent_name}' в поле поиска"):
            info_page.search_workplace(permanent_name)

        with allure.step("ОР: Карточка с искомым названием видима"):
            card_title = open_employer_info_page.locator("h4.job-title", has_text=permanent_name)
            expect(card_title).to_be_visible()

    @allure.title("Кнопка 'Сбросить' очищает поисковый запрос")
    def test_search_reset(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: После сброса поиска список рабочих мест должен вернуться в исходное состояние.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. На странице есть хотя бы одно рабочее место.

        Шаги:
        1. Ввести текст в поле поиска.
        2. Нажать кнопку «Сбросить».
        3. Проверить, что поле поиска очищено.
        4. Проверить, что постоянная карточка снова видима.

        Ожидаемый результат (ОР):
        - Поле поиска пустое.
        - Карточка «Филиал тест» снова отображается.
        """
        info_page = EmployerInfoPage(open_employer_info_page)
        permanent_name = app_config["employer"]["permanent_workplace_name"]

        with allure.step("Шаг 1: Ввод поискового запроса"):
            info_page.search_workplace(permanent_name)

        with allure.step("Шаг 2: Нажатие кнопки 'Сбросить'"):
            info_page.reset_search()

        with allure.step("ОР: Поле поиска очищено"):
            expect(info_page.workplace_search_input).to_have_value("")

        with allure.step("ОР: Постоянная карточка снова видима"):
            card_title = open_employer_info_page.locator("h4.job-title", has_text=permanent_name)
            expect(card_title).to_be_visible()


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Создание и удаление рабочего места")
class TestCreateWorkplace:

    @allure.title("Кнопка создания рабочего места ведёт на страницу создания")
    def test_create_workplace_btn_navigates(self, open_employer_info_page: Page):
        """
        Бизнес-кейс: Клик по кнопке создания рабочего места должен открывать форму создания.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта страница сведений о ЮЛ.

        Шаги:
        1. Кликнуть по кнопке создания рабочего места.
        2. Дождаться загрузки страницы.

        Ожидаемый результат (ОР):
        - URL содержит /create-workplace/.
        """
        info_page = EmployerInfoPage(open_employer_info_page)

        with allure.step("Клик по кнопке создания рабочего места"):
            info_page.create_workplace_btn.click()
            open_employer_info_page.wait_for_load_state("networkidle")

        with allure.step("ОР: URL содержит /create-workplace/"):
            expect(open_employer_info_page).to_have_url(
                "https://gsz.gov.by/registration/employer/business-entity/create-workplace/"
            )

    @allure.title("На странице создания рабочего места присутствует ссылка на инструкцию")
    def test_create_workplace_instruction_link(self, open_employer_info_page: Page):
        """
        Бизнес-кейс: На форме создания рабочего места должна быть ссылка на PDF-инструкцию.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта страница /create-workplace/.

        Шаги:
        1. Перейти на страницу создания рабочего места.
        2. Найти ссылку «Инструкция».

        Ожидаемый результат (ОР):
        - Ссылка ведёт на /media/pdf/workplace_instruction.pdf и открывается в новой вкладке.
        """
        goto_with_retry(open_employer_info_page, CREATE_WORKPLACE_URL, wait_until="load")
        create_page = EmployerCreateWorkplacePage(open_employer_info_page)

        with allure.step("Проверка наличия ссылки на PDF-инструкцию"):
            expect(create_page.instruction_link).to_be_visible()
            expect(create_page.instruction_link).to_have_attribute("target", "_blank")

    @allure.title("Полный цикл: создание нового рабочего места, поиск по нему, удаление")
    def test_create_and_delete_workplace(self, open_employer_info_page: Page, app_config):
        """
        Бизнес-кейс: Проверка полного цикла жизни рабочего места: создание → поиск → удаление.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Рабочее место «Автотест Филиал» не существует в системе.

        Шаги:
        1. Перейти на страницу создания рабочего места.
        2. Заполнить форму тестовыми данными и нажать «Создать».
        3. На странице сведений о ЮЛ найти созданное рабочее место через поиск.
        4. Нажать «Удалить» на карточке созданного рабочего места.
        5. Подтвердить удаление в модальном окне.
        6. Убедиться, что рабочее место удалено.

        Ожидаемый результат (ОР):
        - После создания новое рабочее место отображается в списке.
        - После удаления карточка исчезает из списка.
        """
        page = open_employer_info_page
        workplace = app_config["employer"]["test_workplace"]

        with allure.step("Прекондишн: Удаление остатков 'Автотест Филиал' от предыдущих прогонов"):
            info_page = EmployerInfoPage(page)
            info_page.search_workplace(workplace["name"])
            page.wait_for_timeout(1500)
            while page.locator("h4.job-title").filter(has_text=workplace["name"]).count() > 0:
                info_page.get_workplace_delete_btn(workplace["name"]).click()
                info_page.confirm_workplace_delete()
                page.wait_for_timeout(1500)
            info_page.reset_search()

        with allure.step("Шаг 1: Переход на страницу создания рабочего места"):
            goto_with_retry(page, CREATE_WORKPLACE_URL, wait_until="load")
            page.wait_for_load_state("networkidle")

        with allure.step("Шаг 2: Заполнение формы и отправка"):
            create_page = EmployerCreateWorkplacePage(page)
            create_page.fill_and_submit(
                unpf=workplace["unpf"],
                name=workplace["name"],
                address=workplace["address"],
                region=workplace["region"],
                district=workplace.get("district", ""),
                village=workplace.get("village", ""),
            )

        with allure.step("Шаг 3: Возврат на страницу сведений о ЮЛ"):
            goto_with_retry(page, EMPLOYER_INFO_URL, wait_until="load")
            page.wait_for_load_state("networkidle")

        with allure.step(f"Шаг 4: Поиск созданного рабочего места '{workplace['name']}'"):
            info_page.search_workplace(workplace["name"])

        with allure.step("ОР: Созданное рабочее место присутствует в списке"):
            created_title = page.locator("h4.job-title", has_text=workplace["name"])
            expect(created_title).to_be_visible()

        with allure.step("Шаг 5: Нажатие кнопки 'Удалить' на созданной карточке"):
            delete_btn = page.locator("button.btn-delete").filter(visible=True).first
            delete_btn.click()

        with allure.step("Шаг 6: Подтверждение удаления в модальном окне"):
            info_page.confirm_workplace_delete()

        with allure.step("ОР: Удалённое рабочее место больше не отображается"):
            info_page.reset_search()
            deleted_title = page.locator("h4.job-title", has_text=workplace["name"])
            expect(deleted_title).not_to_be_visible()


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Редактирование сведений — контактные лица")
class TestEditEmployerInfo:

    @allure.title("Добавление и удаление нового контактного лица")
    def test_add_and_delete_contact_person(self, open_employer_edit_info_page: Page, app_config):
        """
        Бизнес-кейс: Проверка полного цикла добавления контактного лица и его удаления.

        Прекондишены:
        1. Пользователь авторизован как наниматель.
        2. Открыта страница редактирования сведений о ЮЛ.
        3. Предсозданное постоянное контактное лицо (индекс 0) не удаляется.

        Шаги:
        1. Нажать «Добавить контактное лицо».
        2. Заполнить поля нового контактного лица (ФИО, должность, телефон, email).
        3. Нажать «Сохранить контактное лицо» (AJAX-сохранение).
        4. Проверить появление уведомления об успехе.
        5. Нажать кнопку удаления (X) для нового контактного лица.
        6. Убедиться, что форма нового контактного лица скрыта.

        Ожидаемый результат (ОР):
        - AJAX-сохранение проходит успешно и показывает зелёный алерт.
        - После удаления новая запись исчезает из формсета.
        """
        page = open_employer_edit_info_page
        contact = app_config["employer"]["test_contact_person"]
        edit_page = EmployerEditInfoPage(page)

        with allure.step("Шаг 1: Нажатие 'Добавить контактное лицо'"):
            edit_page.add_contact_person()

        with allure.step("Шаг 2: Заполнение полей нового контактного лица"):
            edit_page.fill_new_contact_person(
                fio=contact["fio"],
                position=contact["position"],
                phone=contact["phone"],
                email=contact["email"],
            )

        with allure.step("Шаг 3: Сохранение нового контактного лица через AJAX"):
            edit_page.save_new_contact_person()

        with allure.step("ОР: Контакт сохранён в БД — ФИО присутствует после перезагрузки страницы"):
            fio_inputs = page.locator("input[id^='id_contact_person-'][id$='-fio']")
            visible_fio_values = [
                fio_inputs.nth(i).input_value()
                for i in range(fio_inputs.count())
                if fio_inputs.nth(i).is_visible()
            ]
            assert contact["fio"] in visible_fio_values, (
                f"ФИО '{contact['fio']}' не найдено после перезагрузки — AJAX save не записал в БД. "
                f"Видимые ФИО: {visible_fio_values}"
            )

        with allure.step("Шаг 4: Удаление нового контактного лица"):
            edit_page.delete_last_contact_person()

        with allure.step("ОР: Поле ФИО нового контактного лица скрыто из формсета"):
            all_fio_inputs = page.locator("input[id^='id_contact_person-'][id$='-fio']")
            total_fio = all_fio_inputs.count()
            total_delete_btns = page.locator("button[data-formset-delete-button]").count()
            visibility_map = {i: all_fio_inputs.nth(i).is_visible() for i in range(total_fio)}
            visible_fio_values = [
                all_fio_inputs.nth(i).input_value()
                for i in range(total_fio)
                if all_fio_inputs.nth(i).is_visible()
            ]
            last_delete_modal = getattr(edit_page, "_last_delete_modal", "not captured")
            last_delete_responses = getattr(edit_page, "_last_delete_responses", [])
            assert contact["fio"] not in visible_fio_values, (
                f"ФИО '{contact['fio']}' всё ещё присутствует. "
                f"fio_count={total_fio}, delete_btns={total_delete_btns}, "
                f"visibility={visibility_map}, visible_values={visible_fio_values}, "
                f"modal={last_delete_modal}, "
                f"responses={last_delete_responses}"
            )
