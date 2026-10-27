"""Тамперинг запросов: подмена HTTP-метода и mass assignment (лишние поля)."""
import re
import allure
import pytest
from playwright.sync_api import Page

from helpers.network_helper import goto_with_retry

BASE_URL = "https://gsz.gov.by"


def _status(page: Page, method: str, url: str, **kwargs) -> int:
    try:
        return getattr(page.request, method)(url, **kwargs).status
    except Exception as e:
        return -1


@allure.epic("Безопасность")
@allure.feature("HTTP Method Tampering")
class TestMethodTampering:
    """Проверка, что некорректные HTTP-методы на изменяющих эндпоинтах отклоняются."""

    @pytest.mark.parametrize("method", ["put", "delete", "patch"], ids=["PUT", "DELETE", "PATCH"])
    @allure.title("Безопасность: Некорректный HTTP-метод отклонён")
    def test_method_tampering_profile(self, job_seeker_page: Page, method: str):
        """
        Бизнес-кейс: эндпоинт обновления профиля принимает только свой метод.
        Подмена метода (PUT/DELETE/PATCH) должна быть отклонена (405/403/404),
        а не выполнена.

        Ожидаемый результат (ОР): ответ не 200/302-с-изменением.
        """
        url = f"{BASE_URL}/registration/job-seeker/personal-info/"
        status = _status(job_seeker_page, method, url, data={"last_name": "Hacker"})
        allure.attach(f"{method.upper()} {url} -> {status}", name="Статус",
                      attachment_type=allure.attachment_type.TEXT)
        assert status in (400, 403, 404, 405), (
            f"Уязвимость (Method Tampering): {method.upper()} на профиль вернул {status}. "
            "Некорректный метод был принят — возможна несанкционированная операция."
        )

    @allure.title("Безопасность: DELETE на резюме отклонён некорректным методом")
    def test_method_tampering_resume(self, job_seeker_page: Page):
        """
        Бизнес-кейс: подмена метода на операции с резюме должна быть отклонена.

        Ожидаемый результат (ОР): PUT/DELETE на создание резюме не дают 200.
        """
        create_url = f"{BASE_URL}/registration/job-seeker/resume/create/"
        put_status = _status(job_seeker_page, "put", create_url, data={"id_desired_salary": "999999"})
        patch_status = _status(job_seeker_page, "patch", create_url, data={"id_desired_salary": "999999"})
        allure.attach(f"PUT -> {put_status}, PATCH -> {patch_status}", name="Статусы",
                      attachment_type=allure.attachment_type.TEXT)
        assert put_status in (400, 403, 404, 405) and patch_status in (400, 403, 404, 405), (
            f"Уязвимость (Method Tampering): PUT={put_status}, PATCH={patch_status} — "
            "некорректные методы приняты на эндпоинте создания резюме."
        )


@allure.epic("Безопасность")
@allure.feature("Mass assignment")
class TestMassAssignment:
    """Проверка, что лишние/привилегированные поля в форме не применяются."""

    @allure.title("Безопасность: Поле is_admin в форме профиля не применяется")
    def test_mass_assignment_role(self, job_seeker_page: Page):
        """
        Бизнес-кейс: при отправке формы обновления профиля атакующий может
        добавить скрытое поле is_admin / role / is_staff. Сервер должен игнорировать
        непривилегированные поля.

        Ожидаемый результат (ОР): после отправки пользователь НЕ становится админом.
        """
        page = job_seeker_page
        profile_url = f"{BASE_URL}/registration/job-seeker/personal-info/"
        goto_with_retry(page, profile_url, wait_until="load")
        page.wait_for_load_state("networkidle")

        # Собираем CSRF-токен из формы (если есть), чтобы пройти CSRF и проверить именно mass assignment
        token = ""
        tok = page.locator("input[name='csrfmiddlewaretoken']").first
        if tok.count() > 0:
            try:
                token = tok.get_attribute("value") or ""
            except Exception:
                token = ""

        # Отправляем форму с попыткой масс-присвоения привилегированных полей
        resp = page.request.post(
            profile_url,
            data={
                "last_name": "Алексеев",
                "first_name": "Григорий",
                "is_admin": "1",
                "is_staff": "1",
                "is_superuser": "1",
                "role": "admin",
                "csrfmiddlewaretoken": token,
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
            max_redirects=0,
        )
        allure.attach(f"Статус POST с is_admin: {resp.status}", name="Статус",
                      attachment_type=allure.attachment_type.TEXT)

        # Проверяем, что пользователь не стал админом: переходим в профиль и ищем признаки админки
        goto_with_retry(page, profile_url, wait_until="load")
        page.wait_for_load_state("networkidle")
        body = page.content()
        admin_markers = re.search(r"is_admin|is_staff|superuser|администратор", body, re.IGNORECASE)
        # Если 200 и в профиле появились маркеры админки — возможная уязвимость.
        # Но сам по себе 200 не доказывает успех; проверяем по маркерам.
        assert not (resp.status == 200 and admin_markers), (
            "Уязвимость (Mass assignment): попытка присвоить is_admin/role через форму "
            "профиля вернула 200 и в профиле появились привилегированные маркеры."
        )
