import re
import allure
from playwright.sync_api import Page, expect
from pages.gpd_create_page import GpdCreatePage
from helpers.network_helper import goto_with_retry
from tests.employer.gpd.conftest import GPD_ARCHIVE_URL, CREATE_GPD_URL

# ГПД-вакансия нанимателя в списке — карточка содержит ссылку редактирования /employer/gpd/<id>/edit/
GPD_EDIT_LINK = "a[href*='/employer/gpd/'][href$='/edit/']"


def _gpd_ids(page: Page) -> list:
    """Список ID ГПД-вакансий нанимателя по ссылкам редактирования в списке."""
    ids = []
    links = page.locator(GPD_EDIT_LINK)
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href") or ""
        m = re.search(r"/gpd/(\d+)/edit/", href)
        if m:
            ids.append(m.group(1))
    return ids


def _delete_gpd_by_id(page: Page, gpd_id: str) -> bool:
    """Удаляет ГПД-вакансию по ID через кнопку «Удалить» в её карточке. Best-effort."""
    edit_link = page.locator(f"a[href*='/gpd/{gpd_id}/edit/']").first
    if edit_link.count() == 0:
        return False
    edit_link.wait_for(state="visible", timeout=5000)
    # Поднимаемся до контейнера карточки и ищем в ней кнопку «Удалить»
    card = edit_link.locator("xpath=ancestor::div[contains(@class,'inner-box')][1]")
    delete_btn = card.get_by_role("button", name="Удалить")
    if delete_btn.count() == 0:
        delete_btn = page.get_by_role("button", name="Удалить")
    delete_btn.first.click()
    page.wait_for_timeout(1000)
    # Возможное модальное подтверждение
    confirm = page.get_by_role("button", name=re.compile("Удалить|Подтвердить|Да"))
    try:
        confirm.first.wait_for(state="visible", timeout=3000)
        confirm.first.click()
    except Exception:
        pass
    page.wait_for_load_state("load")
    return True


@allure.epic("Личный кабинет нанимателя")
@allure.feature("Вакансии по ГПД")
@allure.title("Создание ГПД-вакансии со всеми полями → проверка отображения в списке")
def test_create_full_gpd_workflow(open_create_gpd_page: Page, app_config):
    """
    Бизнес-кейс: E2E создание вакансии по ГПД с заполнением всех полей формы.
    После сохранения проверяем редирект и что вакансия отобразилась в списке (write-in).

    Шаги:
    1. Зафиксировать число ГПД-вакансий нанимателя в списке ДО создания.
    2. Заполнить все поля формы создания и нажать «Создать вакансию».
    3. Проверить редирект (форма сохранена, URL не /gpd/create/).
    4. Проверить, что число вакансий в списке увеличилось на 1 (отображение).

    Посткондишн: удаление созданной тестовой вакансии (best-effort).
    """
    page = open_create_gpd_page
    gpd_cfg = app_config["employer"]["test_gpd"]
    form = GpdCreatePage(page)
    created_id = None

    # ── Шаг 0: число вакансий ДО создания ────────────────────────────────────
    with allure.step("Шаг 0: Фиксация числа ГПД-вакансий ДО создания"):
        goto_with_retry(page, GPD_ARCHIVE_URL, wait_until="load")
        page.wait_for_load_state("networkidle", timeout=15000)
        ids_before = set(_gpd_ids(page))
        allure.attach(str(len(ids_before)), name="Число вакансий ДО")

    # Возврат на страницу создания (шаг 0 ушёл на список)
    goto_with_retry(page, CREATE_GPD_URL, wait_until="load")
    page.wait_for_load_state("domcontentloaded")

    try:
        # ── Шаг 1: Предмет ГПД (Select2) ─────────────────────────────────────
        with allure.step(f"Шаг 1: Предмет ГПД '{gpd_cfg['type_gpd_label']}'"):
            form.select_type_gpd(gpd_cfg["type_gpd_label"])

        # ── Шаг 2: Наименование работы/услуги ────────────────────────────────
        with allure.step("Шаг 2: Наименование работы"):
            form.work_type_input.fill(gpd_cfg["work_type"])

        # ── Шаг 3: Сфера деятельности (Select2) ──────────────────────────────
        with allure.step(f"Шаг 3: Сфера деятельности '{gpd_cfg['area_label']}'"):
            form.select_area(gpd_cfg["area_label"])

        # ── Шаг 4: Численность граждан ───────────────────────────────────────
        with allure.step("Шаг 4: Численность граждан"):
            form.number_person_input.fill(gpd_cfg["number_person"])

        # ── Шаг 5: Жильё и варианты ──────────────────────────────────────────
        with allure.step("Шаг 5: Предоставление жилья и все варианты"):
            form.housing_checkbox.check(force=True)
            form.avaliable_housing_0.check(force=True)
            form.avaliable_housing_1.check(force=True)
            form.avaliable_housing_2.check(force=True)

        # ── Шаг 6: Сумма и примечание ────────────────────────────────────────
        with allure.step("Шаг 6: Сумма и примечание"):
            form.salary_input.fill(gpd_cfg["salary"])
            form.comments_textarea.fill(gpd_cfg["comments"])

        # ── Шаг 7: Создать вакансию ───────────────────────────────────────────
        with allure.step("Шаг 7: Нажать 'Создать вакансию'"):
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                form.submit_button.click()
            page.wait_for_load_state("networkidle", timeout=15000)

        # ── Шаг 8: Проверка редиректа ─────────────────────────────────────────
        with allure.step("ОР 1: Форма успешно сохранена (редирект произошёл)"):
            if "/gpd/create/" in page.url:
                error_details = page.evaluate("""
                    () => Array.from(document.querySelectorAll(
                        '.errorlist li, .invalid-feedback, .alert-danger'
                    )).map(el => el.innerText.trim()).filter(t => t !== '')
                """)
                raise AssertionError(
                    f"Форма не отправилась, осталась на {page.url}.\n"
                    f"Ошибки: {error_details}"
                )
            expect(page).not_to_have_url(re.compile(r"/gpd/create/"))

        # ── Шаг 9: Проверка отображения (write-in) ───────────────────────────
        with allure.step("ОР 2: Вакансия отобразилась в списке (write-in)"):
            goto_with_retry(page, GPD_ARCHIVE_URL, wait_until="load")
            page.wait_for_load_state("networkidle", timeout=15000)
            ids_after = set(_gpd_ids(page))
            allure.attach(str(len(ids_after)), name="Число вакансий ПОСЛЕ")

            new_ids = ids_after - ids_before
            assert new_ids, (
                f"Созданная вакансия не отобразилась в списке.\n"
                f"ДО: {sorted(ids_before)}\nПОСЛЕ: {sorted(ids_after)}"
            )
            created_id = sorted(new_ids)[0]
            allure.attach(created_id, name="ID созданной вакансии")

    finally:
        # ── Посткондишн: удаление созданной вакансии (best-effort) ───────────
        with allure.step("Посткондишн: Удаление тестовой ГПД-вакансии"):
            if created_id:
                try:
                    goto_with_retry(page, GPD_ARCHIVE_URL, wait_until="load")
                    page.wait_for_load_state("networkidle", timeout=15000)
                    _delete_gpd_by_id(page, created_id)
                except Exception as e:
                    allure.attach(str(e), name="Ошибка при удалении (не критично)",
                                  attachment_type=allure.attachment_type.TEXT)
