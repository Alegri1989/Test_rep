import logging
from playwright.sync_api import Page
from helpers.network_helper import retry_action


class EmployerCreateWorkplacePage:
    def __init__(self, page: Page):
        self.page = page

        self.unpf_input = page.locator("#id_unpf")
        self.name_input = page.locator("#id_name")
        self.region_s2 = page.locator("#select2-id_region-container")
        self.district_s2 = page.locator("#select2-id_district-container")
        self.village_council_s2 = page.locator("#select2-id_village_council-container")
        # #id_address — свободный текстовый input (улица, дом), отдельный от village_council
        self.address_input = page.locator("#id_address")
        self.submit_btn = page.locator("#form_submit")
        self.instruction_link = page.locator("a[href='/media/pdf/workplace_instruction.pdf']")

    def _select_s2(self, container_locator, text: str, label: str):
        """Выбор из Select2. Поиск через ОТКРЫТЫЙ дропдаун — надёжнее, чем get_by_role."""
        def _pick():
            self.page.keyboard.press("Escape")
            container_locator.click()
            # Ждём именно поисковое поле внутри ОТКРЫТОГО Select2
            s2_search = self.page.locator(".select2-container--open input.select2-search__field")
            s2_search.wait_for(state="visible", timeout=5000)
            s2_search.press_sequentially(text, delay=100)
            self.page.wait_for_timeout(1000)
            option = self.page.locator("li.select2-results__option", has_text=text).first
            option.wait_for(state="visible", timeout=3500)
            option.focus()
            option.click()
            self.page.wait_for_timeout(600)

        retry_action(_pick, self.page, retries=3, label=f"выбор {label}='{text}'")

    def select_region(self, region_text: str):
        logging.debug(f"Действие: Выбор области '{region_text}'")
        self._select_s2(self.region_s2, region_text, "регион")

    def select_district(self, district_text: str):
        logging.debug(f"Действие: Выбор района '{district_text}'")
        self._select_s2(self.district_s2, district_text, "район")

    def select_village_council(self, village_text: str):
        logging.debug(f"Действие: Выбор населённого пункта '{village_text}'")
        self._select_s2(self.village_council_s2, village_text, "нас. пункт")

    def fill_and_submit(self, unpf: str, name: str, address: str = "",
                        region: str = "", district: str = "", village: str = ""):
        """Заполняет форму создания рабочего места.

        Поля формы:
          region — Select2 (обязательный, HTML5 required)
          district — Select2 (каскадный после региона, обязательный)
          village — Select2 (#select2-id_village_council-container, как в профиле соискателя)
          address — свободный текст (#id_address, улица/дом, обязательный)
          unpf, name — текстовые поля
        """
        logging.debug(f"Действие: Заполнение формы создания рабочего места '{name}'")

        # 1. Регион
        if region:
            self.select_region(region)
            self.page.wait_for_timeout(2000)  # ждём AJAX загрузки районов

        # 2. Район
        if district:
            try:
                self.district_s2.wait_for(state="visible", timeout=3000)
                self.select_district(district)
                self.page.wait_for_timeout(1500)  # ждём AJAX загрузки нас. пунктов
            except Exception:
                logging.debug("Select2 района не виден — пропускаем")

        # 3. Населённый пункт
        if village:
            try:
                self.village_council_s2.wait_for(state="visible", timeout=3000)
                self.select_village_council(village)
                self.page.wait_for_timeout(500)
            except Exception:
                logging.debug("Select2 населённого пункта не виден — пропускаем")

        # 4. Свободный текстовый адрес (#id_address)
        if address:
            self.address_input.fill(address)

        # 5. УНП и название
        self.unpf_input.click()
        self.unpf_input.press_sequentially(unpf, delay=50)
        self.name_input.click()
        self.name_input.press_sequentially(name, delay=30)

        # 6. Submit
        self.submit_btn.click()
        self.page.wait_for_load_state("networkidle")

        if "create-workplace" in self.page.url:
            try:
                diagnostic = self.page.evaluate("""() => {
                    const results = [];
                    document.querySelectorAll('input, select, textarea').forEach(el => {
                        if (!el.validity.valid)
                            results.push('[HTML5] ' + (el.id || el.name) + ': ' + el.validationMessage);
                    });
                    document.querySelectorAll('[class*="error"], [class*="invalid"], .errorlist, .alert, [class*="message"]').forEach(el => {
                        const t = (el.textContent || '').trim();
                        if (t && t.length < 500)
                            results.push('[DOM:' + el.className.substring(0, 50) + '] ' + t.substring(0, 200));
                    });
                    return results.join(' | ') || 'No errors detected';
                }""")
            except Exception as ex:
                diagnostic = f"evaluate failed: {ex}"
            raise AssertionError(
                f"Форма не прошла: URL={self.page.url}. Диагностика: {diagnostic}"
            )
