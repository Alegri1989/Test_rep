import os
import allure
import json
from playwright.sync_api import Page

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

class CartPage:
    def __init__(self, page: Page):
        self.page = page
        self.checkout_button = page.get_by_text("Proceed To Checkout")
        self.place_order_button = page.get_by_role("link", name="Place Order")
        self.card_name_input = page.locator('input[name="name_on_card"]')
        self.card_number_input = page.locator('input[name="card_number"]')
        self.card_cvc_input = page.get_by_role("textbox", name="ex.")
        self.card_month_input = page.get_by_role("textbox", name="MM")
        self.card_year_input = page.get_by_role("textbox", name="YYYY")
        self.submit_payment_button = page.get_by_role("button", name="Pay and Confirm Order")
        self.download_invoice_button = page.get_by_role("link", name="Download Invoice")

    @allure.step("Перейти к оформлению заказа (Checkout)")
    def proceed_to_checkout(self):
        self.checkout_button.wait_for(state="visible")
        self.page.wait_for_timeout(500)
        self.checkout_button.click()
        self.page.wait_for_url("**/checkout", wait_until="commit")
        self.place_order_button.click()

    @allure.step("Заполнить платежные данные и подтвердить оплату")
    def fill_payment_and_submit(self, name="Alegri Tester",
                                card_number="1111222233334444", cvc="123", month="12", year="2030"):
        self.card_name_input.fill(name)
        self.card_number_input.fill(card_number)
        self.card_cvc_input.fill(cvc)
        self.card_month_input.fill(month)
        self.card_year_input.fill(year)
        self.submit_payment_button.click()

    @allure.step("Скачать файл инвойса")
    def download_invoice(self, target_directory: str = "downloads") -> str:
        os.makedirs(target_directory, exist_ok=True)
        with self.page.expect_download() as download_info:
            self.download_invoice_button.click()
        download = download_info.value
        file_path = os.path.join(target_directory, download.suggested_filename)
        download.save_as(file_path)
        return file_path

    @allure.step("Очистить корзину перед тестом")
    def clear_cart(self):
        self.page.goto(f"{CONFIG['base_url']}/view_cart", wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        product_rows = self.page.locator("tbody tr[id^='product-']")
        while product_rows.count() > 0:
            delete_btn = product_rows.first.locator(".cart_quantity_delete")
            if delete_btn.is_visible():
                delete_btn.click()
                product_rows.first.wait_for(state="hidden", timeout=3000)
            else:
                break