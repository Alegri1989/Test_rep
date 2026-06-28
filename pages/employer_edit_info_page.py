import logging
from playwright.sync_api import Page
from helpers.network_helper import retry_action


class EmployerEditInfoPage:
    def __init__(self, page: Page):
        self.page = page

        self.add_contact_btn = page.get_by_role("button", name="Добавить контактное лицо")
        self.success_alert = page.locator("div.alert-success")

        self._last_delete_modal = None
        self._last_delete_responses = []

    def _get_contact_fio_inputs(self):
        return self.page.locator("input[id^='id_contact_person-'][id$='-fio']")

    def add_contact_person(self):
        count_before = self._get_contact_fio_inputs().count()
        self.add_contact_btn.click()
        self.page.wait_for_timeout(500)
        self._get_contact_fio_inputs().nth(count_before).wait_for(state="visible", timeout=5000)

    def fill_new_contact_person(self, fio: str, position: str, phone: str, email: str):
        self._get_contact_fio_inputs().last.fill(fio)
        self.page.locator("input[id^='id_contact_person-'][id$='-position']").last.fill(position)
        self.page.locator("input[id^='id_contact_person-'][id$='-phone']").last.fill(phone)
        self.page.locator("input[id^='id_contact_person-'][id$='-email']").last.fill(email)

    def save_new_contact_person(self):
        """AJAX-сохранение нового контактного лица + reload для проверки записи в БД."""
        save_btn = self.page.locator("button.js-ajax-save-btn").last
        save_btn.wait_for(state="visible", timeout=5000)
        save_btn.click()
        self.page.wait_for_load_state("networkidle", timeout=20000)
        self.page.wait_for_timeout(500)
        # Reload verifies DB persistence: если контакт в БД — ФИО будет видно после перезагрузки
        self.page.reload()
        self.page.wait_for_load_state("networkidle", timeout=20000)

    def delete_last_contact_person(self):
        """Кликает кнопку удаления последнего видимого контактного лица.

        После клика проверяет:
        1. Скрылась ли форма в DOM (client-side hide)
        2. Были ли сетевые запросы (AJAX delete)
        Если форма не скрылась сразу — делает reload для проверки DB-удаления.
        """
        fio_inputs = self._get_contact_fio_inputs()
        total = fio_inputs.count()
        last_visible_idx = -1
        for i in range(total - 1, -1, -1):
            if fio_inputs.nth(i).is_visible():
                last_visible_idx = i
                break
        if last_visible_idx < 0:
            raise AssertionError("Нет видимых контактных лиц для удаления")

        fio_id = fio_inputs.nth(last_visible_idx).get_attribute("id")
        logging.warning(f"delete_last: fio_id='{fio_id}', last_visible_idx={last_visible_idx}")

        # Находим delete-кнопку в том же [data-formset-form] контейнере
        delete_btn_idx = self.page.evaluate("""(fioId) => {
            const fio = document.getElementById(fioId);
            if (!fio) return -1;
            const form = fio.closest('[data-formset-form]');
            if (!form) return -1;
            const deleteBtn = form.querySelector('[data-formset-delete-button]');
            if (!deleteBtn) return -1;
            const allBtns = Array.from(document.querySelectorAll('[data-formset-delete-button]'));
            return allBtns.indexOf(deleteBtn);
        }""", fio_id)

        logging.warning(f"delete_last: DOM-traversal btn_idx={delete_btn_idx}")

        fio_sibling_selector = f"#{fio_id} ~ button[data-formset-delete-button]"
        sibling_btn = self.page.locator(fio_sibling_selector)

        if sibling_btn.count() > 0:
            delete_btn = sibling_btn.first
            logging.warning(f"delete_last: using sibling-selector '{fio_sibling_selector}'")
        elif delete_btn_idx >= 0:
            delete_btn = self.page.locator("button[data-formset-delete-button]").nth(delete_btn_idx)
            logging.warning(f"delete_last: using nth({delete_btn_idx}) from DOM-traversal")
        else:
            delete_btn = self.page.locator("button[data-formset-delete-button]").nth(last_visible_idx)
            logging.warning(f"delete_last: fallback to nth({last_visible_idx})")

        # Перехватываем все сетевые ответы во время удаления
        delete_responses = []

        def _on_response(resp):
            if resp.request.method in ("POST", "DELETE", "PATCH", "PUT"):
                delete_responses.append(f"{resp.request.method} {resp.status} {resp.url}")

        self.page.on("response", _on_response)
        handler = lambda d: d.accept()
        self.page.on("dialog", handler)
        try:
            delete_btn.scroll_into_view_if_needed()
            delete_btn.click()
            self.page.wait_for_timeout(1500)

            # Диагностика DOM после клика
            try:
                dom_state = self.page.evaluate(f"""(fioId) => {{
                    const fio = document.getElementById(fioId);
                    if (!fio) return 'FIO not found';
                    const form = fio.closest('[data-formset-form]') || fio.parentElement;
                    const style = window.getComputedStyle(form);
                    return {{
                        display: style.display,
                        visibility: style.visibility,
                        formClass: form.className.substring(0, 80),
                        fioVisible: fio.offsetParent !== null
                    }};
                }}""", fio_id)
                logging.warning(f"delete_last: DOM after click: {dom_state}")
            except Exception as ex:
                logging.warning(f"delete_last: DOM evaluate failed: {ex}")

            # Если форма ещё видна — пробуем JS-click как fallback
            if fio_inputs.nth(last_visible_idx).is_visible():
                logging.warning("delete_last: FIO still visible, trying JS dispatchEvent click")
                self.page.evaluate(f"""(idx) => {{
                    const btns = document.querySelectorAll('[data-formset-delete-button]');
                    const btn = btns[idx];
                    if (btn) {{
                        ['mousedown', 'mouseup', 'click'].forEach(type => {{
                            btn.dispatchEvent(new MouseEvent(type, {{bubbles: true, cancelable: true}}));
                        }});
                    }}
                }}""", delete_btn_idx if delete_btn_idx >= 0 else last_visible_idx)
                self.page.wait_for_timeout(1500)

            # Bootstrap/кастомный модал подтверждения
            try:
                modal_info = self.page.evaluate("""() => {
                    const m = document.querySelector('.modal.show');
                    return m ? '[modal] ' + m.textContent.trim().replace(/\\s+/g, ' ').substring(0, 200) : null;
                }""")
                self._last_delete_modal = modal_info
                if modal_info:
                    logging.warning(f"delete_last: modal: {modal_info}")
            except Exception:
                self._last_delete_modal = None

            for sel in [
                ".modal.show button.btn-danger",
                ".modal.show button.btn-primary",
                "[role='dialog'] button:has-text('Да')",
                "[role='dialog'] button:has-text('Удалить')",
                "[role='dialog'] button:has-text('OK')",
                ".swal2-confirm",
            ]:
                try:
                    btn = self.page.locator(sel).first
                    if btn.is_visible(timeout=400):
                        btn.click()
                        break
                except Exception:
                    continue

            self.page.wait_for_load_state("networkidle", timeout=10000)
        finally:
            self.page.remove_listener("response", _on_response)
            self.page.remove_listener("dialog", handler)

        self._last_delete_responses = delete_responses
        logging.warning(f"delete_last: network responses: {delete_responses}")
        self.page.wait_for_timeout(500)

        # Если client-side не скрыл форму — reload покажет DB-состояние.
        # Если AJAX delete прошёл тихо (без DOM update) — reload подтвердит удаление из БД.
        if fio_inputs.nth(last_visible_idx).is_visible():
            logging.warning("delete_last: FIO still visible after clicks — trying reload to confirm DB delete")
            self.page.reload()
            self.page.wait_for_load_state("networkidle", timeout=20000)
